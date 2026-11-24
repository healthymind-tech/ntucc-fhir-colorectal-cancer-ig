"""Crosswalk from this IG's TCR field codes to TWCR_LF 0.1.1: integrity of the CSV and of the IG page."""

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "mappings/twcr-lf-crosswalk.csv"
PAGE_PATH = ROOT / "ig/input/pagecontent/twcr-lf.md"
ROWS = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))

# The crosswalk must cover exactly the fields of the crc-tcr-field CodeSystem,
# so a field added to the IG cannot be left out of the crosswalk.
EXPECTED_FIELDS = set(re.findall(
    r'^\* #([0-9.]+) "', (Path(__file__).resolve().parents[1] / "ig/input/fsh/tcr-terminology.fsh").read_text(encoding="utf-8"),
    flags=re.M))
COLUMNS = [
    "crc_tcr_field", "field_name", "twcr_lf_logical_element", "twcr_lf_profile_url",
    "twcr_lf_element_path", "twcr_lf_value_type", "twcr_lf_codesystem_url",
    "twcr_lf_codesystem_title", "notes",
]
TWCR_LF_CANONICAL = "https://hapi.fhir.tw/fhir/"


def test_columns():
    with CSV_PATH.open(encoding="utf-8") as f:
        assert next(csv.reader(f)) == COLUMNS


def test_field_codes_unique():
    codes = [r["crc_tcr_field"] for r in ROWS]
    assert len(codes) == len(set(codes))


def test_covers_exactly_the_ig_field_set():
    assert {r["crc_tcr_field"] for r in ROWS} == EXPECTED_FIELDS


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["crc_tcr_field"])
def test_row_has_mapping_or_explanation(row):
    mapped = row["twcr_lf_logical_element"].strip() and row["twcr_lf_profile_url"].strip()
    assert mapped or row["notes"].strip(), "unmapped row must explain why in notes"


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["crc_tcr_field"])
def test_urls_use_twcr_lf_canonical(row):
    for col in ("twcr_lf_profile_url", "twcr_lf_codesystem_url"):
        if row[col]:
            assert row[col].startswith(TWCR_LF_CANONICAL), col
    if row["twcr_lf_logical_element"]:
        assert row["twcr_lf_logical_element"].startswith("TWCRLF.")
    if row["twcr_lf_codesystem_url"]:
        assert row["twcr_lf_codesystem_title"].strip()


def test_page_mentions_every_field_code():
    page = PAGE_PATH.read_text(encoding="utf-8")
    for row in ROWS:
        code = re.escape(row["crc_tcr_field"])
        # Not preceded or followed by another digit/dot-digit, so "2.3" does not match only via "2.3.1".
        assert re.search(rf"(?<![\d.]){code}(?![\d]|\.\d)", page), row["crc_tcr_field"]


def test_page_starts_with_disclaimer_and_has_no_h1():
    page = PAGE_PATH.read_text(encoding="utf-8")
    assert page.startswith("{% include disclaimer.md %}")
    assert not re.search(r"^# ", page, re.MULTILINE)
