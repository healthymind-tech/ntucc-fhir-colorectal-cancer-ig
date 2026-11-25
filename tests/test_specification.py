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
        supplemental = [s["criteria"]["expression"] for s in measure.get("supplementalData", [])]
        assert supplemental, f"{path.name}: no supplemental data"
        for expression in supplemental:
            assert expression in DEFINES, f"{path.name}: unknown supplemental data define {expression!r}"


def test_source_hashes_match():
    manifest = (ROOT / "sources/hpa-115/SHA256SUMS").read_text(encoding="utf-8").split("\n")
    import hashlib
    for line in filter(None, manifest):
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((ROOT / "sources/hpa-115" / name).read_bytes()).hexdigest() == digest, name


@pytest.mark.skipif(not GENERATED.exists(), reason="run SUSHI first")
def test_site_value_sets_match_the_reference_implementation():
    from reference import cohort, crc_indicators

    def codes(vs_id):
        vs = json.loads((GENERATED / f"ValueSet-{vs_id}.json").read_text(encoding="utf-8"))
        return {c["code"].replace(".", "") for inc in vs["compose"]["include"] for c in inc["concept"]}

    assert codes("crc-colon-excluding-appendix") == crc_indicators.COLON_EXCLUDING_APPENDIX
    assert codes("crc-rectosigmoid-rectum") == crc_indicators.RECTOSIGMOID_OR_RECTUM
    colorectal = {s for s in codes("crc-colorectal-category") if cohort.cancer_category(s) == cohort.COLORECTAL}
    assert colorectal == codes("crc-colorectal-category")
    assert cohort.cancer_category("C181") is None and cohort.cancer_category("C210") is None


def test_named_lists_in_cql_match_the_reference_implementation():
    from reference import cohort, crc_indicators

    def cql_list(name):
        block = re.search(r'define "' + re.escape(name) + r'":\s*\{([^}]*)\}', CQL).group(1)
        return re.findall(r"'([^']*)'", block)

    assert set(cql_list("Special Histology")) == crc_indicators.SPECIAL_HISTOLOGY
    assert tuple(cql_list("Stage Severity Order")) == cohort.STAGE_SEVERITY_ORDER
