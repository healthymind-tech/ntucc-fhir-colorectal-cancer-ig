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
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference import icdo3  # noqa: E402  (shared, tested registry -> ICD-O-3 rule)

ROOT = Path(__file__).resolve().parents[1]
CANON = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig"
FIELD_CS = f"{CANON}/CodeSystem/crc-tcr-field"
CONCEPT_CS = f"{CANON}/CodeSystem/crc-indicator-concept"
TCR_PROFILE = f"{CANON}/StructureDefinition/crc-tcr-data-item-observation"
CLINICAL_ACTIVE = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]}
PROBLEM_LIST = [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}]}]
# TW Core Patient requires an identifier; synthetic national-ID-shaped values only.
ID_CARD_TYPE = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "NNxxx"}]}

COLON = {"1.1": "0401180014", "2.3": "1", "2.5": "20250305", "2.6": "C187", "2.8": "8140", "2.9": "3", "2.12": "20250305",
         "2.14": "15", "3.7": "3B", "3.13": "3B", "4.1": "20250320", "4.1.4": "30"}
RECTUM = {"1.1": "0401180014", "2.3": "1", "2.5": "20250110", "2.6": "C209", "2.8": "8140", "2.9": "3", "2.12": "20250110",
          "3.7": "2A", "3.13": "2A", "4.1": "20250221", "4.1.4": "40"}
POLYP_REGISTRY = {"1.1": "0401180014", "2.3": "1", "2.5": "20250301", "2.6": "C187", "2.8": "8140", "2.9": "3", "2.12": "20250301",
                  "3.7": "1", "3.13": "1", "4.1": "20250301", "4.1.4": "27"}
POLYP = {"malignant_polyp": "confirmed", "report_issued": "2025-03-01",
         "features": {"B": True}, "resections": [{"date": "2025-05-24", "status": "completed"}]}


POPULATIONS = ("Initial Population", "Denominator 1", "Numerator 1", "Denominator 2",
               "Denominator 2 Exclusion", "Numerator 2", "Denominator 3", "Numerator 3")
DEFAULT_ISSUED = "2025-04-30T17:00:00+08:00"


def tumour(tumour_id, fields, base=None, polyp=None):
    """One primary tumour. A field value is a raw string (one final version) or a
    list of {"value", "issued", "status"} versions."""
    merged = dict(base or {})
    for key, value in fields.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return {"id": tumour_id, "fields": merged, "polyp": polyp}


def case(case_id, description, fields, expected, base=None, polyp=None):
    """A single-tumour case. Boolean expectations mean "this case's tumour is /
    is not in the population"; they are turned into tumour-id lists. Only
    population expressions are asserted: the library's helpers are functions
    of a tumour and are exercised through the populations."""
    tid = f"{case_id}-tumour"
    lists = {k: ([tid] if v else []) for k, v in expected.items() if k in POPULATIONS}
    return multi(case_id, description, [tumour(tid, fields, base, polyp)], lists)


def multi(case_id, description, tumours, expected, national_id="present"):
    unknown = set(expected) - set(POPULATIONS)
    if unknown:
        raise SystemExit(f"{case_id}: not a population expression: {unknown}")
    for t in tumours:
        versions = {}
        for number, value in t["fields"].items():
            items = value if isinstance(value, list) else [{"value": value}]
            versions[number] = [
                {"id": f"{t['id']}-f{number.replace('.', '-')}-v{k:02d}", "value": v["value"],
                 "issued": v.get("issued", DEFAULT_ISSUED), "status": v.get("status", "final")}
                for k, v in enumerate(items)
            ]
        t["fields"] = versions
    return {"id": case_id, "description": description,
            "national_id": case_id if national_id else None, "tumours": tumours,
            "expected": {k: sorted(v) for k, v in expected.items()}}


CASES = [
    # ---- shared initial population -------------------------------------------------
    case("ip-class-1", "Class 1、2025 新診斷：納入", {}, {"Initial Population": True}, COLON),
    case("ip-class-0", "Class 0 不納入", {"2.3": "0"}, {"Initial Population": False}, COLON),
    case("ip-class-3", "Class 3 不納入", {"2.3": "3"}, {"Initial Population": False}, COLON),
    case("ip-dx-unknown", "最初診斷日期 99999999：無法判定收錄年度", {"2.5": "99999999"}, {"Initial Population": False}, COLON),
    case("ip-dx-outside-period", "2024 年診斷，不在 2025 量測期間", {"2.5": "20241231"}, {"Initial Population": False}, COLON),
    case("ip-cross-hospital", "註3 跨院治療：class 2、診斷狀態 2、治療狀態 3",
         {"2.3": "2", "2.3.1": "2", "2.3.2": "3"},
         {"Initial Population": False, "Cross Hospital Treatment": True}, COLON),
    case("ip-class-2-full-course", "Class 2、全部首次療程在本院：納入",
         {"2.3": "2", "2.3.1": "2", "2.3.2": "2"},
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


# ---- tumour as the unit, current registry value, linked indicator-1 facts ------
def _t(case_id, suffix):
    return f"{case_id}-{suffix}"


CASES += [
    # ---- case assembly (reference/cohort.py, case-assembly page) ----------------
    multi("dedup-earlier-diagnosis", "同院同病人兩顆結腸癌：留最初診斷日期較早者",
          [tumour(_t("dedup-earlier-diagnosis", "a"), {}, COLON),
           tumour(_t("dedup-earlier-diagnosis", "b"), {"2.5": "20250201"}, COLON)],
          {"Initial Population": [_t("dedup-earlier-diagnosis", "b")]}),
    multi("dedup-same-day-more-severe", "同日診斷：留病理期別較嚴重者（3B > 2A）",
          [tumour(_t("dedup-same-day-more-severe", "a"), {"3.13": "2A"}, COLON),
           tumour(_t("dedup-same-day-more-severe", "b"), {"3.13": "3B"}, COLON)],
          {"Initial Population": [_t("dedup-same-day-more-severe", "b")]}),
    multi("dedup-same-day-clinical-fallback", "同日診斷、a 病理期別 999：改用臨床 3C，勝過 b 的病理 2A",
          [tumour(_t("dedup-same-day-clinical-fallback", "a"), {"3.13": "999", "3.7": "3C"}, COLON),
           tumour(_t("dedup-same-day-clinical-fallback", "b"), {"3.13": "2A"}, COLON)],
          {"Initial Population": [_t("dedup-same-day-clinical-fallback", "a")]}),
    multi("dedup-full-tie", "同日、同期別：依腫瘤 id 取較小者（本 IG 決定）",
          [tumour(_t("dedup-full-tie", "b"), {}, COLON), tumour(_t("dedup-full-tie", "a"), {}, COLON)],
          {"Initial Population": [_t("dedup-full-tie", "a")]}),
    multi("dedup-kept-record-excluded", "較早的代表個案為 class 0：被排除後不以另一筆遞補",
          [tumour(_t("dedup-kept-record-excluded", "a"), {"2.5": "20250201", "2.3": "0"}, COLON),
           tumour(_t("dedup-kept-record-excluded", "b"), {}, COLON)],
          {"Initial Population": []}),
    multi("dedup-missing-hospital-key", "缺 1.1 申報醫院代碼：無法判定重複，排除",
          [tumour(_t("dedup-missing-hospital-key", "tumour"), {"1.1": None}, COLON)],
          {"Initial Population": []}),
    multi("dedup-missing-national-id", "病人無身分證號：無法判定重複，排除",
          [tumour(_t("dedup-missing-national-id", "tumour"), {}, COLON)],
          {"Initial Population": []}, national_id=None),
    multi("not-colorectal-anus", "肛門 C21.0 不屬大腸癌癌別",
          [tumour(_t("not-colorectal-anus", "tumour"), {"2.6": "C210"}, COLON)],
          {"Initial Population": []}),
    multi("died-tx-status-0", "治療狀態分類 0（未於申報醫院接受任何治療即死亡）",
          [tumour(_t("died-tx-status-0", "tumour"), {"2.3.2": "0"}, COLON)],
          {"Initial Population": []}),
    multi("died-no-first-course", "死亡且首次療程 00000000",
          [tumour(_t("died-no-first-course", "tumour"), {"5.4": "true", "4.1": "00000000"}, COLON)],
          {"Initial Population": []}),
    multi("died-no-first-course-watchful", "死亡、首次療程 00000000，但治療狀態分類 4（不予治療／密切觀察）：保留",
          [tumour(_t("died-no-first-course-watchful", "tumour"), {"5.4": "true", "4.1": "00000000", "2.3.2": "4"}, COLON)],
          {"Initial Population": [_t("died-no-first-course-watchful", "tumour")]}),
    multi("died-before-first-course-date", "死亡日期早於首次療程開始日期",
          [tumour(_t("died-before-first-course-date", "tumour"), {"5.4": "true", "5.3": "20250315"}, COLON)],
          {"Initial Population": []}),
    multi("died-on-first-course-date", "治療開始當日死亡：視為已治療，保留",
          [tumour(_t("died-on-first-course-date", "tumour"), {"5.4": "true", "5.3": "20250320"}, COLON)],
          {"Initial Population": [_t("died-on-first-course-date", "tumour")]}),
    multi("alive-early-last-contact", "存活：5.3 是最後聯絡日期，不是死亡日期，保留",
          [tumour(_t("alive-early-last-contact", "tumour"), {"5.4": "false", "5.3": "20250315"}, COLON)],
          {"Initial Population": [_t("alive-early-last-contact", "tumour")]}),
    multi("multi-primary-colon-rectum", "同院同步結腸癌與直腸癌：同一癌別，註1 只留較早診斷的直腸癌",
          [tumour(_t("multi-primary-colon-rectum", "colon"), {}, COLON),
           tumour(_t("multi-primary-colon-rectum", "rectum"), {"4.1": "20250222"}, RECTUM)],
          {"Initial Population": [_t("multi-primary-colon-rectum", "rectum")],
           "Denominator 2": [], "Numerator 2": [],
           "Denominator 3": [_t("multi-primary-colon-rectum", "rectum")],
           "Numerator 3": []}),
    multi("multi-primary-two-hospitals", "結腸癌與直腸癌由不同醫院申報：不是重複個案，兩顆腫瘤各自計算",
          [tumour(_t("multi-primary-two-hospitals", "colon"), {}, COLON),
           tumour(_t("multi-primary-two-hospitals", "rectum"), {"1.1": "0501110514"}, RECTUM)],
          {"Initial Population": [_t("multi-primary-two-hospitals", "colon"), _t("multi-primary-two-hospitals", "rectum")],
           "Denominator 2": [_t("multi-primary-two-hospitals", "colon")],
           "Numerator 2": [_t("multi-primary-two-hospitals", "colon")],
           "Denominator 3": [_t("multi-primary-two-hospitals", "rectum")],
           "Numerator 3": [_t("multi-primary-two-hospitals", "rectum")]}),
    multi("amended-raises-nodes", "2.14 先 final 11 顆，後 amended 為 15 顆：取最新",
          [tumour(_t("amended-raises-nodes", "tumour"), {"2.14": [
              {"value": "15", "issued": "2025-05-01T09:00:00+08:00", "status": "amended"},
              {"value": "11", "issued": "2025-04-01T09:00:00+08:00", "status": "final"}]}, COLON)],
          {"Denominator 2": [_t("amended-raises-nodes", "tumour")], "Numerator 2": [_t("amended-raises-nodes", "tumour")]}),
    multi("amended-lowers-nodes", "2.14 先 final 15 顆，後 corrected 為 11 顆：取最新",
          [tumour(_t("amended-lowers-nodes", "tumour"), {"2.14": [
              {"value": "15", "issued": "2025-04-01T09:00:00+08:00", "status": "final"},
              {"value": "11", "issued": "2025-05-01T09:00:00+08:00", "status": "corrected"}]}, COLON)],
          {"Denominator 2": [_t("amended-lowers-nodes", "tumour")], "Numerator 2": []}),
    multi("entered-in-error-ignored", "較晚的 entered-in-error 申報值不採用",
          [tumour(_t("entered-in-error-ignored", "tumour"), {"2.14": [
              {"value": "15", "issued": "2025-04-01T09:00:00+08:00", "status": "final"},
              {"value": "11", "issued": "2025-05-01T09:00:00+08:00", "status": "entered-in-error"}]}, COLON)],
          {"Numerator 2": [_t("entered-in-error-ignored", "tumour")]}),
    multi("same-issued-tie-break", "兩筆 issued 相同：依 Observation id 取最後一筆（v01）",
          [tumour(_t("same-issued-tie-break", "tumour"), {"2.14": [
              {"value": "11", "issued": "2025-04-01T09:00:00+08:00", "status": "final"},
              {"value": "15", "issued": "2025-04-01T09:00:00+08:00", "status": "amended"}]}, COLON)],
          {"Numerator 2": [_t("same-issued-tie-break", "tumour")]}),
    multi("qi01-facts-belong-to-one-tumour", "兩顆惡性息肉，只有一顆有高風險條件與切除：只算那一顆",
          [tumour(_t("qi01-facts-belong-to-one-tumour", "a"), {}, POLYP_REGISTRY, POLYP),
           tumour(_t("qi01-facts-belong-to-one-tumour", "b"), {}, POLYP_REGISTRY,
                  {**POLYP, "features": {}, "resections": []})],
          {"Initial Population": [_t("qi01-facts-belong-to-one-tumour", "a")],
           "Denominator 1": [_t("qi01-facts-belong-to-one-tumour", "a")],
           "Numerator 1": [_t("qi01-facts-belong-to-one-tumour", "a")]}),
    multi("qi01-facts-of-duplicate-ignored", "兩顆惡性息肉由不同醫院申報：條件與切除只連到 b，只算 b",
          [tumour(_t("qi01-facts-of-duplicate-ignored", "a"), {}, POLYP_REGISTRY,
                  {**POLYP, "features": {}, "resections": []}),
           tumour(_t("qi01-facts-of-duplicate-ignored", "b"), {"1.1": "0501110514"}, POLYP_REGISTRY, POLYP)],
          {"Initial Population": [_t("qi01-facts-of-duplicate-ignored", "a"), _t("qi01-facts-of-duplicate-ignored", "b")],
           "Denominator 1": [_t("qi01-facts-of-duplicate-ignored", "b")],
           "Numerator 1": [_t("qi01-facts-of-duplicate-ignored", "b")]}),
    multi("qi01-report-not-linked", "病理報告存在但未以 evidence 連到腫瘤：不屬分母",
          [tumour(_t("qi01-report-not-linked", "tumour"), {}, POLYP_REGISTRY, {**POLYP, "report_linked": False})],
          {"Denominator 1": []}),
    multi("qi01-resection-of-other-tumour", "切除的 reasonReference 指向另一顆腫瘤：不算",
          [tumour(_t("qi01-resection-of-other-tumour", "a"), {}, POLYP_REGISTRY, {**POLYP, "resections": []}),
           tumour(_t("qi01-resection-of-other-tumour", "b"), {}, COLON,
                  {"malignant_polyp": None, "features": {}, "resections": [{"date": "2025-04-01", "status": "completed"}]})],
          {"Denominator 1": [_t("qi01-resection-of-other-tumour", "a")], "Numerator 1": []}),
]

LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"
# Criterion A: local code + valueBoolean. B-D: LOINC question + (met, not met) answer.
PATHOLOGY_FINDINGS = {
    "B": ((LOINC, "85290-5"), (LOINC, "LA27251-0"), (LOINC, "LA27250-2")),
    "C": ((LOINC, "59544-7"), (LOINC, "LA13328-2"), (LOINC, "LA13327-4")),
    "D": ((LOINC, "33732-9"), (SNOMED, "1155704001"), (SNOMED, "1155703007")),
}


ICDO3 = "http://terminology.hl7.org/CodeSystem/icd-o-3"
MORPHOLOGY_EXT = f"{CANON}/StructureDefinition/crc-histology-morphology-behavior"


# Synthetic ICD-10-CM diagnosis code consistent with the registry primary site.
def icd10cm_for_site(icdo3_site):
    if icdo3_site.startswith("C18."):
        return icdo3_site
    return {"C19.9": "C19", "C20.9": "C20"}.get(icdo3_site, "C18.9")


def obs_category(code):
    return [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": code}]}]


def ref(kind, rid):
    return {"reference": f"{kind}/{rid}"}


def tumour_resources(pid, subject, t, report_ids):
    tid, fields, polyp = t["id"], t["fields"], t["polyp"]
    current = {num: max((v for v in vs if v["status"] in ("final", "amended", "corrected")),
                        key=lambda v: (v["issued"], v["id"]), default=None)
               for num, vs in fields.items()}
    site = icdo3.topography(current["2.6"]["value"])
    coding = [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": icd10cm_for_site(site)}]
    condition = {
        "resourceType": "Condition", "id": tid, "subject": subject,
        "clinicalStatus": CLINICAL_ACTIVE, "category": PROBLEM_LIST,
        "code": {"coding": coding},
        "bodySite": [{"coding": [{"system": ICDO3, "code": site}]}],
        "extension": [{"url": MORPHOLOGY_EXT, "valueCodeableConcept": {
            "coding": [{"system": ICDO3, "code": icdo3.morphology(current["2.8"]["value"], current["2.9"]["value"])}]}}],
    }
    out = [condition]
    for number, versions in fields.items():
        for v in versions:
            out.append({
                "resourceType": "Observation", "id": v["id"], "meta": {"profile": [TCR_PROFILE]},
                "status": v["status"], "issued": v["issued"],
                "code": {"coding": [{"system": FIELD_CS, "code": number}]},
                "subject": subject, "focus": [ref("Condition", tid)], "valueString": v["value"],
            })
    if not polyp:
        return out
    if polyp.get("malignant_polyp"):
        coding.insert(0, {"system": CONCEPT_CS, "code": "malignant-polyp-t1"})
        condition["verificationStatus"] = {"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": polyp["malignant_polyp"]}]}
    if polyp.get("report_issued"):
        report_id = f"{tid}-report"
        out.append({
            "resourceType": "DiagnosticReport", "id": report_id, "status": "final", "subject": subject,
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "SP"}]}],
            "code": {"coding": [{"system": LOINC, "code": "11529-5"}]},
            "issued": f"{polyp['report_issued']}T10:00:00+08:00",
        })
        if polyp.get("report_linked", True):
            condition["evidence"] = [{"detail": [ref("DiagnosticReport", report_id)]}]
        colonoscopy_date = (date.fromisoformat(polyp["report_issued"]) - timedelta(days=4)).isoformat()
    for letter, present in polyp.get("features", {}).items():
        finding = {
            "resourceType": "Observation", "id": f"{tid}-feature-{letter.lower()}", "status": "final",
            "subject": subject, "focus": [ref("Condition", tid)],
        }
        if letter == "A":  # colonoscopy report: a procedure result, local code + boolean
            finding.update(category=obs_category("procedure"), effectiveDateTime=colonoscopy_date,
                           code={"coding": [{"system": CONCEPT_CS, "code": "criterion-a-polyp-incompletely-excised"}]},
                           valueBoolean=present)
        else:  # pathology report: a lab result, LOINC question + coded answer
            question, met, not_met = PATHOLOGY_FINDINGS[letter]
            answer = met if present else not_met
            finding.update(category=obs_category("laboratory"), effectiveDateTime=polyp["report_issued"],
                           code={"coding": [{"system": question[0], "code": question[1]}]},
                           valueCodeableConcept={"coding": [{"system": answer[0], "code": answer[1]}]})
        out.append(finding)
    for index, resection in enumerate(polyp.get("resections", [])):
        out.append({
            "resourceType": "Procedure", "id": f"{tid}-resection-{index}", "status": resection["status"],
            "code": {"coding": [{"system": CONCEPT_CS, "code": "curative-resection"}]},
            "subject": subject, "reasonReference": [ref("Condition", tid)],
            "performedDateTime": f"{resection['date']}T09:00:00+08:00",
        })
    return out


def to_bundle(item, index):
    pid = item["id"]
    subject = ref("Patient", pid)
    patient = {"resourceType": "Patient", "id": pid, "gender": "male", "birthDate": "1960-01-01"}
    if item.get("national_id"):
        patient["identifier"] = [{"type": ID_CARD_TYPE, "system": "http://www.moi.gov.tw", "value": f"Z{index:09d}"}]
    else:
        # Not a valid TW Core Patient: deliberately tests the missing duplicate key.
        patient["identifier"] = [{"system": "urn:example:local-mrn", "value": f"MRN{index:06d}"}]
    entries = [patient]
    for t in item["tumours"]:
        entries += tumour_resources(pid, subject, t, None)
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
    flat = {"format": "tumour-level-v2", "measurement_period": ["2025-01-01", "2025-12-31"], "cases": CASES}
    (fixtures / "synthetic-cases.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runner = [{"id": c["id"], "expected": c["expected"], "bundle": to_bundle(c, i + 1)} for i, c in enumerate(CASES)]
    (fixtures / "cql/cases.json").write_text(json.dumps(runner, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    vs = value_sets()
    if not vs:
        raise SystemExit("no ValueSets found; run SUSHI first")
    (fixtures / "cql/value-sets.json").write_text(json.dumps(vs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(CASES)} cases, {len(vs)} value sets")


if __name__ == "__main__":
    main()
