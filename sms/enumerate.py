import argparse
import logging
import os.path
import pathlib
import re
import sys
from copy import deepcopy

log = logging.getLogger(__name__)


class Module:
    def __init__(self, name):
        self.name = name
        self.classes = {}
        self.functions = {}
        self.sms_ids = {}

    def update(self, classes=None, functions=None, sms_ids=None):
        if classes:
            self.classes.update(classes)
        if functions:
            self.functions.update(functions)
        if sms_ids:
            self.sms_ids.update(sms_ids)


class Data:
    def __init__(self):
        self.modules = {}
        self.classes = {}
        self.functions = {}
        self.sms_ids = {}

    def update(self, modules, classes):

def enumerate_tests(tests_folder: str) -> list:
    if not os.path.isdir(tests_folder):
        raise ValueError(f"autests path not found: {tests_folder}")

    re_class = r"class\s+(Test\w+)\s*:"
    re_test1 = r"^def\s+(test_\w+)\s*\(.*"
    re_test2 = r"\s+def\s+(test_\w+)\s*\(.*"
    re_sms_id = r"sms_id\(['\"](\d{5,})['\"]\)"
    re_all = re.compile(rf"{re_class}|{re_test1}|{re_test2}|{re_sms_id}|foo")
    # get a list of all test*.py files
    files = list(pathlib.Path(tests_folder).glob(r"**/test_*.py"))

    data = Data()
    # parse each test.py file to get test data
    for file in sorted(files):
        log.info(f"processing {file}")
        cls = None
        classes = {}
        tests = {}
        sms_ids = {}
        in_class = None
        in_test = None
        in_sms_ids = []
        fpath = str(file)
        module = Module(fpath)
        data.modules[fpath] = module
        # modules[fpath] = {'classes': {}, 'tests': {}, 'sms_ids': {}}
        text = file.read_text().splitlines()
        for line in text:
            m = re_all.search(line)
            if m:
                if m.group(1):
                    in_class = m.group(1)
                    classes[in_class] = {}
                    tests.clear()
                    cls = {'name': in_class, 'tests': {}, 'sms_ids': in_sms_ids}
                    modules['classes'][in_class] = cls
                elif m.group(2):
                    in_test = m.group(2)
                    test = {'name': in_test, 'module': fpath, 'class': in_class, 'sms_ids': in_sms_ids}
                    tests[in_test] = test
                    cls = None
                    in_sms_ids = []
                elif m.group(3):
                    in_test = m.group(3)
                    test = {'name': in_test, 'module': fpath, 'class': in_class, 'sms_ids': in_sms_ids}
                    if cls:
                        cls['tests'][in_test] = test
                    else:
                        raise RuntimeWarning(f"function not in class: module: {fpath}, function: {in_test}")
                else:
                    in_sms_ids.append(m.group(4))
                log.info(f"re: {in_class}::{in_test}::{in_sms_ids}")
                if in_test:
                    in_test = None
                    in_sms_ids.clear()
    return files


def parse_args(sysargs):
    parser = argparse.ArgumentParser(description="parse csv and create testsuite yml")
    parser.add_argument("-d", "--directory", help="au-tests directory to search for test*.py files")
    parser.add_argument("-f", "--file", help="output testsuite.yml")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging", default=False)
    return parser.parse_known_args(sysargs)


def main(sysargs):
    args, _ = parse_args(sysargs)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    files = enumerate_tests(args.directory)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
