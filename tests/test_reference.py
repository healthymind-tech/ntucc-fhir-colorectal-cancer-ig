"""Python reference implementation against the hand-written expectations."""

import json
from datetime import date
from pathlib import Path

import pytest

from reference.crc_indicators import POPULATIONS, current_values, evaluate_case, proportion

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/synthetic-cases.json").read_text(encoding="utf-8"))
PERIOD = tuple(date.fromisoformat(d) for d in FIXTURE["measurement_period"])


def test_fixture_format():
    assert FIXTURE["format"] == "tumour-level-v2"


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda c: c["id"])
def test_case_matches_expectation(case):
    result = evaluate_case(case, PERIOD)
    for expression, expected in case["expected"].items():
        assert result[expression] == expected, f"{case['id']}: {expression}"


def test_every_population_has_members_and_non_members_somewhere():
    for measure in (1, 2, 3):
        for expression in (f"Denominator {measure}", f"Numerator {measure}"):
            asserted = [c["expected"][expression] for c in FIXTURE["cases"] if expression in c["expected"]]
            assert any(asserted) and any(not a for a in asserted), expression


def test_a_patient_with_two_primaries_contributes_two_cases():
    case = next(c for c in FIXTURE["cases"] if c["id"] == "multi-primary-colon-rectum")
    assert len(evaluate_case(case, PERIOD)["Initial Population"]) == 2


def test_current_value_is_the_latest_issued_regardless_of_order():
    versions = {"2.14": [
        {"id": "b", "value": "15", "issued": "2025-05-01T09:00:00+08:00", "status": "amended"},
        {"id": "a", "value": "11", "issued": "2025-04-01T09:00:00+08:00", "status": "final"},
        {"id": "c", "value": "99", "issued": "2025-06-01T09:00:00+08:00", "status": "entered-in-error"},
    ]}
    assert current_values(versions) == {"2.14": "15"}


def test_proportion_counts_exclusions_out_of_numerator():
    results = [evaluate_case(case, PERIOD) for case in FIXTURE["cases"]]
    counts = proportion(results, 2)
    assert counts["denominator"] >= counts["denominator-exclusion"] > 0
    assert counts["numerator"] <= counts["denominator"] - counts["denominator-exclusion"]
