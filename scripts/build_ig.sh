#!/usr/bin/env bash
# Build the HTML IG with the HL7 IG Publisher.
# The Publisher refuses to run in a folder whose path contains spaces, so the
# project is copied to a space-free work directory, built there, and the
# output/ folder is copied back to ig/output/.
#
# Requires: Java 17+, Node (ig/tools: npm ci), Ruby + Jekyll.
# Environment overrides: JAVA, IG_BUILD_DIR, PUBLISHER_JAR
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JAVA="${JAVA:-java}"
WORK="${IG_BUILD_DIR:-/tmp/tw-crc-ig-build}"
JAR="${PUBLISHER_JAR:-$WORK/../publisher.jar}"
case "$WORK" in *" "*) echo "IG_BUILD_DIR must not contain spaces: $WORK" >&2; exit 1;; esac

mkdir -p "$WORK" "$(dirname "$JAR")"
if [ ! -s "$JAR" ]; then
  curl -fsSL -o "$JAR" https://github.com/HL7/fhir-ig-publisher/releases/latest/download/publisher.jar
fi
rsync -a --delete --exclude node_modules --exclude .venv --exclude .cql-work \
  --exclude ig/input-cache --exclude ig/temp --exclude ig/output --exclude ig/template \
  "$ROOT/" "$WORK/"
mkdir -p "$WORK/.bin"
ln -sf "$ROOT/ig/tools/node_modules/.bin/sushi" "$WORK/.bin/sushi"
(cd "$WORK/ig" && PATH="$WORK/.bin:$PATH" "$JAVA" -Xmx4g -jar "$JAR" -ig .)
rm -rf "$ROOT/ig/output" && cp -R "$WORK/ig/output" "$ROOT/ig/output"
echo "IG built: $ROOT/ig/output/index.html"
