#!/usr/bin/env bash
# gate-verify.sh — Exit 1 when completed items in NEXT_SOC.md lack evidence notes.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)")"
NEXT="${REPO_ROOT}/.work.soc/plans/NEXT_SOC.md"
fail=0

gate_fail() { echo "FAIL: $*" >&2; fail=1; }

if [ ! -f "$NEXT" ]; then
  echo "gate-verify: PASS (no NEXT_SOC.md)"
  exit 0
fi

# Check "## Completed work" section (ai.soc convention)
# Each table row under that section must have a non-empty Detail cell.
in_block=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    '## Completed work'*)
      in_block=1
      continue
      ;;
    '## '*)
      in_block=0
      continue
      ;;
  esac
  [ "$in_block" -eq 0 ] && continue

  # Skip separator lines (|--|--|)
  [[ "$line" == *'---'* ]] && continue
  [[ "$line" != '| '* ]] && continue

  # Parse markdown table row: | Item | Detail |
  item="$(echo "$line" | cut -d'|' -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  detail="$(echo "$line" | cut -d'|' -f3 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

  [ -z "$item" ] && continue

  if [ -z "$detail" ]; then
    gate_fail "Completed item '${item}' has empty Detail — cite evidence"
  fi
done < "$NEXT"

if [ "$fail" -eq 0 ]; then
  echo "gate-verify: PASS"
else
  echo "gate-verify: FAIL"
fi
exit "$fail"
