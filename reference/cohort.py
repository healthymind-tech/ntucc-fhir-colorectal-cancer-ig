"""Reference implementation of case assembly (收錄資料說明, 115年癌症診療核心測量指標 p. i-ii).

Input is a list of flat registry records, one per tumour (one primary cancer
registered by one hospital):

    {"patient_id": "A123456789",      # 1.4 身分證統一編號
     "hospital_id": "0401180014",     # 1.1 申報醫院代碼
     "tumour_id": "T1",               # unique per record
     "fields": {"2.5": "20240315", "2.6": "C187", ...}}   # raw long-form strings

`assemble_cohort` applies, in this fixed order, every general inclusion rule
and returns the eligible tumour ids plus one machine-readable reason code for
every excluded tumour. The page ig/input/pagecontent/case-assembly.md is the
normative description; every "IG decision" below is listed there as needing
confirmation by the 國家衛生研究院 research team.

Step  Rule (source)                                   Reason code
----  ----------------------------------------------  -----------------------------
 1    癌別 scope (大腸癌: C18 excl. C18.1, C19, C20)   NOT_COLORECTAL
 2    2.5 must be a real YYYYMMDD date                INVALID_DIAGNOSIS_DATE
 3    第一點 new diagnosis since 2024-01-01           DIAGNOSIS_BEFORE_2024
      + caller's measurement period                   OUTSIDE_MEASUREMENT_PERIOD
 4    註1 key must be complete                        MISSING_DEDUP_KEY
 5    註1 重複個案 (hospital + 癌別 + 身分證號)          DUPLICATE_OF:<kept tumour_id>
 6    第三點 class 1, 2                               CLASS_NOT_1_OR_2
 7    註3 跨院 (2.3=2, 2.3.1=2, 2.3.2=3)              CROSS_HOSPITAL_TREATMENT
 8    第二點 治療前已死亡                              DIED_BEFORE_TREATMENT
 9    第五點 外院資料 (hospital-supplied, per indicator) OUTSIDE_DATA_BOTH
                                                      OUTSIDE_NUMERATOR_NOT_OBTAINED

Steps 1-3 run before de-duplication on purpose: the reporting file HPA asks
for is "new diagnoses in the period", and 註1 picks one representative record
per person-癌別 *within that file*. Steps 6-9 run on the representative only,
so a patient is never counted through a back-up record when the earliest
record fails class / cross-hospital / death rules (IG decision, see page).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping

# ---------------------------------------------------------------------------
# Field numbers (TWCR_LF StructureDefinition element short names)
# ---------------------------------------------------------------------------
CLASS_OF_CASE = "2.3"            # TWCRLF.cancerConfirmation.diagnosis.classOfCase
CLASS_OF_DX_STATUS = "2.3.1"     # ...diagnosis.classOfDiagnosisStatus
CLASS_OF_TX_STATUS = "2.3.2"     # ...diagnosis.classOfTreatmentStatus
DATE_OF_DIAGNOSIS = "2.5"        # ...diagnosis.dateOfInitialDiagnosis
PRIMARY_SITE = "2.6"             # ...primaryCancer.primarySite
CLINICAL_STAGE_GROUP = "3.7"
PATHOLOGIC_STAGE_GROUP = "3.13"
FIRST_COURSE_START = "4.1"       # TWCRLF.firstCourseOfTreatment.firstCourseOfTreatmentDate
LAST_CONTACT_OR_DEATH = "5.3"    # TWCRLF.outcome.dateOfLastContactOrDeath
VITAL_STATUS = "5.4"             # TWCRLF.outcome.vitalStatus

REGISTRY_START = date(2024, 1, 1)  # 第一點: 自 113 年 1 月 1 日起新診斷
COLORECTAL = "大腸癌"

NO_NATIONAL_ID = "9999999999"  # 1.4 身分證統一編號: 個案無身分證統一編號 (手冊 p. 56)
NO_DATE = "00000000"       # 無 (e.g. 4.1: no first course treatment)
UNKNOWN_DATE = "99999999"  # 不詳

# ---------------------------------------------------------------------------
# Vital status (5.4)
# ---------------------------------------------------------------------------
# 長表摘錄手冊 (民國114年版) p. 314: 5.4 生存狀態, 編碼範圍 0-1, 0 = 死亡,
# 1 = 存活. (TWCR_LF 0.1.1 maps the element to Patient.deceasedBoolean, but the
# raw long-form value is what this IG keeps.) Any other value is not dead.
DEFAULT_VITAL_STATUS_CODES: Mapping[str, bool] = {"0": True, "1": False}

# ---------------------------------------------------------------------------
# Outside-hospital data (第五點) — hospital-supplied, per indicator
# ---------------------------------------------------------------------------
IN_HOSPITAL = "IN_HOSPITAL"                                  # nothing outside
BOTH_OUTSIDE = "BOTH_OUTSIDE"                                # 第五點 1
NUMERATOR_OUTSIDE_OBTAINED = "NUMERATOR_OUTSIDE_OBTAINED"    # 第五點 2(2) first half
NUMERATOR_OUTSIDE_NOT_OBTAINED = "NUMERATOR_OUTSIDE_NOT_OBTAINED"  # 第五點 2(2) second half
OUTSIDE_DATA_STATUSES = frozenset(
    {IN_HOSPITAL, BOTH_OUTSIDE, NUMERATOR_OUTSIDE_OBTAINED, NUMERATOR_OUTSIDE_NOT_OBTAINED}
)

# ---------------------------------------------------------------------------
# Reason codes and flags
# ---------------------------------------------------------------------------
NOT_COLORECTAL = "NOT_COLORECTAL"
INVALID_DIAGNOSIS_DATE = "INVALID_DIAGNOSIS_DATE"
DIAGNOSIS_BEFORE_2024 = "DIAGNOSIS_BEFORE_2024"
OUTSIDE_MEASUREMENT_PERIOD = "OUTSIDE_MEASUREMENT_PERIOD"
MISSING_DEDUP_KEY = "MISSING_DEDUP_KEY"
DUPLICATE_OF = "DUPLICATE_OF"  # rendered "DUPLICATE_OF:<tumour_id>"
CLASS_NOT_1_OR_2 = "CLASS_NOT_1_OR_2"
CROSS_HOSPITAL_TREATMENT = "CROSS_HOSPITAL_TREATMENT"
DIED_BEFORE_TREATMENT = "DIED_BEFORE_TREATMENT"
OUTSIDE_DATA_BOTH = "OUTSIDE_DATA_BOTH"
OUTSIDE_NUMERATOR_NOT_OBTAINED = "OUTSIDE_NUMERATOR_NOT_OBTAINED"

# Flags never change eligibility on their own; they mark records where this IG
# had to decide something the official text does not cover.
FLAG_ANUS_EXCLUDED = "ANUS_C21_EXCLUDED_PENDING_CONFIRMATION"
FLAG_APPENDIX_EXCLUDED = "APPENDIX_C181_EXCLUDED"
FLAG_TIE_BROKEN_BY_TUMOUR_ID = "TIE_BROKEN_BY_TUMOUR_ID"
FLAG_TIE_BROKEN_BY_STAGE = "SAME_DAY_TIE_BROKEN_BY_STAGE"
FLAG_STAGE_BASIS_CLINICAL = "STAGE_FROM_CLINICAL_FALLBACK"
FLAG_STAGE_UNRANKABLE = "STAGE_UNRANKABLE"
FLAG_DIED_BASIS_TX_STATUS_0 = "DIED_BASIS_TX_STATUS_0"
FLAG_DIED_BASIS_NO_FIRST_COURSE = "DIED_BASIS_DEAD_AND_NO_FIRST_COURSE"
FLAG_DEATH_BEFORE_FIRST_COURSE_DATE = "DEATH_DATE_BEFORE_FIRST_COURSE_DATE_INCONSISTENT"
FLAG_SAME_DAY_DEATH_AND_TREATMENT = "DEATH_ON_FIRST_COURSE_DATE"
FLAG_DEATH_ORDER_UNKNOWN = "DEAD_BUT_DEATH_OR_TREATMENT_DATE_UNKNOWN"
FLAG_VITAL_STATUS_UNRECOGNISED = "VITAL_STATUS_UNRECOGNISED"
FLAG_OUTSIDE_DATA_DEFAULTED = "OUTSIDE_DATA_STATUS_NOT_SUPPLIED"

# ---------------------------------------------------------------------------
# Raw value parsing
# ---------------------------------------------------------------------------
# Raw values: leading/trailing ASCII spaces and tabs are removed, nothing else
# (an internal blank, CR or LF makes a value malformed); digits are ASCII only.
# A value made only of whitespace (Java Character.isWhitespace: ASCII blanks,
# CR, LF, VT, FF, U+001C-001F and the Unicode space separators except the
# no-break spaces, e.g. U+3000) is no value at all: FHIR parsers such as HAPI
# drop such values, so every engine must treat them as absent. The CQL applies
# the same rule ("Trimmed", "Normalized Site"). Patterns use fullmatch: `$`
# would also match before a final newline.
BLANKS = " \t"
WHITESPACE = frozenset(" \t\n\r\x0b\x0c\x1c\x1d\x1e\x1f\u1680\u2000\u2001\u2002\u2003\u2004"
                       "\u2005\u2006\u2008\u2009\u200a\u2028\u2029\u205f\u3000")
_DATE_RE = re.compile(r"[0-9]{8}")
_SITE_RE = re.compile(r"C([0-9]{2})\.?([0-9])")


def is_blank(raw: str | None) -> bool:
    """True for None, "" and values made only of whitespace (see WHITESPACE)."""
    return raw is None or all(c in WHITESPACE for c in raw)


def registry_date(raw: str | None) -> date | None:
    """A real calendar date, or None for 00000000, 99999999, partial or impossible dates."""
    if raw is None:
        return None
    raw = raw.strip(BLANKS)
    if not _DATE_RE.fullmatch(raw):
        return None
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:  # month/day 00 or 99, 20250231, ...
        return None


def normalise_site(raw: str | None) -> str | None:
    """'C18.7' / ' c187 ' -> 'C187'; anything else -> None."""
    if raw is None:
        return None
    m = _SITE_RE.fullmatch(raw.strip(BLANKS).upper())
    return f"C{m.group(1)}{m.group(2)}" if m else None


def cancer_category(site: str | None) -> str | None:
    """HPA 癌別 used as part of the 註1 duplicate key.

    Returns "大腸癌" for C18.0, C18.2-C18.9, C19.9 and C20.9, otherwise None.

    * Colon and rectum are ONE 癌別: the indicator document has a single chapter
      「三、大腸癌診療」 and 指標群組「大腸癌」 for both the colon indicator
      (指標 2, C18) and the rectum indicator (指標 3, C19-20); the 115 colorectal
      attachment (附件2) speaks of 同步結直腸癌 (SSF9), i.e. treats synchronous
      colon/rectum primaries as one disease family.
    * C18.1 (appendix) is excluded: 附件2「適用範圍」defines 結腸癌 as
      C18.0-C18.9「不包含 Appendix C18.1」.
    * C21 (anus/anal canal) is excluded: no HPA 115 text mentions it; the only
      site lists are C18 and C19-20. Flagged for confirmation.
    """
    s = normalise_site(site)
    if s is None:
        return None
    if s == "C181":
        return None
    if s.startswith("C18") or s in {"C199", "C209"}:
        return COLORECTAL
    return None


def _site_flags(site: str | None) -> list[str]:
    s = normalise_site(site)
    if s is None:
        return []
    if s.startswith("C21"):
        return [FLAG_ANUS_EXCLUDED]
    if s == "C181":
        return [FLAG_APPENDIX_EXCLUDED]
    return []


# ---------------------------------------------------------------------------
# Stage severity (註1 tie-break)
# ---------------------------------------------------------------------------
# Every rankable code of the TWCR_LF CliStageGroup / PathStageGroup code systems,
# least to most severe. Ordering: main group 0 < I < II < III < IV; within a
# group the bare code (substage not recorded) ranks below its substages, then
# letters A < B < C < D, then digits 1 < 2 < 3. Codes that do not occur in AJCC
# colorectal staging (0A, 0IS, 1E, 1S, 2BU, 2E, 3D, 4A1, 4A2, ...) are placed by
# the same rule only so that the order is total. Not rankable: OC, 888 (不適用),
# 999 (不清楚或醫師未記錄), BBB, empty, anything else.
STAGE_SEVERITY_ORDER: tuple[str, ...] = (
    "0", "0A", "0IS",
    "1", "1A", "1A1", "1A2", "1A3", "1B", "1B1", "1B2", "1C", "1E", "1S",
    "2", "2A", "2A1", "2A2", "2B", "2BU", "2C", "2E",
    "3", "3A", "3A1", "3A2", "3B", "3C", "3C1", "3C2", "3D",
    "4", "4A", "4A1", "4A2", "4B", "4C",
)
_STAGE_RANK = {code: i for i, code in enumerate(STAGE_SEVERITY_ORDER)}


def stage_rank(raw: str | None) -> int | None:
    if raw is None:
        return None
    return _STAGE_RANK.get(raw.strip(BLANKS).upper())


def severity(fields: Mapping[str, str]) -> tuple[int | None, str | None]:
    """(rank, basis) used for the same-day tie-break.

    Pathological stage group (3.13) first — 說明檔第七點: 期別「除非個別指標特有所指，
    否則一般乃係指病理分期」. If 3.13 is not rankable (888/999/missing, e.g. no
    resection), fall back to the clinical stage group (3.7). Basis is "3.13",
    "3.7" or None (unrankable; ranks below every rankable stage).
    """
    for item in (PATHOLOGIC_STAGE_GROUP, CLINICAL_STAGE_GROUP):
        r = stage_rank(fields.get(item))
        if r is not None:
            return r, item
    return None, None


# ---------------------------------------------------------------------------
# Died before treatment (第二點)
# ---------------------------------------------------------------------------
def died_before_treatment(
    fields: Mapping[str, str],
    vital_status_codes: Mapping[str, bool] = DEFAULT_VITAL_STATUS_CODES,
) -> tuple[bool, list[str]]:
    """Return (excluded, flags).

    Excluded when ANY of:
      (a) 2.3.2 == "0" — the registry's own code 「未於申報醫院接受任何治療即死亡」.
      (b) 5.4 = dead, and 4.1 == "00000000" (no first course of treatment), and
          2.3.2 != "4" (a first course that *is* 「不予治療或是再密切觀察」/
          palliative-only is a treatment decision, not death before treatment).
      (c) 5.4 = dead, 5.3 and 4.1 are both real dates, and 5.3 < 4.1. Logically
          inconsistent registry data; excluded literally and flagged.
    Not excluded (flagged): dead with 5.3 == 4.1 (treatment started on the day
    of death); dead with 4.1 or 5.3 unknown (99999999 / invalid) where (a)/(b)
    do not apply — the order cannot be established, so no exclusion is made.
    5.3 is only read as a death date when 5.4 says dead; otherwise it is the
    last-contact date.
    """
    flags: list[str] = []
    tx_status = (fields.get(CLASS_OF_TX_STATUS) or "").strip(BLANKS)
    if tx_status == "0":
        return True, [FLAG_DIED_BASIS_TX_STATUS_0]

    raw_vs = fields.get(VITAL_STATUS)
    dead: bool | None = None
    if raw_vs is not None and raw_vs.strip(BLANKS) != "":
        # case-insensitive on both sides, like the CQL
        dead = {k.lower(): v for k, v in vital_status_codes.items()}.get(raw_vs.strip(BLANKS).lower())
        if dead is None:
            flags.append(FLAG_VITAL_STATUS_UNRECOGNISED)
    if not dead:
        return False, flags

    raw_first = (fields.get(FIRST_COURSE_START) or "").strip(BLANKS)
    if raw_first == NO_DATE:
        if tx_status == "4":
            return False, flags
        return True, flags + [FLAG_DIED_BASIS_NO_FIRST_COURSE]

    first = registry_date(raw_first)
    death = registry_date(fields.get(LAST_CONTACT_OR_DEATH))
    if first is None or death is None:
        return False, flags + [FLAG_DEATH_ORDER_UNKNOWN]
    if death < first:
        return True, flags + [FLAG_DEATH_BEFORE_FIRST_COURSE_DATE]
    if death == first:
        flags.append(FLAG_SAME_DAY_DEATH_AND_TREATMENT)
    return False, flags


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
@dataclass
class CohortResult:
    eligible: list[str]                                   # tumour ids, sorted
    excluded: dict[str, str]                              # tumour id -> reason code
    flags: dict[str, list[str]] = field(default_factory=dict)  # tumour id -> flags


def _key_part(raw: object) -> str | None:
    if raw is None or is_blank(str(raw)):
        return None
    return str(raw).strip(BLANKS).upper()


def _pick_representative(group: list[dict]) -> tuple[dict, list[str]]:
    """註1: earliest 2.5; same day -> more severe stage; still tied -> smallest tumour_id."""
    earliest = min(registry_date(r["fields"].get(DATE_OF_DIAGNOSIS)) for r in group)
    same_day = [r for r in group if registry_date(r["fields"].get(DATE_OF_DIAGNOSIS)) == earliest]
    if len(same_day) == 1:
        return same_day[0], []
    ranked = [(severity(r["fields"]), r) for r in same_day]
    best = max(-1 if s[0] is None else s[0] for s, _ in ranked)
    top = [r for (s, r) in ranked if (-1 if s[0] is None else s[0]) == best]
    flags = []
    if len(top) == 1:
        flags.append(FLAG_TIE_BROKEN_BY_STAGE)
    else:
        flags.append(FLAG_TIE_BROKEN_BY_TUMOUR_ID)
    kept = min(top, key=lambda r: r["tumour_id"])
    return kept, flags


def assemble_cohort(
    records: Iterable[Mapping],
    period: tuple[date, date] | None = None,
    outside_data: Mapping[str, str] | None = None,
    vital_status_codes: Mapping[str, bool] = DEFAULT_VITAL_STATUS_CODES,
) -> CohortResult:
    """Apply the general inclusion rules to colorectal registry records.

    period: inclusive (start, end) on 2.5; None = only the 2024-01-01 floor.
    outside_data: per-tumour 第五點 status for ONE indicator, supplied by the
        hospital (values in OUTSIDE_DATA_STATUSES). None = rule not applied
        (cohort shared by all indicators). When a mapping is given, tumours
        missing from it are treated as IN_HOSPITAL and flagged.
    """
    recs = [dict(r) for r in records]
    seen: set[str] = set()
    for r in recs:
        tid = r.get("tumour_id")
        if not tid or tid in seen:
            raise ValueError(f"tumour_id missing or duplicated: {tid!r}")
        seen.add(tid)
        r["fields"] = dict(r.get("fields") or {})
    if outside_data is not None:
        bad = {k: v for k, v in outside_data.items() if v not in OUTSIDE_DATA_STATUSES}
        if bad:
            raise ValueError(f"unknown outside-data status: {bad}")

    excluded: dict[str, str] = {}
    flags: dict[str, list[str]] = {}

    def flag(tid: str, items: list[str]) -> None:
        if items:
            flags.setdefault(tid, []).extend(items)

    # Steps 1-4: per-record checks
    candidates: dict[tuple[str, str, str], list[dict]] = {}
    for r in recs:
        tid, f = r["tumour_id"], r["fields"]
        site = f.get(PRIMARY_SITE)
        flag(tid, _site_flags(site))
        category = cancer_category(site)
        if category is None:
            excluded[tid] = NOT_COLORECTAL
            continue
        dx = registry_date(f.get(DATE_OF_DIAGNOSIS))
        if dx is None:
            excluded[tid] = INVALID_DIAGNOSIS_DATE
            continue
        if dx < REGISTRY_START:
            excluded[tid] = DIAGNOSIS_BEFORE_2024
            continue
        if period is not None and not (period[0] <= dx <= period[1]):
            excluded[tid] = OUTSIDE_MEASUREMENT_PERIOD
            continue
        hospital, patient = _key_part(r.get("hospital_id")), _key_part(r.get("patient_id"))
        if patient == NO_NATIONAL_ID:  # 長表 1.4: 個案無身分證統一編號
            patient = None
        if hospital is None or patient is None:
            excluded[tid] = MISSING_DEDUP_KEY
            continue
        candidates.setdefault((hospital, category, patient), []).append(r)

    # Step 5: 註1 de-duplication
    representatives: list[dict] = []
    for key in sorted(candidates):
        group = candidates[key]
        kept, tie_flags = _pick_representative(group)
        representatives.append(kept)
        if len(group) > 1:
            flag(kept["tumour_id"], tie_flags)
        for r in group:
            if r is not kept:
                excluded[r["tumour_id"]] = f"{DUPLICATE_OF}:{kept['tumour_id']}"
        if FLAG_TIE_BROKEN_BY_STAGE in tie_flags or FLAG_TIE_BROKEN_BY_TUMOUR_ID in tie_flags:
            for r in group:
                _, basis = severity(r["fields"])
                if basis == CLINICAL_STAGE_GROUP:
                    flag(r["tumour_id"], [FLAG_STAGE_BASIS_CLINICAL])
                elif basis is None:
                    flag(r["tumour_id"], [FLAG_STAGE_UNRANKABLE])

    # Steps 6-9: representative only
    eligible: list[str] = []
    for r in representatives:
        tid, f = r["tumour_id"], r["fields"]
        klass = (f.get(CLASS_OF_CASE) or "").strip(BLANKS)
        if klass not in {"1", "2"}:
            excluded[tid] = CLASS_NOT_1_OR_2
            continue
        if (
            klass == "2"
            and (f.get(CLASS_OF_DX_STATUS) or "").strip(BLANKS) == "2"
            and (f.get(CLASS_OF_TX_STATUS) or "").strip(BLANKS) == "3"
        ):
            excluded[tid] = CROSS_HOSPITAL_TREATMENT
            continue
        died, death_flags = died_before_treatment(f, vital_status_codes)
        flag(tid, death_flags)
        if died:
            excluded[tid] = DIED_BEFORE_TREATMENT
            continue
        if outside_data is not None:
            status = outside_data.get(tid)
            if status is None:
                flag(tid, [FLAG_OUTSIDE_DATA_DEFAULTED])
                status = IN_HOSPITAL
            if status == BOTH_OUTSIDE:
                excluded[tid] = OUTSIDE_DATA_BOTH
                continue
            if status == NUMERATOR_OUTSIDE_NOT_OBTAINED:
                excluded[tid] = OUTSIDE_NUMERATOR_NOT_OBTAINED
                continue
        eligible.append(tid)

    return CohortResult(eligible=sorted(eligible), excluded=excluded, flags=flags)
