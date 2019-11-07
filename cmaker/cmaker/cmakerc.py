import logging
from argparse import ArgumentParser
import os
from enum import Enum

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s | %(levelname).3s | %(name)-20s | %(lineno)04d | %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
fh = logging.FileHandler("/tmp/cmakerc.txt", "w")
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(min([ch.level, fh.level]))


def debug():
    ch.setLevel(logging.DEBUG)
    # logger.setLevel(min([ch.level, fh.level]))


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


def extract_define(token: str) -> ParseStatus:
    """
    Extract defines of the form -Ddefinition.
    """
    if token.startswith("-D"):
        define = token[len("-D"):]
        if define:
            defines.add(define)
        return ParseStatus.FOUND
    return ParseStatus.CONT


def extract_include(token: str, prefix: str, status=ParseStatus.CONT) -> ParseStatus:
    """
    Extract includes of the forms -I includedir or -Iincludedir.

    For the form, -I includedir, the value ParseStatus.MORE will be returned. The caller must
    call again with the next token and ParseStatus.MORE to be extracted.
    """
    if token.startswith("-I"):
        value = token[len("-I"):]
        if value:
            includes.add(prefix + value.strip('"'))
            return ParseStatus.FOUND
        else:  # this indicates the -I includedir so need to get the next token to complete the extraction.
            return ParseStatus.MORE
    else:  # the final token needed for the -I includedir case.
        if status == ParseStatus.MORE and token:
            includes.add(prefix + token.strip('"'))
            return ParseStatus.FOUND
    return ParseStatus.CONT


def extract_source(token: str, prefix: str) -> ParseStatus:
    """
    Extract source files that end with .c.
    """
    if ".c" in token:
        sources.add(prefix + token)
        return ParseStatus.FOUND
    return ParseStatus.CONT


def process_line(line: str) -> None:
    """
    Process each line and extra the wanted values.

    The line is split into tokens that are space-delimited. Each token is parsed by different parsers
    to extract the desired data.
    """
    # Only process compile lines.
    if not (line.startswith("armcc") or line.startswith("gcc")):
        return

    # Add a path prefix for lines where the path has changed due to different make calls.
    prefix = ""
    if "-Ibsp" in line:
        prefix = "../RTOS/Nucleus_3/"
    if "bc1" in line:
        prefix = "../bc1/"


    pstatus = ParseStatus.CONT
    tokens = line.split()
    for token in tokens:
        if pstatus == ParseStatus.MORE:
            extract_include(token, prefix, pstatus)
            pstatus = ParseStatus.CONT
            continue
        pstatus = extract_include(token, prefix, pstatus)
        if pstatus == ParseStatus.MORE:
            continue

        if extract_define(token) == ParseStatus.FOUND:
            continue

        if extract_source(token, prefix) == ParseStatus.FOUND:
            continue


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
    with open(args.buildfile) as f:
        for line in f:
            process_line(line)

    # Further correct the lists to include the compiler and to remove unneeded stuff.
    #includes.add("/opt/projects/ccxsw_tools/mentor_graphics/mgc-2018.070/toolchains/arm-none-eabi.2016.11"
    #             "/arm-none-eabi/include")
    # TODO: Below one is not so bad but it didn't remove from the set as expected. Possibly the wrong API
    # or the /'s need to be escaped
    # includes.remove("../../../common")

    make_cmakelist(args)


def create_parser():
    parser = ArgumentParser(prog="python cmaker", description="Create a CMakeFiles.txt for thor")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity level")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s (version {version})".format(version="0.0.1"))
    parser.add_argument("-o", "--outdir", help="the path to the output dir. Default: /tmp", default="/tmp")
    parser.add_argument("-n", "--name", help="the project name. Default: Cumulus", default="Cumulus")
    parser.add_argument("buildfile", help="the build output text file")
    return parser


def parse_args():
    parser = create_parser()
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    if args.verbose > 0:
        debug()
    parse_build(args)


if __name__ == "__main__":
    run()
