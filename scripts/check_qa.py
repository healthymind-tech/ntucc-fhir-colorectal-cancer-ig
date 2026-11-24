"""Fail when the IG Publisher QA report contains errors or broken links.

The IG Publisher exits successfully even when qa.json reports errors, so CI
and the local build call this script to make those problems blocking. A
report without the expected keys also fails, so a change in the Publisher's
report format cannot silently disable the gate.

usage: python3 scripts/check_qa.py ig/output/qa.json
"""

import json
import sys

REQUIRED = ("errs", "warnings", "broken-links")


def main(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as handle:
            qa = json.load(handle)
    except (OSError, ValueError) as error:
        print(f"cannot read QA report {path}: {error}")
        return 1
    if "exception" in qa:
        print(f"IG Publisher failed: {qa['exception']}")
        return 1
    missing = [key for key in REQUIRED if not isinstance(qa.get(key), int)]
    if missing:
        print(f"QA report lacks {', '.join(missing)}; refusing to treat it as clean")
        return 1
    print(f"IG Publisher QA: errors={qa['errs']} broken-links={qa['broken-links']} warnings={qa['warnings']}")
    return 1 if qa["errs"] or qa["broken-links"] else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
