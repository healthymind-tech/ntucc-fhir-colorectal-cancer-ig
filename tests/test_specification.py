"""The criteria table, the CQL and the generated Measures must agree."""

import csv
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = list(csv.DictReader((ROOT / "mappings/crc-core-indicator-criteria.csv").open(encoding="utf-8")))
CQL = (ROOT / "ig/input/cql/ColorectalCancerCoreIndicators.cql").read_text(encoding="utf-8")
REFERENCE = (ROOT / "reference/crc_indicators.py").read_text(encoding="utf-8")
GENERATED = ROOT / "ig/fsh-generated/resources"
DEFINES = set(re.findall(r'^define (?:function )?"([^"]+)"', CQL, flags=re.M))


def test_criterion_ids_are_unique():
    ids = [row["criterion_id"] for row in CRITERIA]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("row", [r for r in CRITERIA if r["cql_define"]], ids=lambda r: r["criterion_id"])
def test_criterion_points_at_an_existing_define(row):
    assert row["cql_define"] in DEFINES


@pytest.mark.parametrize("row", [r for r in CRITERIA if r["status"].startswith("implemented")], ids=lambda r: r["criterion_id"])
def test_implemented_criterion_is_cited_in_both_implementations(row):
    cid = row["criterion_id"]
    assert cid in CQL, f"{cid} not cited in CQL"
    assert cid in REFERENCE, f"{cid} not cited in reference implementation"


def test_task_layer_criteria_are_not_silently_implemented():
    for row in CRITERIA:
        if row["status"] == "task-layer":
            assert not row["cql_define"], row["criterion_id"]


@pytest.mark.skipif(not GENERATED.exists(), reason="run SUSHI first")
def test_measure_populations_resolve_to_defines():
    measures = sorted(GENERATED.glob("Measure-*.json"))
    assert [m.stem for m in measures] == ["Measure-crc-qi-01", "Measure-crc-qi-02", "Measure-crc-qi-03"]
    for path in measures:
        measure = json.loads(path.read_text(encoding="utf-8"))
        for population in measure["group"][0]["population"]:
            assert population["criteria"]["expression"] in DEFINES


def test_source_hashes_match():
    manifest = (ROOT / "sources/hpa-115/SHA256SUMS").read_text(encoding="utf-8").split("\n")
    import hashlib
    for line in filter(None, manifest):
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((ROOT / "sources/hpa-115" / name).read_bytes()).hexdigest() == digest, name
