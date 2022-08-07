import sublime
import sublime_plugin

import subprocess
import threading
import os
import re
import signal
import sys

class FwBuildCommand(sublime_plugin.WindowCommand):

    encoding = 'utf-8'
    killed = False
    proc = None
    panel = None
    panel_lock = threading.Lock()
    THOR_MAKE_PATH = 'main/Cumulus/firmware/THOR'
    CHIMP_MAKE_PATH = 'main/Cumulus/firmware/ChiMP/bootcode'

    def is_enabled(self, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    def run(self, chip="thor", build_type="release", sign=False, kill=False):
        self._local_make_path = None
        self.repo = None
        self.chip = chip
        self.build_type = build_type
        self.sign = sign

        if kill:
            if self.proc:
                self.killed = True
                self.proc.communicate(input=b'\x03')
                self.proc.terminate()
            return
        self.get_repo()

        # A lock is used to ensure only one thread is
        # touching the output panel at a time
        with self.panel_lock:
            # Creating the panel implicitly clears any previous contents
            self.panel = self.window.create_output_panel('exec')

            # Enable result navigation.
            settings = self.panel.settings()
            settings.set(
                'syntax',
                'Packages/Makefile/Make Output.sublime-syntax'
            )

            self.window.run_command('show_panel', {'panel': 'output.exec'})

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        self.proc = subprocess.Popen(
            self.build_args(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.killed = False

        threading.Thread(
            target=self.read_handle,
            args=(self.proc.stdout,)
        ).start()

    def build_args(self) -> list:
        # buildthor.sh -u shague -i 127.0.0.1 -p 2021
        args = ['/Users/shague/bin/fwbuild.sh']
        args.append('-u')
        args.append('shague')
        args.append('-i')
        args.append('127.0.0.1')
        args.append('-p')
        args.append('2021')
        if self.chip == "thor" or self.chip == "chimp":
            args.append(f'-t')
            args.append(f'{self.chip}')
        else:
            error_msg = "Invalid chip type {self.chip}".format(chip=self.chip)
            sublime.error_message(error_msg)
            raise ValueError(error_msg)
        if self.build_type == "release" or self.build_type == "debug":
            args.append('-r')
            args.append(self.repo.replace('/Users/shague/git', '/git'))
        elif self.build_type == "clean":
            args.append('-r')
            args.append(self.repo)
        else:
            error_msg = "Invalid build type {build_type}".format(build_type=build_type)
            sublime.error_message(error_msg)
            raise ValueError(error_msg)
        args.append('-b')
        args.append(self.build_type)
        if self.sign:
            args.append('-c')
            args.append('CRID=0001')
            args.append('-s')
            args.append('/home/shague/sign.txt')

        sublime.status_message(f"build command: {args}")
        return args

    def read_handle(self, handle):
        chunk_size = 2 ** 10
        out = b''
        while True:
            try:
                data = os.read(handle.fileno(), chunk_size)
                # If exactly the requested number of bytes was
                # read, there may be more data, and the current
                # data may contain part of a multibyte char
                out += data
                if len(data) == chunk_size:
                    continue
                if data == b'' and out == b'':
                    raise IOError('EOF')
                # We pass out to a function to ensure the
                # timeout gets the value of out right now,
                # rather than a future (mutated) version
                self.queue_write(out.decode(self.encoding))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.queue_write(msg  % (self.encoding, str(e)))
                break
            except (IOError):
                if self.killed:
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                self.queue_write('\n[%s]' % msg)
                break

    def queue_write(self, text):
        sublime.set_timeout(lambda: self.do_write(text), 30)

    def do_write(self, text):
        text = remove_ansi_ctrl(text)
        text = self.translate_file_paths(text)
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})

    def get_repo(self):
        """Find the git repo.

        Different methods will be used until a suitable path is found:
        1. vars folder: the first folder opened for the project
        2. vars file_path: the path to the currently open file
        """
        vars = self.window.extract_variables()
        for var in ['folder', 'file_path']:
            folder = vars.get(var)
            if "git" in folder:
                self.repo = folder
                return

        err_msg = f"repo was not found"
        sublime.error_message(err_msg)
        raise ValueError(err_msg)


    def translate_file_paths(self, text):
        regexs = [
            # Example: ../Primate/grc.c:561:9: error: 'ELAS_PR_TMR_PRIORITY' undeclared (first use in this function)
            r"(?P<before>^)(?P<filename>\S+)(?P<after>:\d+:\d+:\s+.*)",
            # Example: Compiling: ../Primate/main_srt.c
            r"(?P<before>^Compiling:\s+)(?P<filename>\S+)(?P<after>.*)",
            # Example: ../Primate/grc.c: In function 'grc_hisr_func':
            r"(?P<before>^)(?P<filename>\S+)(?P<after>\s+In function .*)",
            # Example: Linking: THORB0_DUAL_SIGNED_0001_0001/srt_bootcode.out
            r"(?P<before>^Linking:\s*)(?P<filename>\S+)(?P<after>.*)",
            # Example: Generating THORB0_DUAL_SIGNED_0001_0001/srt.bin file
            r"(?P<before>^Generating\s+)(?P<filename>\S+)(?P<after>.*)",
            # Example: Created THORB0_DUAL_SIGNED_0001_0001/srt_thor.signed.rev0001.bin
            r"(?P<before>^Created\s+)(?P<filename>\S+)(?P<after>.*)",
        ]
        new_lines = []
        for line in text.splitlines():
            line = line.rstrip('\r\n')
            for regex in regexs:
                match = re.search(regex, line)
                if match:
                    new_filename = self.translate_path(match.group("filename"))
                    line = match.group("before") + new_filename + match.group("after")
                    break
            new_lines.append(line + '\n')
        return ''.join(new_lines)

    def translate_path(self, path):
        return os.path.abspath(os.path.join(self.local_make_path, path))

    @property
    def local_make_path(self):
        if self._local_make_path is None:
            if self.chip == "thor":
                self._local_make_path = os.path.join(self.repo, self.THOR_MAKE_PATH)
            elif self.chip == "chimp":
                self._local_make_path = os.path.join(self.repo + self.CHIMP_MAKE_PATH)
            else:
                raise ValueError("Unsupported chip {chip}".format(chip=self.chip))
        print(f"local_make_path: {self._local_make_path}")
        return self._local_make_path


# 7-bit C1 ANSI sequences
ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

def remove_ansi_ctrl(text):
    return ansi_escape.sub('', text)
