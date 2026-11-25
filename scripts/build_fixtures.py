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
from datetime import date, datetime, timedelta
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


from reference.crc_indicators import POPULATIONS  # noqa: E402  (single source)
DEFAULT_ISSUED = "2025-04-30T17:00:00+08:00"


def tumour(tumour_id, fields, base=None, polyp=None, **options):
    """One primary tumour. A field value is a raw string (one final version) or a
    list of {"value", "issued", "status"} versions ("issued": None omits it).
    options: verification (Condition.verificationStatus), reference ("relative",
    "versioned", "absolute"), extra_focus (a second focus on every registry item),
    foreign_coding ({field: other-system code} added to that field's items),
    foreign_subject (registry items name another patient as subject)."""
    merged = dict(base or {})
    for key, value in fields.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return {"id": tumour_id, "fields": merged, "polyp": polyp, **options,
            # Registry items the CQL attributes to no tumour of this patient.
            "multi_focus": bool(options.get("extra_focus") or options.get("foreign_subject"))}


def case(case_id, description, fields, expected, base=None, polyp=None):
    """A single-tumour case. Boolean expectations mean "this case's tumour is /
    is not in the population"; they are turned into tumour-id lists. Only
    population expressions are asserted: the library's helpers are functions
    of a tumour and are exercised through the populations."""
    tid = f"{case_id}-tumour"
    lists = {k: ([tid] if v else []) for k, v in expected.items() if k in POPULATIONS}
    return multi(case_id, description, [tumour(tid, fields, base, polyp)], lists)


def multi(case_id, description, tumours, expected, national_id="present", outside_excluded=None, outside_ignored=None):
    unknown = set(expected) - set(POPULATIONS)
    if unknown:
        raise SystemExit(f"{case_id}: not a population expression: {unknown}")
    for t in tumours:
        versions = {}
        for number, value in t["fields"].items():
            items = value if isinstance(value, list) else [{"value": value}]
            versions[number] = [
                {"id": f"{t['id']}-f{number.replace('.', '-')}-v{k:02d}", "value": v["value"],
                 "issued": v["issued"] if "issued" in v else DEFAULT_ISSUED,
                 "status": v.get("status", "final")}
                for k, v in enumerate(items)
            ]
        t["fields"] = versions
    return {"id": case_id, "description": description,
            "national_id": (case_id if national_id == "present" else national_id), "tumours": tumours,
            "outside_excluded": outside_excluded or {},
            # (indicator, tumour id, status) declarations the CQL must ignore;
            # not passed to the Python reference, which never sees them.
            "outside_ignored": outside_ignored or [],
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
    # Time zone (A-05): dates are read in Taiwan time. Each case would come out
    # the other way if the CQL took the date of the instant as written.
    case("qi01-report-utc-instant", "病理報告 issued 以 UTC 記載（台灣 3/1 00:30）：第 84 天切除仍計入", {},
         {"Denominator 1": True, "Numerator 1": True}, POLYP_REGISTRY,
         {**POLYP, "report_issued_at": "2025-02-28T16:30:00Z"}),
    case("qi01-resection-utc-day-85", "切除時間以 UTC 記載（台灣 5/25 00:30）：第 85 天，不計入", {},
         {"Denominator 1": True, "Numerator 1": False}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"at": "2025-05-24T16:30:00Z", "status": "completed"}]}),
    case("qi01-resection-other-offset", "切除時間 +09:00（台灣 5/24 23:30）：第 84 天，計入", {},
         {"Denominator 1": True, "Numerator 1": True}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"at": "2025-05-25T00:30:00+09:00", "status": "completed"}]}),
    case("qi01-resection-date-only", "切除時間只有日期 2025-05-24：第 84 天，計入", {},
         {"Denominator 1": True, "Numerator 1": True}, POLYP_REGISTRY,
         {**POLYP, "resections": [{"at": "2025-05-24", "status": "completed"}]}),
    case("qi01-no-feature", "A–D 皆記載為不成立：不屬分母", {}, {"Has High Risk Feature": False, "Denominator 1": False},
         POLYP_REGISTRY, {**POLYP, "features": {"A": False, "B": False, "C": False, "D": False}}),
    case("qi01-feature-a-only", "只有條件 A（大腸鏡報告）", {}, {"Denominator 1": True}, POLYP_REGISTRY,
         {**POLYP, "features": {"A": True}}),
    case("qi01-unconfirmed-polyp", "惡性息肉未確認", {}, {"Has Malignant Polyp": False, "Denominator 1": False},
         POLYP_REGISTRY, {**POLYP, "malignant_polyp": "provisional"}),
    case("qi01-feature-b-translation", "條件 B 的 LOINC 答案另附 SNOMED CT 同義代碼：仍成立", {},
         {"Denominator 1": True}, POLYP_REGISTRY, {**POLYP, "features": {"B": "met-with-translation"}}),
    case("qi01-feature-c-contradictory", "條件 C 同時帶「有」與「無」淋巴血管侵犯：不成立（矛盾資料）", {},
         {"Has High Risk Feature": False, "Denominator 1": False}, POLYP_REGISTRY,
         {**POLYP, "features": {"C": "contradictory"}}),
    case("qi01-no-polyp-facts", "沒有惡性息肉臨床事實", {}, {"Denominator 1": False, "Numerator 1": False}, COLON),
]


# ---- tumour as the unit, current registry value, linked indicator-1 facts ------
def _t(case_id, suffix):
    return f"{case_id}-{suffix}"


CASES += [
    # ---- raw value normalisation: trim ASCII blanks only, ASCII digits only ----
    multi("ws-hospital-internal", "1.1 內含空白：與另一筆不是同一醫院代碼，不視為重複",
          [tumour(_t("ws-hospital-internal", "a"), {"1.1": "0401 180014"}, COLON),
           tumour(_t("ws-hospital-internal", "b"), {"2.5": "20250201"}, COLON)],
          {"Initial Population": [_t("ws-hospital-internal", "a"), _t("ws-hospital-internal", "b")]}),
    case("ws-site-internal", "2.6「C 18.7」內含空白：格式錯誤，不屬大腸癌", {"2.6": "C 18.7"}, {"Initial Population": False}, COLON),
    case("ws-site-malformed", "2.6「C1.87」：格式錯誤", {"2.6": "C1.87"}, {"Initial Population": False}, COLON),
    case("ws-site-trailing", "2.6「C18.7 」：去除尾端空白後有效", {"2.6": "C18.7 "},
         {"Initial Population": True, "Denominator 2": True}, COLON),
    case("ws-dx-leading", "2.5 前置空白：去除後有效", {"2.5": " 20250305"}, {"Initial Population": True}, COLON),
    case("ws-class-trailing", "2.3「1 」：去除後為 1", {"2.3": "1 "}, {"Initial Population": True}, COLON),
    case("ws-tx-status-0", "2.3.2「 0」：治療前死亡", {"2.3.2": " 0"}, {"Initial Population": False}, COLON),
    case("ws-first-course-none", "死亡且 4.1「00000000 」", {"5.4": "0", "4.1": "00000000 "}, {"Initial Population": False}, COLON),
    case("ws-cross-hospital", "2.3.1「2 」：跨院治療", {"2.3": "2", "2.3.1": "2 ", "2.3.2": "3"}, {"Initial Population": False}, COLON),
    case("ws-vital-internal", "5.4「0 0」內含空白：不是死亡代碼", {"5.4": "0 0", "4.1": "00000000"}, {"Initial Population": True}, COLON),
    case("vital-trailing-blank", "5.4「0 」：去除尾端空白後為 0（死亡）", {"5.4": "0 ", "4.1": "00000000"}, {"Initial Population": False}, COLON),
    case("vital-alive", "5.4＝1 存活、4.1＝00000000：不是治療前死亡", {"5.4": "1", "4.1": "00000000"}, {"Initial Population": True}, COLON),
    case("vital-boolean-true", "5.4「true」不是長表代碼（0＝死亡）：不視為死亡", {"5.4": "true", "4.1": "00000000"}, {"Initial Population": True}, COLON),
    multi("ws-stage-internal", "同日：a 病理期別「3 C」格式錯誤且臨床 999，無法排序；留 b（2A）",
          [tumour(_t("ws-stage-internal", "a"), {"3.13": "3 C", "3.7": "999"}, COLON),
           tumour(_t("ws-stage-internal", "b"), {"3.13": "2A"}, COLON)],
          {"Initial Population": [_t("ws-stage-internal", "b")]}),
    case("fullwidth-nodes", "2.14 全形「１５」：不是 ASCII 數字", {"2.14": "１５"},
         {"Denominator 2": True, "Numerator 2": False}, COLON),
    case("stage-pathological-missing", "3.13 缺漏：不屬指標 2 分母（不得使引擎出錯）", {"3.13": None},
         {"Initial Population": True, "Denominator 2": False, "Numerator 2": False}, COLON),
    case("stage-pathological-blank", "3.13 只有空白與換行：視為缺漏", {"3.13": " \t\n"},
         {"Initial Population": True, "Denominator 2": False}, COLON),
    case("stage-clinical-missing", "3.7 缺漏：不屬指標 3 分母", {"3.7": None},
         {"Initial Population": True, "Denominator 3": False, "Numerator 3": False}, RECTUM),
    case("stage-clinical-missing-colon", "結腸個案 3.7 缺漏：指標 2 照常計算", {"3.7": None},
         {"Denominator 2": True, "Numerator 2": True}, COLON),
    case("ws-site-newline", "2.6「C187\\n」尾端換行：不是可去除的空白，格式錯誤", {"2.6": "C187\n"},
         {"Initial Population": False}, COLON),
    case("ws-dx-newline", "2.5「20250305\\n」尾端換行：格式錯誤", {"2.5": "20250305\n"}, {"Initial Population": False}, COLON),
    case("ws-class-newline", "2.3「1\\n」尾端換行：不是 class 1", {"2.3": "1\n"}, {"Initial Population": False}, COLON),
    case("ws-first-course-newline", "4.1「20250120\\n」尾端換行：日期無效，不屬分子 3", {"4.1": "20250120\n"},
         {"Denominator 3": True, "Numerator 3": False}, RECTUM),
    # ---- what counts as a tumour, references, field identity ---------------------
    multi("tumour-entered-in-error", "Condition 為 entered-in-error：不是個案",
          [tumour(_t("tumour-entered-in-error", "tumour"), {}, COLON, verification="entered-in-error")],
          {"Initial Population": []}),
    multi("registry-item-two-focus", "癌登欄位同時 focus 腫瘤與糖尿病：不歸屬任何一方",
          [tumour(_t("registry-item-two-focus", "tumour"), {}, COLON, extra_focus=_t("registry-item-two-focus", "diabetes"))],
          {"Initial Population": []}),
    multi("reference-versioned", "focus 帶版本（Condition/x/_history/1）",
          [tumour(_t("reference-versioned", "tumour"), {}, COLON, reference="versioned")],
          {"Initial Population": [_t("reference-versioned", "tumour")], "Numerator 2": [_t("reference-versioned", "tumour")]}),
    multi("reference-absolute", "focus 為絕對 URL",
          [tumour(_t("reference-absolute", "tumour"), {}, COLON, reference="absolute")],
          {"Initial Population": [_t("reference-absolute", "tumour")]}),
    multi("issued-missing-only", "2.5 唯一一筆沒有 issued：仍採用",
          [tumour(_t("issued-missing-only", "tumour"), {"2.5": [{"value": "20250305", "issued": None}]}, COLON)],
          {"Initial Population": [_t("issued-missing-only", "tumour")]}),
    multi("issued-missing-loses", "2.14 一筆有 issued（15）、一筆沒有（11）：有 issued 者勝",
          [tumour(_t("issued-missing-loses", "tumour"), {"2.14": [
              {"value": "15", "issued": "2025-04-01T09:00:00+08:00"}, {"value": "11", "issued": None}]}, COLON)],
          {"Numerator 2": [_t("issued-missing-loses", "tumour")]}),
    multi("foreign-coding", "2.6 欄位另帶其他系統的代碼「2.5」：不得被當成 2.5",
          [tumour(_t("foreign-coding", "tumour"), {"2.6": [{"value": "C187", "issued": "2025-05-30T09:00:00+08:00"}]}, COLON,
                  foreign_coding={"2.6": "2.5"})],
          {"Initial Population": [_t("foreign-coding", "tumour")]}),
    multi("national-id-blank", "身分證號只有空白：視為缺少，但不排除（CQL 以 Patient 判定同一人）",
          [tumour(_t("national-id-blank", "tumour"), {}, COLON)], {"Initial Population": [_t("national-id-blank", "tumour")]}, national_id=" "),
    multi("national-id-unknown-code", "身分證號 9999999999（長表：個案無身分證統一編號）：不排除",
          [tumour(_t("national-id-unknown-code", "tumour"), {}, COLON)], {"Initial Population": [_t("national-id-unknown-code", "tumour")]}, national_id="9999999999"),
    multi("national-id-ideographic-space", "身分證號只有全形空白 U+3000：視為缺少，不排除",
          [tumour(_t("national-id-ideographic-space", "tumour"), {}, COLON)], {"Initial Population": [_t("national-id-ideographic-space", "tumour")]}, national_id="\u3000"),
    multi("national-id-newline", "身分證號只有換行：視為缺少，不排除",
          [tumour(_t("national-id-newline", "tumour"), {}, COLON)], {"Initial Population": [_t("national-id-newline", "tumour")]}, national_id="\n"),
    multi("national-id-nbsp", "身分證號只有不換行空白 U+00A0：不屬空白字元，視為有值（本 IG 決定）",
          [tumour(_t("national-id-nbsp", "tumour"), {}, COLON)],
          {"Initial Population": [_t("national-id-nbsp", "tumour")]}, national_id="\u00a0"),
    multi("hospital-id-ideographic-space", "1.1 只有全形空白：視為缺少，排除",
          [tumour(_t("hospital-id-ideographic-space", "tumour"), {"1.1": "\u3000"}, COLON)], {"Initial Population": []}),
    # ---- 第五點 outside-hospital data (hospital-supplied, per indicator) ----------
    multi("outside-data-excluded-qi02", "醫院依第五點將此腫瘤自指標 2 排除：列為指標 2 的 denominator exclusion",
          [tumour(_t("outside-data-excluded-qi02", "tumour"), {}, COLON)],
          {"Initial Population": [_t("outside-data-excluded-qi02", "tumour")], "Denominator 2": [_t("outside-data-excluded-qi02", "tumour")], "Denominator 2 Exclusion": [_t("outside-data-excluded-qi02", "tumour")], "Outside Data Excluded 2": [_t("outside-data-excluded-qi02", "tumour")]},
          outside_excluded={"2": [_t("outside-data-excluded-qi02", "tumour")]}),
    multi("outside-data-excluded-qi01", "醫院依第五點將此腫瘤自指標 1 排除",
          [tumour(_t("outside-data-excluded-qi01", "tumour"), {}, POLYP_REGISTRY, POLYP)],
          {"Initial Population": [_t("outside-data-excluded-qi01", "tumour")], "Denominator 1": [_t("outside-data-excluded-qi01", "tumour")], "Denominator 1 Exclusion": [_t("outside-data-excluded-qi01", "tumour")], "Outside Data Excluded 1": [_t("outside-data-excluded-qi01", "tumour")]},
          outside_excluded={"1": [_t("outside-data-excluded-qi01", "tumour")]}),
    multi("outside-data-excluded-qi03", "醫院依第五點將此腫瘤自指標 3 排除；指標 2 不受影響",
          [tumour(_t("outside-data-excluded-qi03", "tumour"), {}, RECTUM)],
          {"Initial Population": [_t("outside-data-excluded-qi03", "tumour")], "Denominator 3": [_t("outside-data-excluded-qi03", "tumour")], "Denominator 3 Exclusion": [_t("outside-data-excluded-qi03", "tumour")], "Outside Data Excluded 3": [_t("outside-data-excluded-qi03", "tumour")]},
          outside_excluded={"3": [_t("outside-data-excluded-qi03", "tumour")]}),
    multi("outside-data-entered-in-error", "第五點宣告為 entered-in-error：不排除",
          [tumour(_t("outside-data-entered-in-error", "tumour"), {}, COLON)],
          {"Denominator 2": [_t("outside-data-entered-in-error", "tumour")]},
          outside_ignored=[(2, _t("outside-data-entered-in-error", "tumour"), "entered-in-error")]),
    multi("outside-data-other-tumour", "第五點宣告指向同一病人的另一顆腫瘤（不同院）：本腫瘤不受影響",
          [tumour(_t("outside-data-other-tumour", "a"), {}, COLON),
           tumour(_t("outside-data-other-tumour", "b"), {"1.1": "0501110514"}, COLON)],
          {"Denominator 2": [_t("outside-data-other-tumour", "a"), _t("outside-data-other-tumour", "b")],
           "Outside Data Excluded 2": [_t("outside-data-other-tumour", "b")]},
          outside_excluded={"2": [_t("outside-data-other-tumour", "b")]}),
    multi("outside-data-other-subject", "第五點宣告的 subject 是另一位病人：不採用",
          [tumour(_t("outside-data-other-subject", "tumour"), {}, COLON)],
          {"Denominator 2": [_t("outside-data-other-subject", "tumour")]},
          outside_ignored=[(2, _t("outside-data-other-subject", "tumour"), "final",
                            {"subject": {"reference": "Patient/someone-else"}})]),
    multi("outside-data-no-value", "第五點宣告沒有理由（value）：不採用",
          [tumour(_t("outside-data-no-value", "tumour"), {}, COLON)],
          {"Denominator 2": [_t("outside-data-no-value", "tumour")]},
          outside_ignored=[(2, _t("outside-data-no-value", "tumour"), "final", {"valueCodeableConcept": None})]),
    multi("registry-items-other-subject", "癌登欄位的 subject 是另一位病人：不歸屬此病人的腫瘤",
          [tumour(_t("registry-items-other-subject", "tumour"), {}, COLON, foreign_subject=True)],
          {"Initial Population": []}),
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
    multi("dedup-missing-national-id", "病人無身分證號：同一 Patient 內仍可去重，不排除",
          [tumour(_t("dedup-missing-national-id", "tumour"), {}, COLON)],
          {"Initial Population": [_t("dedup-missing-national-id", "tumour")]}, national_id=None),
    multi("not-colorectal-anus", "肛門 C21.0 不屬大腸癌癌別",
          [tumour(_t("not-colorectal-anus", "tumour"), {"2.6": "C210"}, COLON)],
          {"Initial Population": []}),
    multi("died-tx-status-0", "治療狀態分類 0（未於申報醫院接受任何治療即死亡）",
          [tumour(_t("died-tx-status-0", "tumour"), {"2.3.2": "0"}, COLON)],
          {"Initial Population": []}),
    multi("died-no-first-course", "死亡且首次療程 00000000",
          [tumour(_t("died-no-first-course", "tumour"), {"5.4": "0", "4.1": "00000000"}, COLON)],
          {"Initial Population": []}),
    multi("died-no-first-course-watchful", "死亡、首次療程 00000000，但治療狀態分類 4（不予治療／密切觀察）：保留",
          [tumour(_t("died-no-first-course-watchful", "tumour"), {"5.4": "0", "4.1": "00000000", "2.3.2": "4"}, COLON)],
          {"Initial Population": [_t("died-no-first-course-watchful", "tumour")]}),
    multi("died-before-first-course-date", "死亡日期早於首次療程開始日期",
          [tumour(_t("died-before-first-course-date", "tumour"), {"5.4": "0", "5.3": "20250315"}, COLON)],
          {"Initial Population": []}),
    multi("died-on-first-course-date", "治療開始當日死亡：視為已治療，保留",
          [tumour(_t("died-on-first-course-date", "tumour"), {"5.4": "0", "5.3": "20250320"}, COLON)],
          {"Initial Population": [_t("died-on-first-course-date", "tumour")]}),
    multi("alive-early-last-contact", "存活：5.3 是最後聯絡日期，不是死亡日期，保留",
          [tumour(_t("alive-early-last-contact", "tumour"), {"5.4": "1", "5.3": "20250315"}, COLON)],
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
# Equivalent codings from outside the question's answer list (translations).
PATHOLOGY_TRANSLATIONS = {
    "B": (SNOMED, "370109009"),   # Surgical margin involved by tumor
    "C": (SNOMED, "395717001"),   # Lymphatic (small vessel) invasion by tumor present
    "D": (SNOMED, "369718005"),   # G3: Poorly differentiated (5-49 percent gland forming)
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


def version_rank(v):
    """Latest issued instant wins (compared as instants, not strings); a version
    without issued ranks below every dated one; ties fall back to the id."""
    issued = datetime.fromisoformat(v["issued"].replace("Z", "+00:00")).timestamp() if v["issued"] else float("-inf")
    return (issued, v["id"])


def tumour_resources(pid, subject, t, report_ids):
    tid, fields, polyp = t["id"], t["fields"], t["polyp"]
    current = {num: max((v for v in vs if v["status"] in ("final", "amended", "corrected")),
                        key=version_rank, default=None)
               for num, vs in fields.items()}
    try:
        site = icdo3.topography(current["2.6"]["value"])
    except (ValueError, TypeError, KeyError):  # deliberately malformed registry site
        site = "C18.9"
    coding = [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": icd10cm_for_site(site)}]
    condition = {
        "resourceType": "Condition", "id": tid, "subject": subject,
        "clinicalStatus": CLINICAL_ACTIVE, "category": PROBLEM_LIST,
        "code": {"coding": coding},
        "bodySite": [{"coding": [{"system": ICDO3, "code": site}]}],
    }
    try:
        condition["extension"] = [{"url": MORPHOLOGY_EXT, "valueCodeableConcept": {
            "coding": [{"system": ICDO3, "code": icdo3.morphology(current["2.8"]["value"], current["2.9"]["value"])}]}}]
    except (ValueError, TypeError, KeyError):
        pass
    out = [condition]
    style = t.get("reference", "relative")
    tumour_ref = {"relative": ref("Condition", tid),
                  "versioned": {"reference": f"Condition/{tid}/_history/1"},
                  "absolute": {"reference": f"https://hospital.example.org/fhir/Condition/{tid}"}}[style]
    if t.get("verification"):
        condition["verificationStatus"] = {"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": t["verification"]}]}
    if t.get("extra_focus"):
        out.append({"resourceType": "Condition", "id": t["extra_focus"], "subject": subject,
                    "clinicalStatus": CLINICAL_ACTIVE, "category": PROBLEM_LIST,
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "E11.9"}]}})
    for number, versions in fields.items():
        for v in versions:
            item_coding = [{"system": FIELD_CS, "code": number}]
            if number in t.get("foreign_coding", {}):
                item_coding.append({"system": "urn:example:other-field-codes", "code": t["foreign_coding"][number]})
            item = {
                "resourceType": "Observation", "id": v["id"], "meta": {"profile": [TCR_PROFILE]},
                "status": v["status"], "code": {"coding": item_coding},
                "subject": ref("Patient", "someone-else") if t.get("foreign_subject") else subject,
                "focus": [tumour_ref], "valueString": v["value"],
            }
            if v["issued"] is not None:
                item["issued"] = v["issued"]
            if t.get("extra_focus"):
                item["focus"].append(ref("Condition", t["extra_focus"]))
            out.append(item)
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
            "issued": polyp.get("report_issued_at") or f"{polyp['report_issued']}T10:00:00+08:00",
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
            # True / False: one answer coding. "met-with-translation": the met
            # answer plus an equivalent coding from another system (allowed).
            # "contradictory": met and not-met answers together (not met).
            answers = {True: [met], False: [not_met], "contradictory": [met, not_met],
                       "met-with-translation": [met, PATHOLOGY_TRANSLATIONS[letter]]}[present]
            finding.update(category=obs_category("laboratory"), effectiveDateTime=polyp["report_issued"],
                           code={"coding": [{"system": question[0], "code": question[1]}]},
                           valueCodeableConcept={"coding": [{"system": a[0], "code": a[1]} for a in answers]})
        out.append(finding)
    for index, resection in enumerate(polyp.get("resections", [])):
        out.append({
            "resourceType": "Procedure", "id": f"{tid}-resection-{index}", "status": resection["status"],
            "code": {"coding": [{"system": CONCEPT_CS, "code": "curative-resection"}]},
            "subject": subject, "reasonReference": [ref("Condition", tid)],
            "performedDateTime": resection.get("at") or f"{resection['date']}T09:00:00+08:00",
        })
    return out


def to_bundle(item, index):
    pid = item["id"]
    subject = ref("Patient", pid)
    patient = {"resourceType": "Patient", "id": pid, "gender": "male", "birthDate": "1960-01-01"}
    if item.get("national_id") is not None:
        value = f"Z{index:09d}" if item["national_id"] == item["id"] else item["national_id"]
        patient["identifier"] = [{"type": ID_CARD_TYPE, "system": "http://www.moi.gov.tw", "value": value}]
    else:
        # Not a valid TW Core Patient: deliberately tests the missing duplicate key.
        patient["identifier"] = [{"system": "urn:example:local-mrn", "value": f"MRN{index:06d}"}]
    entries = [patient]
    for t in item["tumours"]:
        entries += tumour_resources(pid, subject, t, None)
    # 第五點: one CRCOutsideDataExclusion Observation per tumour and indicator.
    declarations = [(m, tid, "final") for m, ids in item.get("outside_excluded", {}).items() for tid in ids]
    for k, (m, tid, status, *override) in enumerate(declarations + list(item.get("outside_ignored", []))):
        declaration = {
            "resourceType": "Observation", "id": f"{pid}-outside-{k}", "status": status,
            "code": {"coding": [{"system": f"{CANON}/CodeSystem/crc-outside-data", "code": f"excluded-qi0{m}"}]},
            "subject": subject, "focus": [ref("Condition", tid)],
            "valueCodeableConcept": {"coding": [{"system": f"{CANON}/CodeSystem/crc-outside-data",
                                                 "code": "numerator-outside-not-obtained"}]},
            "issued": "2026-01-15T10:00:00+08:00",
        }
        for key, value in (override[0] if override else {}).items():  # None removes the element
            if value is None:
                declaration.pop(key, None)
            else:
                declaration[key] = value
        entries.append(declaration)
    return {"resourceType": "Bundle", "type": "collection",
            "meta": {"tag": [{"system": f"{CANON}/CodeSystem/fixture-tag", "code": "synthetic"}]},
            "entry": [{"resource": r} for r in entries]}


MEASURES = {1: "crc-qi-01", 2: "crc-qi-02", 3: "crc-qi-03"}


def write_measure_reports(results, period):
    """Summary MeasureReports over the whole synthetic population, from the
    Python reference. The JavaScript runner aggregates the CQL results and
    checks they reproduce these counts."""
    from fractions import Fraction
    from reference.crc_indicators import proportion

    out = ["// GENERATED by scripts/build_fixtures.py from the Python reference over",
           "// tests/fixtures/synthetic-cases.json. Do not edit by hand. Synthetic data only.", ""]
    for number, measure_id in MEASURES.items():
        counts = proportion(results, number)
        eligible = counts["denominator"] - counts["denominator-exclusion"]
        score = Fraction(counts["numerator"], eligible) if eligible else None
        out += [
            f"Instance: SyntheticSummaryReport{number:02d}",
            "InstanceOf: MeasureReport",
            "Usage: #example",
            f'Title: "合成摘要報告－大腸癌指標 {number}"',
            f'Description: "以本 IG 全部 {len(results)} 個合成個案計算的 {measure_id} 摘要 MeasureReport，僅示範輸出格式，不代表任何醫院的實際表現。"',
            f'* id = "synthetic-summary-{measure_id}"',
            "* language = #zh-TW",
            "* status = #complete",
            "* type = #summary",
            f'* measure = "{CANON}/Measure/{measure_id}|0.1.0-preview.2"',
            f'* date = "2026-11-25"',
            f'* period.start = "{period[0]}"',
            f'* period.end = "{period[1]}"',
        ]
        populations = [("initial-population", "initial-population"), ("denominator", "denominator"),
                       ("denominator-exclusion", "denominator-exclusion"), ("numerator", "numerator")]
        for k, (code, key) in enumerate(populations):
            out += [f"* group.population[{k}].code = $MeasurePopulation#{code}",
                    f"* group.population[{k}].count = {counts[key]}"]
        if score is not None:
            out.append(f"* group.measureScore.value = {float(score):.4f}")
        out.append("")
    (ROOT / "ig/input/fsh/measure-reports.fsh").write_text("\n".join(out), encoding="utf-8")


def value_sets():
    expansions = {}
    for path in sorted((ROOT / "ig/fsh-generated/resources").glob("ValueSet-*.json")):
        vs = json.loads(path.read_text(encoding="utf-8"))
        codes = [{"system": inc["system"], "code": c["code"]}
                 for inc in vs.get("compose", {}).get("include", []) for c in inc.get("concept", [])]
        if codes:
            expansions[vs["url"]] = {vs.get("version", "0.1.0-preview.2"): codes}
    return expansions


def main():
    fixtures = ROOT / "tests/fixtures"
    (fixtures / "cql").mkdir(parents=True, exist_ok=True)
    flat = {"format": "tumour-level-v2", "measurement_period": ["2025-01-01", "2025-12-31"], "cases": CASES}
    (fixtures / "synthetic-cases.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from datetime import date as _date
    from reference.crc_indicators import evaluate_case
    period = tuple(_date.fromisoformat(d) for d in flat["measurement_period"])
    runner = []
    for i, c in enumerate(CASES):
        reference = evaluate_case(c, period)
        wrong = {k: (v, reference[k]) for k, v in c["expected"].items() if reference[k] != v}
        if wrong:
            raise SystemExit(f"{c['id']}: reference disagrees with the hand-written expectation: {wrong}")
        entry = {"id": c["id"], "expected": reference, "bundle": to_bundle(c, i + 1)}
        runner.append(entry)
    (fixtures / "cql/cases.json").write_text(json.dumps(runner, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_measure_reports([r["expected"] for r in runner], flat["measurement_period"])
    vs = value_sets()
    if not vs:
        raise SystemExit("no ValueSets found; run SUSHI first")
    (fixtures / "cql/value-sets.json").write_text(json.dumps(vs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(CASES)} cases, {len(vs)} value sets")


if __name__ == "__main__":
    main()
