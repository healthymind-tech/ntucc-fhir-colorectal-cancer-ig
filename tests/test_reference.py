"""Python reference implementation against the hand-written expectations."""

import json
from datetime import date
from pathlib import Path

import pytest

from reference.crc_indicators import PolypFacts, evaluate, proportion

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/synthetic-cases.json").read_text(encoding="utf-8"))
PERIOD = tuple(date.fromisoformat(d) for d in FIXTURE["measurement_period"])


def run(case):
    return evaluate(case["fields"], PolypFacts.from_json(case["polyp"]), PERIOD)


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda c: c["id"])
def test_case_matches_expectation(case):
    result = run(case)
    for expression, expected in case["expected"].items():
        assert expression in result, f"reference does not compute {expression}"
        assert result[expression] == expected, f"{case['id']}: {expression}"


def test_every_measure_has_both_outcomes_covered():
    asserted = {}
    for case in FIXTURE["cases"]:
        for expression, value in case["expected"].items():
            asserted.setdefault(expression, set()).add(value)
    for measure in (1, 2, 3):
        for expression in (f"Denominator {measure}", f"Numerator {measure}"):
            assert asserted.get(expression) == {True, False}, f"{expression} lacks a True or False case"


def test_proportion_counts_exclusions_out_of_numerator():
    results = [run(case) for case in FIXTURE["cases"]]
    counts = proportion(results, 2)
    assert counts["denominator"] >= counts["denominator-exclusion"] > 0
    assert counts["numerator"] <= counts["denominator"] - counts["denominator-exclusion"]
