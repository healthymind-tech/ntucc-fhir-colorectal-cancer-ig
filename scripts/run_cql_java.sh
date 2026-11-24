#!/usr/bin/env bash
# Cross-check: execute every synthetic CQL case on the HL7/CQF Java reference
# engine (info.cqframework engine-fhir) instead of cql-execution. Requires
# Java 17+; run SUSHI first (cd ig && sushi .) so ig/fsh-generated has the
# Measures. Set CQL_JAVA_RESULTS=<file> to also dump every evaluated value.
# See tools/cql-java/README.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${CQL_JAVA_WORK_DIR:-$ROOT/.cql-work/java}"
JAVA="${JAVA:-java}"
JAVAC="${JAVAC:-$(dirname "$(command -v "$JAVA")")/javac}"

# Pinned versions. Bump together; HAPI is forced so cql-to-elm and engine-fhir agree.
CQF_VERSION=3.26.0
HAPI_VERSION=8.2.0
SLF4J_VERSION=2.0.16
COURSIER_URL="https://github.com/coursier/coursier/releases/download/v2.1.25-M26/coursier.jar"
COURSIER_SHA256=97647d0378b877db2552a29caec075de1bae86375f0343ba82cf52d69193eb5e
CQL_IG_URL="https://hl7.org/fhir/uv/cql/STU2/package.tgz" # hl7.fhir.uv.cql#2.0.0, FHIRHelpers 4.0.1
CQL_IG_SHA256=a7c201465e98a7a528bf0ce1fff55e3d6f974efc8e19f99f476d88b3a063c35a

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
fetch() { # url sha256 dest
  if [ ! -s "$3" ] || [ "$(sha256 "$3")" != "$2" ]; then
    curl -fsSL -o "$3.tmp" "$1"
    local got; got="$(sha256 "$3.tmp")"
    if [ "$got" != "$2" ]; then echo "checksum mismatch for $1: $got" >&2; rm -f "$3.tmp"; exit 1; fi
    mv "$3.tmp" "$3"
  fi
}

mkdir -p "$WORK"
CLASSPATH_FILE="$WORK/classpath-cqf$CQF_VERSION-hapi$HAPI_VERSION.txt"
if [ ! -s "$CLASSPATH_FILE" ]; then
  fetch "$COURSIER_URL" "$COURSIER_SHA256" "$WORK/coursier.jar"
  force=()
  for a in base converter structures-r5 structures-r4 structures-dstu3 structures-dstu2 structures-hl7org-dstu2; do
    force+=(--force-version "ca.uhn.hapi.fhir:hapi-fhir-$a:$HAPI_VERSION")
  done
  "$JAVA" -jar "$WORK/coursier.jar" fetch --classpath \
    "info.cqframework:engine-fhir:$CQF_VERSION" \
    "info.cqframework:cql-to-elm:$CQF_VERSION" \
    "info.cqframework:quick:$CQF_VERSION" \
    "info.cqframework:model-jackson:$CQF_VERSION" \
    "org.slf4j:slf4j-simple:$SLF4J_VERSION" \
    "${force[@]}" > "$CLASSPATH_FILE.tmp"
  mv "$CLASSPATH_FILE.tmp" "$CLASSPATH_FILE"
fi

HELPERS="$WORK/FHIRHelpers-4.0.1.cql"
if [ ! -s "$HELPERS" ]; then
  fetch "$CQL_IG_URL" "$CQL_IG_SHA256" "$WORK/cql-package.tgz"
  tar -xOf "$WORK/cql-package.tgz" package/Library-FHIRHelpers.json \
    | python3 -I -c "import json,sys,base64;d=json.load(sys.stdin);assert d['version']=='4.0.1';sys.stdout.buffer.write(next(base64.b64decode(c['data']) for c in d['content'] if c['contentType']=='text/cql'))" \
    > "$HELPERS.tmp"
  mv "$HELPERS.tmp" "$HELPERS"
fi

SRC="$ROOT/tools/cql-java/src/CqlJavaRunner.java"
CLASSES="$WORK/classes"
CP="$(cat "$CLASSPATH_FILE")"
if [ ! -f "$CLASSES/CqlJavaRunner.class" ] || [ "$SRC" -nt "$CLASSES/CqlJavaRunner.class" ] || [ "$CLASSPATH_FILE" -nt "$CLASSES/CqlJavaRunner.class" ]; then
  rm -rf "$CLASSES"; mkdir -p "$CLASSES"
  "$JAVAC" --release 17 -nowarn -cp "$CP" -d "$CLASSES" "$SRC"
fi

cd "$ROOT"
"$JAVA" -Dorg.slf4j.simpleLogger.defaultLogLevel=warn -cp "$CP:$CLASSES" CqlJavaRunner \
  ig/input/cql "$HELPERS" tests/fixtures/cql/cases.json tests/fixtures/cql/value-sets.json ig/fsh-generated/resources \
  ${CQL_JAVA_RESULTS:+"$CQL_JAVA_RESULTS"}
