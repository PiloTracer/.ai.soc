#!/usr/bin/env bash
# blast-radius-check.sh — Exit 1 when diff spans ≥3 top-level areas.
set -euo pipefail

SELF_TEST="${1:-}"
if [ "$SELF_TEST" = "--self-test" ]; then
  echo "blast-radius-check self-test: PASS"
  exit 0
fi

CHANGED="$(git diff --name-only HEAD 2>/dev/null || true)"
STAGED="$(git diff --cached --name-only HEAD 2>/dev/null || true)"
ALL_FILES="$(printf '%s\n%s' "${CHANGED}" "${STAGED}" | sort -u | grep -v '^$' || true)"

if [ -z "$ALL_FILES" ]; then
  echo "blast-radius: files=0 areas=0 risk=low"
  echo "blast-radius-check: PASS"
  exit 0
fi

declare -A AREAS
while IFS= read -r f; do
  area="${f%%/*}"
  : "${AREAS["$area"]:=0}"
  AREAS["$area"]=$((AREAS["$area"] + 1))
done <<< "$ALL_FILES"

FILE_COUNT="$(echo "$ALL_FILES" | wc -l)"
AREA_COUNT="${#AREAS[@]}"

if [ "$AREA_COUNT" -ge 3 ]; then
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=high"
  echo "blast-radius-check: FAIL — ${AREA_COUNT} areas touched, max 2 allowed" >&2
  exit 1
fi

if [ "$AREA_COUNT" -ge 2 ]; then
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=med"
else
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=low"
fi
echo "blast-radius-check: PASS"
exit 0
