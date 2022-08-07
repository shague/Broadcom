import argparse
import glob
import logging
import os
import re
import sys
from typing import Tuple

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)8s %(module)s(%(lineno)3s): %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

stats = {'changed': [], 'unchanged': []}


def update_testsuite(src, dst, values: Tuple[str, str]):
    with open(src, 'r') as f:
        src_data = f.read()
    changed_data = re.sub(rf"(.*rls_stream_to_sms_matrix.*){values[0]}(:.*)", rf"\1{values[1]}\2",
                          src_data, flags=re.MULTILINE|re.DOTALL)
    if src_data == changed_data:
        stats['unchanged'].append(src)
        return
    with open(dst, 'w') as f:
        stats['changed'].append(src)
        f.write(changed_data)


def update_testsuites(ts_folder: str, ts_file: str, out_folder: str, values: Tuple[str, str]):
    def dst_file(_ts_file, _out_folder):
        if out_folder:
            _dst = os.path.join(out_folder, os.path.basename(ts_file))
        else:
            _dst = ts_file
        return _dst

    if out_folder:
        os.makedirs(out_folder, exist_ok=True)

    if ts_file:
        dst = dst_file(ts_file, out_folder)
        update_testsuite(ts_file, dst, values)
    elif ts_folder:
        os.chdir(ts_folder)
        for ts_file in glob.glob("**/*.yml", recursive=True):
            dst = dst_file(ts_file, out_folder)
            update_testsuite(ts_file, dst, values)

    if log.isEnabledFor(logging.DEBUG):
        changed = ""
        for file in stats['changed']:
            changed += f"\n{file}"
        log.debug(f"changed {len(stats['changed'])} files:{changed}")


def parse_args(sysargs):
    parser = argparse.ArgumentParser(description="flatten nvm cfg xml")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("-d", "--directory", help="testsuite directory to search for yaml's to update")
    g.add_argument("-f", "--file", help="single testsuite.yaml to update")
    parser.add_argument("-o", "--output", help="output directory for yaml's instead of updating in place")
    parser.add_argument("-r", "--replace", help="replacement string", required=True)
    parser.add_argument("-s", "--search", help="search string to replace", required=True)
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging", default=False)
    return parser.parse_known_args(sysargs)


def main(sysargs):
    args, _ = parse_args(sysargs)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    update_testsuites(args.directory, args.file, args.output, (args.search, args.replace))


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
