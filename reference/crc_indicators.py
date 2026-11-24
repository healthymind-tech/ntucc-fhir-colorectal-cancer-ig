"""Reference implementation of the 115 colorectal cancer core indicators.

Independent of the CQL: it reads a flat registry record (TCR long-form field
number -> raw string) plus, for indicator 1, a small set of clinical facts.
Each check carries the criterion_id from mappings/crc-core-indicator-criteria.csv.
The returned keys are the CQL define names, so the two implementations can be
compared case by case on the same synthetic data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

DATE_RE = re.compile(r"^[0-9]{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$")
COLON_EXCLUDING_APPENDIX = {f"C18{d}" for d in "023456789"}
RECTOSIGMOID_OR_RECTUM = {"C199", "C209"}
SPECIAL_HISTOLOGY = {"8935", "8936", "8153", "8240", "8241", "8242", "8246", "8249"}
POLYP_WINDOW = timedelta(days=84)  # 12 weeks
RECTAL_WINDOW_DAYS = 42  # 6 weeks
REGISTRY_START = date(2024, 1, 1)  # 收錄自 113/1/1 起新診斷


def registry_date(raw: str | None) -> date | None:
    if raw is None or not DATE_RE.match(raw):
        return None
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:  # e.g. 20250231
        return None


def registry_int(raw: str | None) -> int | None:
    if raw is None or not raw.isdigit():
        return None
    return int(raw)


def normalized_site(raw: str | None) -> str | None:
    return None if raw is None else raw.replace(".", "").upper()


def leading_digit(raw: str | None) -> str | None:
    return raw[0] if raw else None


@dataclass
class PolypFacts:
    """Clinical facts for indicator 1 (醫院自行申報)."""

    malignant_polyp_confirmed: bool = False
    report_issued: date | None = None
    high_risk_features: dict[str, bool] = field(default_factory=dict)  # A-D
    resections: list[tuple[date, str]] = field(default_factory=list)  # (date, status)

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> "PolypFacts":
        if not data:
            return cls()
        return cls(
            malignant_polyp_confirmed=data.get("malignant_polyp") == "confirmed",
            report_issued=date.fromisoformat(data["report_issued"]) if data.get("report_issued") else None,
            high_risk_features=dict(data.get("features", {})),
            resections=[(date.fromisoformat(r["date"]), r.get("status", "completed")) for r in data.get("resections", [])],
        )


def evaluate(fields: dict[str, str], polyp: PolypFacts, period: tuple[date, date]) -> dict[str, Any]:
    f = fields.get
    out: dict[str, bool] = {}

    # --- shared initial population ------------------------------------------
    dx = registry_date(f("2.5"))
    klass = f("2.3")
    cross = klass == "2" and f("CLASS-DX-STATUS") == "2" and f("CLASS-TX-STATUS") == "3"  # IP-CROSS
    out["Cross Hospital Treatment"] = cross
    ip = (
        dx is not None
        and dx >= REGISTRY_START  # IP-DXDATE
        and period[0] <= dx <= period[1]
        and klass in {"1", "2"}  # IP-CLASS
        and not cross
    )
    out["Initial Population"] = ip

    # --- crc-qi-01 -----------------------------------------------------------
    out["Has Malignant Polyp"] = polyp.malignant_polyp_confirmed  # D1-POLYP
    out["Has High Risk Feature"] = any(polyp.high_risk_features.values())  # D1-FEATURE
    report = polyp.report_issued  # D1-REPORT
    out["Denominator 1"] = ip and out["Has Malignant Polyp"] and out["Has High Risk Feature"] and report is not None
    out["Numerator 1"] = report is not None and any(  # N1-RESECT
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
    out["Denominator 2 Exclusion"] = f("2.8") in SPECIAL_HISTOLOGY or f("2.9") == "2"  # X2-HIST
    nodes = registry_int(f("2.14"))
    out["Numerator 2"] = nodes is not None and 12 <= nodes <= 90  # N2-LN12

    # --- crc-qi-03 -----------------------------------------------------------
    out["Is Rectosigmoid Or Rectum"] = site in RECTOSIGMOID_OR_RECTUM  # D3-SITE
    out["Is Clinical Stage II To III"] = leading_digit(f("3.7")) in {"2", "3"}  # D3-CSTAGE
    out["Denominator 3"] = (
        ip and out["Is Rectosigmoid Or Rectum"] and klass == "1" and out["Is Clinical Stage II To III"]  # D3-CLASS
    )
    confirm, first_course = registry_date(f("2.12")), registry_date(f("4.1"))
    days = (first_course - confirm).days if confirm and first_course else None
    out["Days From Confirmation To First Course"] = days
    out["Numerator 3"] = days is not None and days <= RECTAL_WINDOW_DAYS  # N3-42D
    return out


def proportion(results: list[dict[str, bool]], measure: int) -> dict[str, int]:
    """Aggregate population counts the way a summary MeasureReport would."""
    den_key, num_key, exc_key = f"Denominator {measure}", f"Numerator {measure}", f"Denominator {measure} Exclusion"
    denominator = [r for r in results if r["Initial Population"] and r[den_key]]
    excluded = [r for r in denominator if r.get(exc_key, False)]
    remaining = [r for r in denominator if not r.get(exc_key, False)]
    return {
        "initial-population": sum(r["Initial Population"] for r in results),
        "denominator": len(denominator),
        "denominator-exclusion": len(excluded),
        "numerator": sum(r[num_key] for r in remaining),
    }
