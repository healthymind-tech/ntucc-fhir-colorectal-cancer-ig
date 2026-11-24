"""Candidate terminology mappings: integrity of the CSV and of what is generated from it."""

import csv
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / "mappings/terminology-candidates.csv").open(encoding="utf-8")))
GENERATED = ROOT / "ig/fsh-generated/resources"
LOCAL_SYSTEMS = {
    "tcr-field-to-loinc": "ig/input/fsh/tcr-terminology.fsh",
    "indicator-concept-to-standard": "ig/input/fsh/indicator-terminology.fsh",
}
CODE_FORMAT = {
    "http://loinc.org": re.compile(r"^\d{1,7}-\d$"),
    "http://snomed.info/sct": re.compile(r"^\d{6,18}$"),
}


def load_builder():
    spec = importlib.util.spec_from_file_location("build_terminology", ROOT / "scripts/build_terminology.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("row", ROWS, ids=lambda r: f"{r['map_id']}:{r['source_code']}:{r['target_code'] or 'unmatched'}")
def test_row_is_well_formed(row):
    fsh = (ROOT / LOCAL_SYSTEMS[row["map_id"]]).read_text(encoding="utf-8")
    assert f"#{row['source_code']} " in fsh, "source code is not defined in the local CodeSystem"
    if row["equivalence"] == "unmatched":
        assert not row["target_code"] and not row["target_system"]
    else:
        assert CODE_FORMAT[row["target_system"]].match(row["target_code"])
        assert row["target_display"] and row["verified_with"].startswith("tx.fhir.org")
    assert row["rationale"], "every candidate needs a written reason"
    if row["review_status"] != "unreviewed":
        assert row["reviewer"] and row["review_date"], "a review decision needs a reviewer and a date"


def test_csv_validation_rejects_bad_rows(tmp_path, monkeypatch):
    builder = load_builder()
    header = (ROOT / "mappings/terminology-candidates.csv").read_text(encoding="utf-8").splitlines()[0]
    good = ROWS[4]
    line = ",".join(good[k] for k in header.split(","))
    for bad in (
        [line, line],  # duplicate
        [line.replace(good["target_system"], "http://example.org/x")],  # unknown system
        [line.replace(good["source_display"], good["source_display"] + " ")],  # whitespace
    ):
        path = tmp_path / "c.csv"
        path.write_text("\n".join([header, *bad]) + "\n", encoding="utf-8")
        monkeypatch.setattr(builder, "CSV_PATH", path)
        with pytest.raises(SystemExit):
            builder.load_rows()


def test_generated_files_match_the_csv():
    builder = load_builder()
    rows = builder.load_rows()
    assert (ROOT / "ig/input/fsh/conceptmaps.fsh").read_text(encoding="utf-8") == builder.build_fsh(rows)
    assert (ROOT / "ig/input/includes/terminology-candidates-table.md").read_text(encoding="utf-8") == builder.build_table(rows)


@pytest.mark.skipif(not GENERATED.exists(), reason="run SUSHI first")
def test_every_candidate_reaches_a_conceptmap():
    expected = {
        (r["map_id"], r["source_code"], r["target_code"] or None, r["equivalence"])
        for r in ROWS
        if r["review_status"] != "rejected"
    }
    found = set()
    for map_id in LOCAL_SYSTEMS:
        cmap = json.loads((GENERATED / f"ConceptMap-{map_id}.json").read_text(encoding="utf-8"))
        assert cmap["status"] == "draft" and cmap["experimental"] is True
        for group in cmap["group"]:
            for element in group["element"]:
                for target in element["target"]:
                    found.add((map_id, element["code"], target.get("code"), target["equivalence"]))
                    assert target["comment"].startswith("[unreviewed]") or target["comment"].startswith("[accepted]")
    assert found == expected


@pytest.mark.skipif(not GENERATED.exists(), reason="run SUSHI first")
@pytest.mark.parametrize("example", ["crc-condition-colon", "crc-condition-rectum"])
def test_primary_condition_examples_keep_icdo3_and_snomed_separate(example):
    # A slice assignment after an indexed assignment once collapsed both codings
    # into one, leaving an ICD-O-3 code with a SNOMED display.
    condition = json.loads((GENERATED / f"Condition-{example}.json").read_text(encoding="utf-8"))
    codings = condition["bodySite"][0]["coding"]
    by_system = {coding["system"]: coding for coding in codings}
    assert len(codings) == 2 and set(by_system) == {"http://terminology.hl7.org/CodeSystem/icd-o-3", "http://snomed.info/sct"}
    assert re.match(r"^C\d{2}\.\d$", by_system["http://terminology.hl7.org/CodeSystem/icd-o-3"]["code"])
    assert "display" not in by_system["http://terminology.hl7.org/CodeSystem/icd-o-3"]
    morphology = condition["extension"][0]["valueCodeableConcept"]["coding"][0]["code"]
    assert re.match(r"^\d{4}/\d$", morphology)
