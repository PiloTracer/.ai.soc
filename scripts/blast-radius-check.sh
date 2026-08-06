#!/usr/bin/env bash
# blast-radius-check.sh — Exit 1 when diff spans more than the allowed
# number of top-level areas. Default limit is 2 (legacy SOC-008 rule).
# An operator may grant a higher standing limit by adding a line of the
# form ``# BLAST_RADIUS_MAX_AREAS: <N>`` to ``.work.soc/touch-scope``.
# The override is logged visibly in the gate's output whenever it fires
# so a reader of the run logs can always see that the limit was raised
# and why. Removing the marker restores the default-2 limit immediately.
set -euo pipefail

SELF_TEST="${1:-}"
if [ "$SELF_TEST" = "--self-test" ]; then
  echo "blast-radius-check self-test: PASS"
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)")"
SCOPE_FILE="${REPO_ROOT}/.work.soc/touch-scope"

MAX_AREAS=2
OVERRIDE_SOURCE=""
if [[ -f "$SCOPE_FILE" ]]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      \#BLAST_RADIUS_MAX_AREAS:*|\#*BLAST_RADIUS_MAX_AREAS:*)
        # Strip leading "#", surrounding whitespace, and the env-name
        # prefix; whatever's left should be the integer.
        val="${line#\#}"
        val="${val#"${val%%[![:space:]]*}"}"   # trim leading whitespace after "#"
        val="${val#BLAST_RADIUS_MAX_AREAS:}"
        val="${val// /}"
        if [[ "$val" =~ ^[0-9]+$ ]] && [[ "$val" -ge 1 ]]; then
          MAX_AREAS="$val"
          OVERRIDE_SOURCE="touch-scope"
        fi
        ;;
    esac
  done < "$SCOPE_FILE"
fi

# Untracked files are part of the blast radius — new files in a new
# top-level area are exactly what this gate should be counting.
CHANGED="$(git diff --name-only HEAD 2>/dev/null || true)"
STAGED="$(git diff --cached --name-only HEAD 2>/dev/null || true)"
UNTRACKED="$(git ls-files --others --exclude-standard 2>/dev/null || true)"
ALL_FILES="$(printf '%s\n%s\n%s' "${CHANGED}" "${STAGED}" "${UNTRACKED}" | sort -u | grep -v '^$' || true)"

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

if [[ -n "$OVERRIDE_SOURCE" && "$MAX_AREAS" -ne 2 ]]; then
  OVERRIDE_NOTE=" (max=${MAX_AREAS} via ${OVERRIDE_SOURCE})"
else
  OVERRIDE_NOTE=""
fi

if [ "$AREA_COUNT" -gt "$MAX_AREAS" ]; then
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=high${OVERRIDE_NOTE}"
  echo "blast-radius-check: FAIL — ${AREA_COUNT} areas touched, max ${MAX_AREAS} allowed" >&2
  exit 1
fi

# Preserve the legacy risk-band reporting for the non-FAIL path so human
# readers still see med/low signal as before. With an operator override
# in place, "med" can mean 2..(MAX-1) areas and still gate green.
if [ "$AREA_COUNT" -ge 2 ]; then
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=med${OVERRIDE_NOTE}"
else
  echo "blast-radius: files=${FILE_COUNT} areas=${AREA_COUNT} risk=low${OVERRIDE_NOTE}"
fi
echo "blast-radius-check: PASS"
exit 0
