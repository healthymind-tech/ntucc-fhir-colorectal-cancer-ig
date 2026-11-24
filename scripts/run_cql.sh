#!/usr/bin/env bash
# Translate the CQL and execute every synthetic case. Requires Java 17+ and
# Node 20+; run SUSHI and scripts/build_fixtures.py first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${CQL_WORK_DIR:-$ROOT/.cql-work}"
JAVA="${JAVA:-java}"
mkdir -p "$WORK/elm-out"
COURSIER_SHA256=97647d0378b877db2552a29caec075de1bae86375f0343ba82cf52d69193eb5e
CQL_IG_SHA256=a7c201465e98a7a528bf0ce1fff55e3d6f974efc8e19f99f476d88b3a063c35a
sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
verify() { [ "$(sha256 "$1")" = "$2" ] || { echo "checksum mismatch for $1" >&2; rm -f "$1"; exit 1; }; }
cd "$WORK"
if [ ! -s classpath.txt ]; then
  curl -fsSL -o coursier.jar "https://github.com/coursier/coursier/releases/download/v2.1.25-M26/coursier.jar"
  verify coursier.jar "$COURSIER_SHA256"
  "$JAVA" -jar coursier.jar fetch --classpath info.cqframework:cql-to-elm-cli:3.26.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-structures-r5:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-structures-r4:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-structures-dstu3:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-structures-dstu2:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-structures-hl7org-dstu2:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-converter:8.2.0 \
    --force-version ca.uhn.hapi.fhir:hapi-fhir-base:8.2.0 > classpath.txt
fi
if [ ! -s elm-out/FHIRHelpers.json ]; then
  curl -fsSL -o cql-package.tgz "https://hl7.org/fhir/uv/cql/STU2/package.tgz"
  verify cql-package.tgz "$CQL_IG_SHA256"
  tar -xOf cql-package.tgz package/Library-FHIRHelpers.json \
    | python3 -I -c "import json,sys,base64;d=json.load(sys.stdin);sys.stdout.buffer.write(next(base64.b64decode(c['data']) for c in d['content'] if c['contentType']=='application/elm+json'))" \
    > elm-out/FHIRHelpers.json
fi
cd "$ROOT"
"$JAVA" -cp "$(cat "$WORK/classpath.txt")" org.cqframework.cql.cql2elm.cli.Main \
  --input ig/input/cql/ColorectalCancerCoreIndicators.cql --root-dir ig \
  --output "$WORK/elm-out" --format JSON --signatures Overloads 2>&1 | tee "$WORK/cql-translation.log" | grep -E "^(Error|Warning)" || true
if grep -qE '^Error|Translation failed|failed due to errors|ELM generation failed' "$WORK/cql-translation.log"; then
  echo "CQL translation failed" >&2; exit 1
fi
node ig/tools/cql-evaluation/run-asserted-cases.js \
  "$WORK/elm-out/ColorectalCancerCoreIndicators.json" "$WORK/elm-out/FHIRHelpers.json" \
  tests/fixtures/cql/cases.json tests/fixtures/cql/value-sets.json ig/fsh-generated/resources
