"""Re-check every candidate code in mappings/terminology-candidates.csv on tx.fhir.org.

For each row with a target code it confirms the code exists, is active, and
that the official display still matches the CSV. Needs network access, so it
is not part of the default CI run; run it before a review session and before
each release:

    python3 scripts/verify_terminology.py

Exit status is non-zero if any code is missing, inactive, has a changed
display, or (SNOMED CT) is not in the International Edition module.
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TX = "https://tx.fhir.org/r4"
# Only SNOMED CT International Edition concepts are acceptable. Judged by the
# concept's module, not its SCTID: some concepts promoted from national
# extensions keep their extension-style identifier.
SNOMED_INTERNATIONAL = "900000000000207008"


def lookup(system: str, code: str) -> dict:
    params = [("system", system), ("code", code)]
    if system == "http://snomed.info/sct":
        # Asking for specific properties limits the response to them, so
        # "inactive" must be requested too or the active check would go blind.
        params += [("property", "moduleId"), ("property", "inactive")]
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{TX}/CodeSystem/$lookup?{query}", headers={"Accept": "application/fhir+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    if result.get("resourceType") == "OperationOutcome":
        return {"found": False}
    info = {"found": True, "display": None, "version": None, "active": True, "module": None}
    for parameter in result.get("parameter", []):
        if parameter["name"] in ("display", "version"):
            info[parameter["name"]] = parameter.get("valueString")
        if parameter["name"] == "property":
            parts = {part["name"]: part for part in parameter.get("part", [])}
            prop = parts.get("code", {}).get("valueCode")
            value = parts.get("value", {})
            if prop == "moduleId":
                info["module"] = value.get("valueCode")
            if prop == "inactive" and value.get("valueBoolean"):
                info["active"] = False
            if prop == "STATUS" and value.get("valueString") not in (None, "ACTIVE"):
                info["active"] = False
    return info


def main() -> int:
    with (ROOT / "mappings/terminology-candidates.csv").open(encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["target_code"]]
    problems = 0
    for row in rows:
        try:
            info = lookup(row["target_system"], row["target_code"])
        except OSError as error:
            print(f"ERROR   {row['target_code']}: {error}")
            problems += 1
            continue
        if not info["found"]:
            status = "MISSING"
        elif not info["active"]:
            status = "INACTIVE"
        elif row["target_system"] == "http://snomed.info/sct" and info["module"] != SNOMED_INTERNATIONAL:
            status = f"NOT INTERNATIONAL (module {info['module']})"
        elif info["display"] != row["target_display"]:
            status = f"DISPLAY CHANGED -> {info['display']!r}"
        else:
            status = "ok"
        problems += status != "ok"
        print(f"{status:8} {row['target_system'].split('/')[-1]:5} {row['target_code']:16} {row['target_display']}  [{info.get('version')}]")
    print(f"{len(rows) - problems}/{len(rows)} candidate codes verified")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
