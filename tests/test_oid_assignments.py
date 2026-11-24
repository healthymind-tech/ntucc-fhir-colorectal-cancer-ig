"""The committed OID register: derived root, complete, unique, never suppressed."""

import configparser
import json
import re
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "ig/sushi-config.yaml"
OIDS = ROOT / "ig/oids.ini"
GENERATED = ROOT / "ig/fsh-generated/resources"
CANONICAL = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig"
OID_ROOT = f"2.25.{uuid.uuid5(uuid.NAMESPACE_URL, CANONICAL).int}"
CANONICAL_TYPES = {"CodeSystem", "ValueSet", "ConceptMap", "StructureDefinition", "Library", "Measure", "NamingSystem"}


def register():
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(OIDS, encoding="utf-8-sig")
    return parser


def test_root_is_derived_from_the_canonical():
    config = CONFIG.read_text(encoding="utf-8")
    assert f"canonical: {CANONICAL}" in config
    assert f"auto-oid-root: {OID_ROOT}" in config
    assert OID_ROOT == "2.25.142027862386738326818551980187783253635"


def test_register_is_consistent_unique_and_under_the_root():
    parser = register()
    declared = {kind: int(count) for kind, count in parser["Key"].items()}
    oids = []
    for kind, count in declared.items():
        section = dict(parser[kind])
        assert len(section) == count, f"[Key] count for {kind} does not match its section"
        oids += section.values()
    assert len(oids) == len(set(oids)), "an OID is assigned twice"
    assert all(re.fullmatch(re.escape(OID_ROOT) + r"\.\d+\.\d+", oid) for oid in oids)


@pytest.mark.skipif(not GENERATED.exists(), reason="run SUSHI first")
def test_every_canonical_resource_has_a_committed_oid():
    parser = register()
    missing = []
    for path in GENERATED.glob("*.json"):
        resource = json.loads(path.read_text(encoding="utf-8"))
        kind = resource["resourceType"]
        if kind in CANONICAL_TYPES and not (parser.has_section(kind) and parser.has_option(kind, resource["id"])):
            missing.append(f"{kind}/{resource['id']}")
    assert not missing, f"run scripts/build_ig.sh and commit ig/oids.ini; missing: {missing}"


def test_oid_warnings_are_not_suppressed():
    ignored = (ROOT / "ig/input/ignoreWarnings.txt").read_text(encoding="utf-8")
    assert "OID" not in ignored and "auto-oid-root" not in ignored
