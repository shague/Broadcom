import json
import os.path
import re
from argparse import ArgumentParser
import logging
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


cmake_template = '''cmake_minimum_required(VERSION 3.14)

set(CMAKE_SYSTEM_NAME Generic)
# set(CMAKE_CROSSCOMPILING TRUE)
# set(CMAKE_SYSTEM_PROCESSOR arm)
# set(CMAKE_C_COMPILER /usr/local/bin/arm-none-eabi-gcc)
set(CMAKE_C_COMPILER_FORCED TRUE)
set(CMAKE_CXX_COMPILER_FORCED TRUE)
# set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")

project({})

add_custom_target(thor COMMAND /Users/shague/bin/buildthor.sh -u shague -i 127.0.0.1 -p 2021)
add_custom_target(thor-clean-all COMMAND /Users/shague/bin/buildthor.sh -u shague -i 127.0.0.1 -p 2021 -n)
add_custom_target(thor-dbg COMMAND /Users/shague/bin/buildthor.sh -u shague -i 127.0.0.1 -p 2021 -d -l)
add_custom_target(thor-dbg-signed COMMAND /Users/shague/bin/buildthor.sh -u shague -i 127.0.0.1 -p 2021 -d -l -c CRID=0001 -s /home/shague/sign.txt)


add_compile_definitions(
  {}
)

include_directories(
  {}
)

add_executable({}
  {}
)
'''

dirs = set()
defs = set()
incs = set()
exes = set()


def make_relative(src: str, root: str):
    if src.startswith('/'):
        com_path = os.path.commonpath([src, root])
        rel_path = os.path.relpath(com_path, root)
        return rel_path
        # incs.add(rel_path)
    else:
        return src
        # incs.add(inc)


def parse_cc(commands: list):
    re_incs = re.compile(r"-I ?(\S+)")  # all lines with -I path or -Ipath
    re_defs = re.compile(r"-D ?(\S+)")  # all lines with -D define or -Ddefine
    for obj in commands:
        dirs.add(obj['directory'])
        exes.add(make_relative(obj['file'], obj['directory']))
        all_args = " ".join(obj['arguments'])
        all_defs = re_defs.findall(all_args)
        for define in  all_defs:  # remove the __FILE__ lines
            if "__FILE__" not in define:
                defs.add(define)
        for inc in re_incs.findall(all_args):
            rel_path = make_relative(inc, obj['directory'])
            incs.add(rel_path)
    log.info("done")


def makelststr(tokens: set) -> str:
    """
    Make a space-delimited string composed of joined tokens.
    """
    lst = [token for token in tokens]
    lst.sort()
    lststr = "\n  ".join(lst)
    return lststr


def extras(defines, includes, executables):
    # TODO: multiple executables: eg, bnxtnvm and thor
    for define in list(defines):
        if define.startswith("__FILE__"):
            defines.remove(define)


def make_cmakelist(args):
    """
    Create the CMakeLists.txt file.
    """
    definelststr = makelststr(defs)
    includelststr = makelststr(incs)
    sourcelststr = makelststr(exes)
    output = cmake_template.format(args.name, definelststr, includelststr, args.name, sourcelststr)
    fname = args.output  # args.outdir + "/CMakeLists.txt"
    with open(fname, "w") as f:
        f.write(output)
        log.info("{} has been written".format(fname))


def parse_json(cc_json: str) -> list:
    with open(cc_json) as json_file:
        return json.load(json_file)


def parse_args(sysargs):
    parser = ArgumentParser(description="convert compile_commands.json to CMakeLists.txt")
    parser.add_argument("-n", "--name", help="the project name. Default: THOR", default="THOR")
    parser.add_argument("-i", "--input", help="input filename", default="compile_commands.json")
    parser.add_argument("-o", "--output", help="output filename", default="CMakeLists.txt")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging", default=False)
    return parser.parse_known_args(sysargs)


def main(sysargs):
    pargs, _ = parse_args(sysargs)
    if pargs.verbose:
        log.setLevel(logging.DEBUG)
    log.info(f"parsing input {pargs.input} to output {pargs.output}")
    cc_json = parse_json(pargs.input)
    parse_cc(cc_json)
    extras(defs, incs, exes)
    make_cmakelist(pargs)


if __name__ == "__main__":
    main(sys.argv[1:])
