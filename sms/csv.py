"""
- walk all py files
  - grep for sms_id, track file.py::{class}::{test_function} as script
  - add sms_id to tests dict as {'id': sms_id, 'script': script}
- read in tests.csv
- loop over rows
  - extract sms test id from ID (first column) for rows with Keep / Remove==y (third column)
  - update existing id in test dict, add new, set 'automated:True'
- loop over test dict keys
  if automated==True
  - new automated dict keys as module name, /au-tests/...
  - add ids: [], append id
- loop over automated dict
  - create testsuite.yml, add include, sms_id, add path, add sms ids 10 per line
"""
import logging
import re
import sys
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)


def get_sms_ids(csv_file: str) -> List[int]:
    file = Path(csv_file)
    if not file.is_file():
        raise ValueError(f"can't find {file}")
    str_ids = file.read_text().split(",")
    return [int(i) for i in str_ids]


def get_ts_sms_ids(ts_path: str) -> List[int]:
    ts_sms_ids = []
    ts_file = Path(ts_path)
    text = ts_file.read_text().splitlines()
    for line in text:
        m = re.findall(r"\d{5}", line)
        if m:
            for sms_id in m:
                ts_sms_ids.append(int(sms_id))
    return ts_sms_ids


def get_dups(ids: List[int], id_type: str) -> List[int]:
    dups = []
    tmp = []
    for i in ids:
        if i in tmp:
            dups.append(i)
        else:
            tmp.append(i)
    log.info(f"dups in {id_type}:\n{fmt_ids(sorted(dups))}")
    return dups


def fmt_ids(ids: List[int]) -> str:
    out = ""
    for cnt, value in enumerate(ids):
        if cnt % 10:
            out += f" {value}"
        elif cnt:
            out += f"\n{value}"
        else:
            out += f"{value}"
    return out


def get_diff(ids1, ids2, text: str):
    s_ids2 = set(ids2)
    x_ids = [x for x in ids1 if x not in s_ids2]
    log.info(f"diff {text}:\n{fmt_ids(sorted(x_ids))}")


def verify_ids(sms_ids, ts_sms_ids):
    dups_in_sms = get_dups(sms_ids, "sms_ids")
    dups_in_ts = get_dups(ts_sms_ids, "ts_sms_ids")

    get_diff(sms_ids, ts_sms_ids, "missing in ts")
    get_diff(ts_sms_ids, sms_ids, "missing in sms")


def main(argv):
    if len(argv) == 3:
        csv_path = argv[1]
        ts_path = argv[2]
    else:
        csv_path = "/tmp/221.sms.txt"
        ts_path = "/tmp/thor.yml"
    log.info(f"verify csv file: {csv_path} with ts file: {ts_path}")
    sms_ids = get_sms_ids(csv_path)
    ts_sms_ids = get_ts_sms_ids(ts_path)
    verify_ids(sms_ids, ts_sms_ids)


if __name__ == "__main__":
    exit(main(sys.argv))
