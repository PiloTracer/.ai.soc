#!/usr/bin/env bash
# touch-scope-verify.sh — Exit 1 when changed files fall outside declared scope.
# Scope is declared in .work.soc/touch-scope — one path prefix per line.
# Directories listed with trailing / allow everything under them.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)")"
SCOPE_FILE="${REPO_ROOT}/.work.soc/touch-scope"

SELF_TEST="${1:-}"
if [ "$SELF_TEST" = "--self-test" ]; then
  echo "touch-scope-verify self-test: PASS"
  exit 0
fi

if [ ! -f "$SCOPE_FILE" ]; then
  echo "skip: no .work.soc/touch-scope — declare scope first"
  exit 0
fi

# Read allowed path prefixes from scope file
ALLOWED=()
while IFS= read -r line; do
  trimmed="${line#"${line%%[![:space:]]*}"}"   # strip leading whitespace
  trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"  # strip trailing whitespace
  [ -z "$trimmed" ] && continue
  [[ "$trimmed" == \#* ]] && continue
  ALLOWED+=("$trimmed")
done < "$SCOPE_FILE"

if [ ${#ALLOWED[@]} -eq 0 ]; then
  echo "FAIL: .work.soc/touch-scope is empty — add at least one allowed path" >&2
  exit 1
fi

# Collect changed files
CHANGED="$(git diff --name-only HEAD 2>/dev/null || true)"
STAGED="$(git diff --cached --name-only HEAD 2>/dev/null || true)"
ALL_FILES="$(printf '%s\n%s' "${CHANGED}" "${STAGED}" | sort -u | grep -v '^$' || true)"

if [ -z "$ALL_FILES" ]; then
  echo "touch-scope-verify: PASS (no changed files)"
  exit 0
fi

# Check each changed file against allowed prefixes
OFFENDING=()
while IFS= read -r f; do
  in_scope=0
  for allowed in "${ALLOWED[@]}"; do
    if [[ "$allowed" == */ ]]; then
      # Trailing / → prefix match
      if [[ "$f" == "$allowed"* ]]; then
        in_scope=1
        break
      fi
    elif [[ "$f" == "$allowed" ]]; then
      in_scope=1
      break
    fi
  done
  [ "$in_scope" -eq 0 ] && OFFENDING+=("$f")
done <<< "$ALL_FILES"

if [ ${#OFFENDING[@]} -gt 0 ]; then
  echo "FAIL: file(s) outside declared scope:" >&2
  printf '  - %s\n' "${OFFENDING[@]}" >&2
  echo "touch-scope-verify: FAIL" >&2
  exit 1
fi

echo "touch-scope-verify: PASS ($(echo "$ALL_FILES" | wc -l) file(s) in scope)"
exit 0
