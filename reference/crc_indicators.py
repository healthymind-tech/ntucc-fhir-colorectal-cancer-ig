"""Reference implementation of the 115 colorectal cancer core indicators.

Independent of the CQL. The unit is a registry case, i.e. one primary tumour:
each tumour has its registry fields (long-form item number -> versions of the
raw string value) and, for indicator 1, the clinical facts linked to it. Each
check carries the criterion_id from mappings/crc-core-indicator-criteria.csv.
Population results are lists of tumour ids keyed by the CQL define names, so
the two implementations can be compared case by case on the same synthetic data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from reference.cohort import BLANKS, assemble_cohort, normalise_site

DATE_RE = re.compile(r"^[0-9]{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$")
COLON_EXCLUDING_APPENDIX = {f"C18{d}" for d in "023456789"}
RECTOSIGMOID_OR_RECTUM = {"C199", "C209"}
SPECIAL_HISTOLOGY = {"8935", "8936", "8153", "8240", "8241", "8242", "8246", "8249"}
POLYP_WINDOW = timedelta(days=84)  # 12 weeks
RECTAL_WINDOW_DAYS = 42  # 6 weeks
REGISTRY_START = date(2024, 1, 1)  # 收錄自 113/1/1 起新診斷
CURRENT_STATUSES = {"final", "amended", "corrected"}
POPULATIONS = ("Initial Population", "Denominator 1", "Numerator 1", "Denominator 2",
               "Denominator 2 Exclusion", "Numerator 2", "Denominator 3", "Numerator 3")


def current_values(versions: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    """IP-CURRENT. Field -> current raw value, trimmed of leading/trailing blanks.

    Among final/amended/corrected versions the one with the latest issued time
    wins; equal times fall back to the version id. A version without issued
    ranks below every dated version. An all-blank value counts as no value.
    """
    out = {}
    for number, items in versions.items():
        live = [v for v in items if v["status"] in CURRENT_STATUSES]
        dated = [v for v in live if v.get("issued")]
        if dated:
            chosen = max(dated, key=lambda v: (datetime.fromisoformat(v["issued"]), v["id"]))
        elif live:
            chosen = max(live, key=lambda v: v["id"])
        else:
            continue
        value = chosen["value"].strip(BLANKS)
        if value:
            out[number] = value
    return out


def registry_date(raw: str | None) -> date | None:
    if raw is None or not DATE_RE.match(raw):
        return None
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:  # e.g. 20250231
        return None


def registry_int(raw: str | None) -> int | None:
    if raw is None or not re.fullmatch(r"[0-9]+", raw):  # ASCII digits only
        return None
    return int(raw)


def normalized_site(raw: str | None) -> str | None:
    return normalise_site(raw)


def leading_digit(raw: str | None) -> str | None:
    return raw[0] if raw else None


@dataclass
class PolypFacts:
    """Clinical facts for indicator 1 (醫院自行申報)."""

    malignant_polyp_confirmed: bool = False
    # report_issued is the date of the pathology report linked to the tumour
    # through Condition.evidence; an unlinked report does not start the clock.
    report_issued: date | None = None
    high_risk_features: dict[str, bool] = field(default_factory=dict)  # A-D
    resections: list[tuple[date, str]] = field(default_factory=list)  # (date, status)

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> "PolypFacts":
        if not data:
            return cls()
        linked = data.get("report_issued") and data.get("report_linked", True)
        return cls(
            malignant_polyp_confirmed=data.get("malignant_polyp") == "confirmed",
            report_issued=date.fromisoformat(data["report_issued"]) if linked else None,
            high_risk_features=dict(data.get("features", {})),
            resections=[(date.fromisoformat(r["date"]), r.get("status", "completed")) for r in data.get("resections", [])],
        )


def evaluate(fields: dict[str, str], polyp: PolypFacts, period: tuple[date, date], in_cohort: bool) -> dict[str, Any]:
    """One tumour. in_cohort is the case assembly result (reference/cohort.py):
    IP-SCOPE, IP-DXDATE, IP-DUP, IP-CLASS, IP-CROSS and IP-DEATH."""
    f = fields.get
    out: dict[str, Any] = {}
    klass = f("2.3")
    ip = in_cohort
    out["Initial Population"] = ip

    # --- crc-qi-01 -----------------------------------------------------------
    out["Has Malignant Polyp"] = polyp.malignant_polyp_confirmed  # D1-POLYP
    out["Has High Risk Feature"] = any(polyp.high_risk_features.values())  # D1-FEATURE
    report = polyp.report_issued  # D1-REPORT
    out["Denominator 1"] = ip and out["Has Malignant Polyp"] and out["Has High Risk Feature"] and report is not None
    out["Numerator 1"] = out["Denominator 1"] and any(  # N1-RESECT
        status == "completed" and report <= when <= report + POLYP_WINDOW for when, status in polyp.resections
    )

    # --- crc-qi-02 -----------------------------------------------------------
    site = normalized_site(f("2.6"))
    surgery = registry_int(f("4.1.4"))
    out["Is Colon Excluding Appendix"] = site in COLON_EXCLUDING_APPENDIX  # D2-SITE
    out["Has Resection Surgery 30 To 90"] = surgery is not None and 30 <= surgery <= 90  # D2-SURG / X2-POLYP
    out["Is Pathological Stage I To III"] = leading_digit(f("3.13")) in {"1", "2", "3"}  # D2-PSTAGE
    out["Denominator 2"] = (
        ip
        and out["Is Colon Excluding Appendix"]
        and out["Has Resection Surgery 30 To 90"]
        and out["Is Pathological Stage I To III"]
    )
    out["Denominator 2 Exclusion"] = out["Denominator 2"] and (f("2.8") in SPECIAL_HISTOLOGY or f("2.9") == "2")  # X2-HIST
    nodes = registry_int(f("2.14"))
    out["Numerator 2"] = out["Denominator 2"] and nodes is not None and 12 <= nodes <= 90  # N2-LN12

    # --- crc-qi-03 -----------------------------------------------------------
    out["Is Rectosigmoid Or Rectum"] = site in RECTOSIGMOID_OR_RECTUM  # D3-SITE
    out["Is Clinical Stage II To III"] = leading_digit(f("3.7")) in {"2", "3"}  # D3-CSTAGE
    out["Denominator 3"] = (
        ip and out["Is Rectosigmoid Or Rectum"] and klass == "1" and out["Is Clinical Stage II To III"]  # D3-CLASS
    )
    confirm, first_course = registry_date(f("2.12")), registry_date(f("4.1"))
    days = (first_course - confirm).days if confirm and first_course else None
    out["Days From Confirmation To First Course"] = days
    out["Numerator 3"] = out["Denominator 3"] and days is not None and days <= RECTAL_WINDOW_DAYS  # N3-42D
    return out


def evaluate_case(case: dict[str, Any], period: tuple[date, date]) -> dict[str, list[str]]:
    """IP-UNIT. Population define -> sorted ids of the case's tumours that belong to it."""
    results = {name: [] for name in POPULATIONS}
    # A Condition recorded in error or refuted is never a case; registry items
    # with more than one focus are not attributed to any tumour.
    tumours = [t for t in case["tumours"] if t.get("verification") not in ("entered-in-error", "refuted")]
    current = {t["id"]: ({} if t.get("multi_focus") else current_values(t["fields"])) for t in tumours}
    tumours = [t for t in tumours if current[t["id"]]]
    cohort = assemble_cohort(
        [{"patient_id": case.get("national_id"), "hospital_id": current[t["id"]].get("1.1"),
          "tumour_id": t["id"], "fields": current[t["id"]]} for t in tumours],
        period=period,
    )
    outside = case.get("outside_excluded", {})  # IP-OUTSIDE (第五點): indicator -> tumour ids
    for tumour in tumours:
        out = evaluate(current[tumour["id"]], PolypFacts.from_json(tumour.get("polyp")), period,
                       tumour["id"] in cohort.eligible)
        for measure, excluded in outside.items():
            if tumour["id"] in excluded:
                for name in (f"Denominator {measure}", f"Numerator {measure}", f"Denominator {measure} Exclusion"):
                    if name in out:
                        out[name] = False
        for name in POPULATIONS:
            if out[name]:
                results[name].append(tumour["id"])
    return {name: sorted(ids) for name, ids in results.items()}


def proportion(results: list[dict[str, list[str]]], measure: int) -> dict[str, int]:
    """Aggregate tumour counts the way a summary MeasureReport would."""
    den, num, exc = (set().union(*(set(r.get(k, [])) for r in results)) for k in
                     (f"Denominator {measure}", f"Numerator {measure}", f"Denominator {measure} Exclusion"))
    ip = set().union(*(set(r["Initial Population"]) for r in results))
    return {
        "initial-population": len(ip),
        "denominator": len(den),
        "denominator-exclusion": len(exc & den),
        "numerator": len((num & den) - exc),
    }
