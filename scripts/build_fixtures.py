"""Build the synthetic test fixtures shared by the Python reference and the CQL.

Writes:
  tests/fixtures/synthetic-cases.json     flat registry records + hand-written expectations
  tests/fixtures/cql/cases.json           the same cases as FHIR R4 Bundles (runner input)
  tests/fixtures/cql/value-sets.json      ValueSet expansions read from SUSHI output

Every value is synthetic. Expectations are written by hand from the official
text, never copied from either implementation's output.

Run from the repository root after SUSHI:  python3 scripts/build_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig"
FIELD_CS = f"{CANON}/CodeSystem/crc-tcr-field"
CONCEPT_CS = f"{CANON}/CodeSystem/crc-indicator-concept"
TCR_PROFILE = f"{CANON}/StructureDefinition/crc-tcr-data-item-observation"

COLON = {"2.3": "1", "2.5": "20250305", "2.6": "C187", "2.8": "8140", "2.9": "3", "2.12": "20250305",
         "2.14": "15", "3.7": "3B", "3.13": "3B", "4.1": "20250320", "4.1.4": "30"}
RECTUM = {"2.3": "1", "2.5": "20250110", "2.6": "C209", "2.8": "8140", "2.9": "3", "2.12": "20250110",
          "3.7": "2A", "3.13": "2A", "4.1": "20250221", "4.1.4": "40"}
POLYP_REGISTRY = {"2.3": "1", "2.5": "20250301", "2.6": "C187", "2.8": "8140", "2.9": "3", "2.12": "20250301",
                  "3.7": "1", "3.13": "1", "4.1": "20250301", "4.1.4": "27"}
POLYP = {"malignant_polyp": "confirmed", "report_issued": "2025-03-01",
         "features": {"B": True}, "resections": [{"date": "2025-05-24", "status": "completed"}]}


def case(case_id, description, fields, expected, base=None, polyp=None):
    merged = dict(base or {})
    for key, value in fields.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return {"id": case_id, "description": description, "fields": merged, "polyp": polyp, "expected": expected}


CASES = [
    # ---- shared initial population -------------------------------------------------
    case("ip-class-1", "Class 1、2025 新診斷：納入", {}, {"Initial Population": True}, COLON),
    case("ip-class-0", "Class 0 不納入", {"2.3": "0"}, {"Initial Population": False}, COLON),
    case("ip-class-3", "Class 3 不納入", {"2.3": "3"}, {"Initial Population": False}, COLON),
    case("ip-dx-unknown", "最初診斷日期 99999999：無法判定收錄年度", {"2.5": "99999999"}, {"Initial Population": False}, COLON),
    case("ip-dx-outside-period", "2024 年診斷，不在 2025 量測期間", {"2.5": "20241231"}, {"Initial Population": False}, COLON),
    case("ip-cross-hospital", "註3 跨院治療：class 2、診斷狀態 2、治療狀態 3",
         {"2.3": "2", "CLASS-DX-STATUS": "2", "CLASS-TX-STATUS": "3"},
         {"Initial Population": False, "Cross Hospital Treatment": True}, COLON),
    case("ip-class-2-full-course", "Class 2、全部首次療程在本院：納入",
         {"2.3": "2", "CLASS-DX-STATUS": "2", "CLASS-TX-STATUS": "2"},
         {"Initial Population": True, "Cross Hospital Treatment": False}, COLON),
    # ---- crc-qi-02 ----------------------------------------------------------------
    case("qi02-met", "乙狀結腸 3B 期、部分結腸切除、15 顆", {},
         {"Denominator 2": True, "Denominator 2 Exclusion": False, "Numerator 2": True}, COLON),
    case("qi02-nodes-11", "淋巴結 11 顆：不符分子", {"2.14": "11"}, {"Denominator 2": True, "Numerator 2": False}, COLON),
    case("qi02-nodes-12", "淋巴結 12 顆：下界", {"2.14": "12"}, {"Numerator 2": True}, COLON),
    case("qi02-nodes-90", "淋巴結 90 顆：上界", {"2.14": "90"}, {"Numerator 2": True}, COLON),
    case("qi02-nodes-95", "2.14=95：不在 12~90", {"2.14": "95"}, {"Denominator 2": True, "Numerator 2": False}, COLON),
    case("qi02-appendix", "闌尾 C18.1：115/06/18 起排除", {"2.6": "C181"},
         {"Is Colon Excluding Appendix": False, "Denominator 2": False}, COLON),
    case("qi02-dotted-site", "部位寫成 C18.7：視同 C187", {"2.6": "C18.7"}, {"Denominator 2": True}, COLON),
    case("qi02-rectum-not-colon", "直腸 C20.9 不屬結腸", {"2.6": "C209"}, {"Denominator 2": False}, COLON),
    case("qi02-polypectomy", "手術方式 27（局部切除）：<30 排除", {"4.1.4": "27"},
         {"Has Resection Surgery 30 To 90": False, "Denominator 2": False}, COLON),
    case("qi02-surgery-90", "手術方式 90：上界", {"4.1.4": "90"}, {"Denominator 2": True}, COLON),
    case("qi02-surgery-99", "手術方式 99（不詳）", {"4.1.4": "99"}, {"Denominator 2": False}, COLON),
    case("qi02-stage-4", "病理第 4 期", {"3.13": "4"}, {"Denominator 2": False}, COLON),
    case("qi02-stage-0", "病理第 0 期", {"3.13": "0"}, {"Denominator 2": False}, COLON),
    case("qi02-stage-unknown", "病理期別 999", {"3.13": "999"}, {"Denominator 2": False}, COLON),
    case("qi02-stage-1", "病理第 1 期", {"3.13": "1"}, {"Is Pathological Stage I To III": True, "Denominator 2": True}, COLON),
    case("qi02-gist", "GIST 8936：特殊組織型態排除", {"2.8": "8936"},
         {"Denominator 2": True, "Denominator 2 Exclusion": True}, COLON),
    case("qi02-net", "NET 8240：特殊組織型態排除", {"2.8": "8240"}, {"Denominator 2 Exclusion": True}, COLON),
    # ---- crc-qi-03 ----------------------------------------------------------------
    case("qi03-42-days", "直腸 2A 期、確診後第 42 天開始治療", {},
         {"Denominator 3": True, "Days From Confirmation To First Course": 42, "Numerator 3": True}, RECTUM),
    case("qi03-43-days", "第 43 天開始治療", {"4.1": "20250222"}, {"Denominator 3": True, "Numerator 3": False}, RECTUM),
    case("qi03-class-2", "Class 2 不納入指標 3", {"2.3": "2"}, {"Initial Population": True, "Denominator 3": False}, RECTUM),
    case("qi03-rectosigmoid", "直腸乙狀結腸交界 C19.9", {"2.6": "C19.9"}, {"Denominator 3": True}, RECTUM),
    case("qi03-stage-3c", "臨床 3C 期", {"3.7": "3C"}, {"Denominator 3": True}, RECTUM),
    case("qi03-stage-1", "臨床第 1 期不納入", {"3.7": "1"}, {"Denominator 3": False}, RECTUM),
    case("qi03-stage-4", "臨床第 4 期不納入", {"3.7": "4A"}, {"Denominator 3": False}, RECTUM),
    case("qi03-colon", "結腸不屬指標 3", {"2.6": "C187"}, {"Denominator 3": False}, RECTUM),
    case("qi03-no-treatment-date", "首次療程開始日期 00000000（未治療）", {"4.1": "00000000"},
         {"Denominator 3": True, "Numerator 3": False}, RECTUM),
    case("qi03-unknown-confirmation", "首次顯微鏡檢證實日期 99999999", {"2.12": "99999999"},
         {"Denominator 3": True, "Numerator 3": False}, RECTUM),
    case("qi03-invalid-calendar-date", "4.1=20250231（不存在之日期）", {"4.1": "20250231"},
         {"Numerator 3": False}, RECTUM),
    # ---- crc-qi-01 ----------------------------------------------------------------
    case("qi01-day-84", "條件 B、病理報告後第 84 天治癒性切除", {},
         {"Denominator 1": True, "Numerator 1": True}, POLYP_REGISTRY, POLYP),
    case("qi01-day-85", "第 85 天切除：超過 12 週", {},
         {"Denominator 1": True, "Numerator 1": False}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"date": "2025-05-25", "status": "completed"}]}),
    case("qi01-day-0", "報告當日切除", {}, {"Numerator 1": True}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"date": "2025-03-01", "status": "completed"}]}),
    case("qi01-before-report", "報告前一天之切除不算", {}, {"Numerator 1": False}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"date": "2025-02-28", "status": "completed"}]}),
    case("qi01-not-done", "切除 status=not-done", {}, {"Denominator 1": True, "Numerator 1": False}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"date": "2025-04-01", "status": "not-done"}]}),
    case("qi01-no-feature", "A–D 皆記載為不成立：不屬分母", {}, {"Has High Risk Feature": False, "Denominator 1": False},
         POLYP_REGISTRY, {**POLYP, "features": {"A": False, "B": False, "C": False, "D": False}}),
    case("qi01-feature-a-only", "只有條件 A（大腸鏡報告）", {}, {"Denominator 1": True}, POLYP_REGISTRY,
         {**POLYP, "features": {"A": True}}),
    case("qi01-unconfirmed-polyp", "惡性息肉未確認", {}, {"Has Malignant Polyp": False, "Denominator 1": False},
         POLYP_REGISTRY, {**POLYP, "malignant_polyp": "provisional"}),
    case("qi01-no-polyp-facts", "沒有惡性息肉臨床事實", {}, {"Denominator 1": False, "Numerator 1": False}, COLON),
]

FEATURE_CODES = {
    "A": "criterion-a-polyp-incompletely-excised",
    "B": "criterion-b-margin-positive",
    "C": "criterion-c-lymphovascular-invasion",
    "D": "criterion-d-grade3-poorly-differentiated",
}


def ref(kind, rid):
    return {"reference": f"{kind}/{rid}"}


def to_bundle(item):
    pid = item["id"]
    subject = ref("Patient", pid)
    tumour = f"{pid}-tumour"
    entries = [
        {"resourceType": "Patient", "id": pid, "gender": "male", "birthDate": "1960-01-01"},
        {"resourceType": "Condition", "id": tumour, "subject": subject,
         "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "C18.7"}]}},
    ]
    for number, value in item["fields"].items():
        entries.append({
            "resourceType": "Observation", "id": f"{pid}-f{number.replace('.', '-').lower()}",
            "meta": {"profile": [TCR_PROFILE]}, "status": "final",
            "code": {"coding": [{"system": FIELD_CS, "code": number}]},
            "subject": subject, "focus": [ref("Condition", tumour)], "valueString": value,
        })
    polyp = item.get("polyp")
    if polyp:
        entries.append({
            "resourceType": "Condition", "id": f"{pid}-polyp", "subject": subject,
            "verificationStatus": {"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": polyp["malignant_polyp"]}]},
            "code": {"coding": [{"system": CONCEPT_CS, "code": "malignant-polyp-t1"}]},
        })
        entries.append({
            "resourceType": "DiagnosticReport", "id": f"{pid}-report", "status": "final", "subject": subject,
            "code": {"coding": [{"system": CONCEPT_CS, "code": "malignant-polyp-pathology-report"}]},
            "issued": f"{polyp['report_issued']}T10:00:00+08:00",
        })
        for letter, present in polyp["features"].items():
            entries.append({
                "resourceType": "Observation", "id": f"{pid}-feature-{letter.lower()}", "status": "final",
                "code": {"coding": [{"system": CONCEPT_CS, "code": FEATURE_CODES[letter]}]},
                "subject": subject, "valueBoolean": present,
            })
        for index, resection in enumerate(polyp["resections"]):
            entries.append({
                "resourceType": "Procedure", "id": f"{pid}-resection-{index}", "status": resection["status"],
                "code": {"coding": [{"system": CONCEPT_CS, "code": "curative-resection"}]},
                "subject": subject, "performedDateTime": f"{resection['date']}T09:00:00+08:00",
            })
    return {"resourceType": "Bundle", "type": "collection",
            "meta": {"tag": [{"system": f"{CANON}/CodeSystem/fixture-tag", "code": "synthetic"}]},
            "entry": [{"resource": r} for r in entries]}


def value_sets():
    expansions = {}
    for path in sorted((ROOT / "ig/fsh-generated/resources").glob("ValueSet-*.json")):
        vs = json.loads(path.read_text(encoding="utf-8"))
        codes = [{"system": inc["system"], "code": c["code"]}
                 for inc in vs.get("compose", {}).get("include", []) for c in inc.get("concept", [])]
        if codes:
            expansions[vs["url"]] = {vs.get("version", "0.1.0-preview.1"): codes}
    return expansions


def main():
    fixtures = ROOT / "tests/fixtures"
    (fixtures / "cql").mkdir(parents=True, exist_ok=True)
    flat = {"measurement_period": ["2025-01-01", "2025-12-31"], "cases": CASES}
    (fixtures / "synthetic-cases.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runner = [{"id": c["id"], "expected": c["expected"], "bundle": to_bundle(c)} for c in CASES]
    (fixtures / "cql/cases.json").write_text(json.dumps(runner, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    vs = value_sets()
    if not vs:
        raise SystemExit("no ValueSets found; run SUSHI first")
    (fixtures / "cql/value-sets.json").write_text(json.dumps(vs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(CASES)} cases, {len(vs)} value sets")


if __name__ == "__main__":
    main()
