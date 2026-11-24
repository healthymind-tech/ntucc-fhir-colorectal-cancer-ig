"""Registry long-form values -> ICD-O-3 codes.

The Taiwan cancer registry stores primary site (2.6) as ICD-O-3 topography
without the dot ("C187") and histology (2.8) / behavior (2.9) as separate
fields ("8140", "3"). FHIR conventionally writes ICD-O-3 topography with the
dot ("C18.7", as mCODE does) and morphology as "histology/behavior" ("8140/3").

Both functions are strict: anything that is not a well-formed code raises
ValueError instead of producing a plausible-looking wrong code.
"""

from __future__ import annotations

import re

# Same raw-value rule as reference.cohort: ASCII digits, only leading/trailing
# spaces and tabs trimmed, whole-string (fullmatch) patterns.
_BLANKS = " \t"
_TOPOGRAPHY = re.compile(r"C([0-9]{2})\.?([0-9])")
_HISTOLOGY = re.compile(r"[0-9]{4}")
_BEHAVIOR = re.compile(r"[0-36]")  # ICD-O-3 behavior codes 0, 1, 2, 3, 6


def topography(raw: str) -> str:
    """'C187', 'C18.7', ' c187 ' -> 'C18.7'."""
    match = _TOPOGRAPHY.fullmatch(raw.strip(_BLANKS).upper())
    if not match:
        raise ValueError(f"not an ICD-O-3 topography code: {raw!r}")
    return f"C{match.group(1)}.{match.group(2)}"


def morphology(histology: str, behavior: str) -> str:
    """('8140', '3') -> '8140/3'."""
    histology, behavior = histology.strip(_BLANKS), behavior.strip(_BLANKS)
    if not _HISTOLOGY.fullmatch(histology):
        raise ValueError(f"not an ICD-O-3 histology code: {histology!r}")
    if not _BEHAVIOR.fullmatch(behavior):
        raise ValueError(f"not an ICD-O-3 behavior code: {behavior!r}")
    return f"{histology}/{behavior}"
