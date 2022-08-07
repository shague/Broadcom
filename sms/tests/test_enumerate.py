import logging
import re

from enumerate import enumerate_tests

log = logging.getLogger(__name__)
AUTESTS = "/git/au-tests/tests"
# AUTESTS = "/git/au-tests/tests/afm/ntuple"


def test_enumerate_tests():
    tests = enumerate_tests(AUTESTS)
    log.info(f"enumerated {len(tests)} tests")
    assert tests, f"failed to enumerate tests, len: {len(tests)}"


def test_re_sms():
    text = "@pytest.mark.sms_id('53230')"
    m = re.search(r"sms_id\(['\"](\d{5,})['\"]\)", text)
    if m:
        log.info(f"sms_id: {m.group(1)}")


def test_re_all():
    re_class = r"class\s+(Test\w+)\s*:"
    re_test1 = r"^def\s+(test_\w+)\s*\(.*"
    re_test2 = r"\s+def\s+(test_\w+)\s*\(.*"
    re_sms_id = r"sms_id\(['\"](\d{5,})['\"]\)"
    re_all = re.compile(rf"{re_class}|{re_test1}|{re_test2}|{re_sms_id}|foo")

    text = "    def test_foo():"
    m = re_all.search(text)
    if m:
        log.info(f"match: {m.group(0)}")
    if m and m.group(2):
        log.info(f"match 2: {m.group(2)}")
    if m and m.group(3):
        log.info(f"match 3: {m.group(3)}")
