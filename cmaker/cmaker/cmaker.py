import logging
from argparse import ArgumentParser
import os
import re
from enum import Enum

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s | %(levelname).3s | %(name)-20s | %(lineno)04d | %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
logfname = "/tmp/cmaker.txt"
fh = logging.FileHandler(logfname, "w")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(min([ch.level, fh.level]))


def debug(ch_level=logging.INFO, fh_level=logging.DEBUG):
    ch.setLevel(ch_level)
    ch.setLevel(fh_level)
    logger.setLevel(min(ch_level, fh_level))


def logfile(path: str):
    global fh
    global logfname
    logger.removeHandler(fh)
    fh.close()
    logfname = path
    fh = logging.FileHandler(path, "w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


cmake_template = '''
cmake_minimum_required(VERSION 3.14)
project({})

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


pwd = ""
mkdir = ""
blddir = ""
re_mkdir = re.compile(r"^make.* Entering directory `(\S*)'")  # group is the directory after Entering directory
re_cc = re.compile(r"^\s*(gcc|gcc|arm-none-eabi-gcc|armcc)")  # return the line if a compiler call is found
re_def = re.compile(r"-D(\S*)")  # return definitions after -D
re_inc = re.compile(r"-I (\S*)|-I(\S*)")  # return includes after -I
re_src = re.compile(r"\s*gcc.*\s(\S*\.c)")  # return source files found in gcc lines
cwd = os.getcwd()

defines = set([])
includes = set([])
sources = set([])


class ParseStatus(Enum):
    """
    Parsing status codes.

    FOUND: a value of the expected type was found.
    CONT: continue processing for the next types.
    MORE: a partial value of the expected type was found. The caller must call again with the next token.
    """
    FOUND = 1
    CONT = 2
    MORE = 3


def get_prefix_value(value: str, prefix: str, strip: str):
    """

    """
    pvalue = value.strip('"')
    if strip != "" and pvalue.startswith(strip):
        pvalue = pvalue[len(strip):]
    elif prefix != "" and not pvalue.startswith("/"):
        pvalue = (prefix + "/" + pvalue)
    logger.debug("pvalue: {}".format(pvalue))
    return pvalue


def get_rel_path(blddir, prefix):
    norm_prefix_path = os.path.normpath(prefix)
    rel_path = os.path.relpath(norm_prefix_path, blddir)
    logger.debug("add: {}".format(rel_path))
    return rel_path


def extract_defines(line: str) -> None:
    """
    Extract defines of the form -Ddefinition.
    """
    # regex to get any -D defines.
    for m in re_def.finditer(line):
        defines.add(m.group(1))


def extract_includes(line: str, prefix: str, blddir: str) -> None:
    """
    Extract includes of the forms -I includedir or -Iincludedir.

    For the form, -I includedir, the value ParseStatus.MORE will be returned. The caller must
    call again with the next token and ParseStatus.MORE to be extracted.
    """
    # regex to get any -I includes. The iterate over the list to add
    # any path prefix, normalize the path and then get a relative path from the build dir.
    for m in re_inc.finditer(line):
        # group(1): -I /path, group(2): -I/path
        group = m.group(1) if m.group(1) else m.group(2)
        rel_path = get_rel_path(blddir, get_prefix_value(group, prefix, ""))
        includes.add(rel_path)


def extract_source(line: str, prefix: str, blddir: str) -> None:
    """
    Extract source files that end with .c.
    """
    # regex to get a .c file.
    # Then add any path prefix, normalize the path and then get a relative path from the build dir.
    m = re_src.search(line)
    if m:
        rel_path = get_rel_path(blddir, get_prefix_value(m.group(1), prefix, ""))
        sources.add(rel_path)


def extract_mkdir(line: str) -> None:
    """
    Extract the Make directory lines by looking for Entering directory...
    """
    global mkdir
    m = re_mkdir.search(line)
    if m:
        mkdir = m.group(1)
        # /usr is in /git on the mac
        if mkdir.startswith("/usr"):
            mkdir = "/git" + mkdir
        logger.debug("new mkdir: {}".format(mkdir))


def extract_cc(line: str) -> bool:
    """
    Extract the compiler lines if a compiler call is found.
    """
    m = re_cc.search(line)
    if m:
        return True
    return False


def process_line(args, line: str) -> None:
    """
    Process each line and extra the wanted values.

    The line is split into tokens that are space-delimited. Each token is parsed by different parsers
    to extract the desired data.
    """

    # Get make directories if the make changes the cwd.
    if line.startswith("make"):
        extract_mkdir(line)
        return

    # Only process compile lines.
    if not extract_cc(line):
        return

    inc_prefix, src_prefix, _ = get_fixups(args, line, mkdir)
    extract_defines(line)
    extract_includes(line, inc_prefix, args.blddir)
    extract_source(line, src_prefix, args.blddir)


def get_fixups(args, line: str, mkdir: str):
    # Add a path prefix for lines where the path has changed due to different make calls.
    strip = ""
    inc_prefix = ""
    src_prefix = ""

    if args.platform == "thor" or args.platform == "cmba":
        # These builds don't print the Entering directory string and run the build
        # in parallel so it is difficult to get the prefixes matched up.
        if "-Ibsp" in line:
            inc_prefix = src_prefix = args.blddir + "/../RTOS/Nucleus_3"
        elif "bc1" in line:
            inc_prefix = src_prefix = args.blddir + "/../bc1"
        else:
            inc_prefix = src_prefix = args.blddir
    elif args.platform == "bnxt-mt" or args.platform == "lcdiag" or args.platform == "bnxt_en":
        inc_prefix = src_prefix = mkdir

    logger.debug("strip: {}, inc_prefix: {}, src_prefix: {}".format(strip, inc_prefix, src_prefix))
    return inc_prefix, src_prefix, strip


def makelststr(tokens: set) -> str:
    """
    Make a space-delimited string composed of joined tokens.
    """
    lst = [token for token in tokens]
    lst.sort()
    lststr = "\n  ".join(lst)
    return lststr


def make_cmakelist(args):
    """
    Create the CMakeLists.txt file.
    """
    definelststr = makelststr(defines)
    includelststr = makelststr(includes)
    sourcelststr = makelststr(sources)
    output = cmake_template.format(args.name, definelststr, includelststr, args.name, sourcelststr)
    fname = args.outdir + "/CMakeLists.txt"
    with open(fname, "w") as f:
        f.write(output)
        logger.info("{} has been written".format(fname))


def parse_build(args):
    """
    Parse a build output file to extract data and create the CMakeLists.txt file.
    """
    if os.path.isfile(args.buildfile) is False:
        logger.warning("{} is missing".format(args.buildfile))
        return

    logger.info("Parsing {}...".format(args.buildfile))
    logger.info("Logging to {}".format(logfname))
    with open(args.buildfile) as f:
        for line in f:
            process_line(args, line)

    # Further correct the lists to include the compiler and to remove unneeded stuff.
    add_extras(args)

    make_cmakelist(args)


def add_extras(args):
    if args.platform == "thor":
        includes.add("/opt/projects/ccxsw_tools/mentor_graphics/mgc-2018.070/toolchains/arm-none-eabi.2016.11"
                     "/arm-none-eabi/include")

    elif args.platform == "cmba":
        includes.add("/projects/armds/include")

    elif args.platform == "bnxt_en":
        pass

    elif args.platform == "bnxt-mt":
        pass


def create_parser():
    parser = ArgumentParser(prog="python cmaker", description="Create a CMakeFiles.txt for thor")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity level")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s (version {version})".format(version="0.0.1"))

    parser.add_argument("-b", "--blddir", help="the path to the dir where the make build started.")
    parser.add_argument("-o", "--outdir", help="the path to the output dir. Default: /tmp", default="/tmp")
    parser.add_argument("-n", "--name", help="the project name. Default: Cumulus", default="Cumulus")
    parser.add_argument("-p", "--platform", help="the platform, thor or cmba(wh+). Default thor.", default=None)
    parser.add_argument("buildfile", help="the build output text file")
    return parser


def parse_args():
    parser = create_parser()
    args = parser.parse_args()
    return args


def validate_args(args):
    if not args.blddir:
        print("Using . as blddir")
        args.blddir = "."
    return True


def run(args):
    if args.verbose > 0:
        debug(logging.DEBUG, logging.DEBUG)
    if not validate_args(args):
        return
    logger.info("platform: {}".format(args.platform))
    parse_build(args)


if __name__ == "__main__":
    pargs = parse_args()
    run(pargs)
