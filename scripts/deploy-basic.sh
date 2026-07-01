#!/usr/bin/env bash
# deploy-basic.sh — Thin-client bootstrap of .ai.soc into a target project.
#
# Copies ONLY the minimal scaffold into the target:
#   - .cursorrules SOC block snippet (appended / created) with SOC_SOURCE pointer
#   - .work.soc/ skeleton (HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC, README, dirs)
#
# Framework assets (skills/, standards/, concepts/, scripts/, templates/)
# are NOT copied — the target's .cursorrules carries a SOC_SOURCE pointer so
# the agent resolves them from the source .ai.soc at runtime (thin-client mode).
#
# Default = NO-OVERWRITE: existing target files are preserved by construction.
# --update: no-overwrite + re-syncs the source pointer + lists existing-but-
# differing local-surface files as merge candidates for agent rules-aware merge.
# --force: idempotent overwrite of the local scaffold surface only.
#
# Source resolution: SOC_ROOT is derived from this script's location, so the
# script can be invoked from a TARGET using an external source .ai.soc:
#   bash /mnt/work/Projects/.ai.soc/scripts/deploy-basic.sh /mnt/work/Projects/tools-project
# Override the source with SOC_SOURCE=/abs/path/.ai.soc if needed.
#
# Usage:
#   bash scripts/deploy-basic.sh <target-path>              # no-overwrite (skip existing)
#   bash scripts/deploy-basic.sh <target-path> --update    # no-overwrite + merge candidate list
#   bash scripts/deploy-basic.sh <target-path> --force     # overwrite local scaffold (legacy)
#   SOC_SOURCE=/path/.ai.soc bash scripts/deploy-basic.sh <target-path>
#
set -euo pipefail

RAW_TARGET="${1:?Usage: $0 <target-path> [--force|--update]}"
shift || true
MODE="skip"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)  MODE="force" ;;
    --update) MODE="update" ;;
    *) echo "ERROR: unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

# Source .ai.soc root: explicit override wins, else derive from script location.
if [[ -n "${SOC_SOURCE:-}" ]]; then
  SOC_ROOT="$(cd "$SOC_SOURCE" && pwd)"
else
  SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Target = repo root of the consumer.
if [[ "$RAW_TARGET" == "." || "$RAW_TARGET" == "$PWD" ]]; then
  DEST_ROOT="$(cd "$RAW_TARGET" && pwd)"
else
  DEST_ROOT="$(cd "$RAW_TARGET" && pwd)"
fi

if [[ ! -d "$DEST_ROOT" ]]; then
  echo "ERROR: target directory does not exist: $DEST_ROOT" >&2
  exit 1
fi

TPL_CURS="${SOC_ROOT}/templates/cursorrules.soc.snippet.template"
TPL_WORK="${SOC_ROOT}/templates/work"

echo "=== deploy-basic (thin-client) → $DEST_ROOT ==="
echo "  source: $SOC_ROOT"
echo "  mode:   $MODE (no-overwrite by default)"

# Pre-scan target .cursorrules for existing source pointer.
CURS_DEST="${DEST_ROOT}/.cursorrules"
existing_source=""
if [[ -f "$CURS_DEST" ]]; then
  existing_source="$(grep -oE 'SOC_SOURCE=[^ ]*' "$CURS_DEST" | head -1 | cut -d= -f2- || true)"
  echo "  cursorrules: exists (keeping existing — will append SOC block if missing)"
fi

# Step 1: Append SOC block snippet to target .cursorrules (no-overwrite on the SOC block itself).
# The snippet includes the SOC_SOURCE pointer substitution.
append_soc_block() {
  if [[ ! -f "$TPL_CURS" ]]; then
    echo "  skip: cursorrules SOC snippet template not found at $TPL_CURS" >&2
    return
  fi
  # Check if block already present.
  if grep -q 'SOC_DESIGN_OS_BEGIN' "$CURS_DEST" 2>/dev/null; then
    echo "  cursorrules: SOC block already present — skipping append"
    return
  fi
  # Build the substituted snippet content.
  {
    echo ""
    cat "$TPL_CURS" | sed "s|REPLACE_SOCSOURCE|${SOC_ROOT}|g"
  } >> "$CURS_DEST"
  echo "  cursorrules: appended SOC block (SOC_SOURCE=$SOC_ROOT)"
}
append_soc_block

# Re-sync source pointer when --update and the existing pointer is stale.
if [[ "$MODE" == "update" ]] && [[ -n "$existing_source" ]] && [[ "$existing_source" != "$SOC_ROOT" ]]; then
  if grep -q 'SOC_SOURCE=' "$CURS_DEST"; then
    SOC_ROOT_ESC="${SOC_ROOT//\//\\/}"
    OLD_ESC="${existing_source//\//\\/}"
    perl -i -pe "s{SOC_SOURCE=\Q${existing_source}\E}{SOC_SOURCE=${SOC_ROOT_ESC}}" "$CURS_DEST" 2>/dev/null || \
      perl -i -pe "s/SOC_SOURCE=[^\n]*/SOC_SOURCE=${SOC_ROOT_ESC}/" "$CURS_DEST"
    echo "  cursorrules: re-synced SOC_SOURCE → $SOC_ROOT (was: ${existing_source:-<unset>})"
  fi
fi

# Step 2: .work.soc/ skeleton via bootstrap.sh (no-overwrite).
BOOTSTRAP_SKIP_CURSERRULES=1 REPO_ROOT="$DEST_ROOT" bash "$SOC_ROOT/templates/bootstrap.sh" \
  > /tmp/deploy-basic-bootstrap.$$.log 2>&1 || { cat /tmp/deploy-basic-bootstrap.$$.log; rm -f /tmp/deploy-basic-bootstrap.$$.log; exit 1; }
grep -E '^(created:|skip )' /tmp/deploy-basic-bootstrap.$$.log | sed 's/^/  work: /'
rm -f /tmp/deploy-basic-bootstrap.$$.log

# Step 3: --update — list merge candidates.
if [[ "$MODE" == "update" ]]; then
  echo ""
  echo "=== update merge candidates ==="
  # .cursorrules SOC block vs current snippet
  if [[ -f "$CURS_DEST" ]]; then
    echo "  review: .cursorrules (SOC block — agent checks for stale source pointer + missing sections)"
  fi
  # .work.soc/ files vs source templates
  WORK_FILES=(
    "README.md" "context/HANDOFF_SOC.md" "plans/NEXT_SOC.md"
    "plans/UNKNOWNS_SOC.md" "analysis/README.md"
  )
  for f in "${WORK_FILES[@]}"; do
    src="${TPL_WORK}/${f}.template"
    dest="${DEST_ROOT}/.work.soc/${f}"
    [[ -f "$src" && -f "$dest" ]] || continue
    if ! cmp -s "$src" "$dest"; then
      echo "  merge: .work.soc/${f}  (target has user content — agent appends new template sections only)"
    fi
  done
  echo "  (agent performs rules-aware merge — append new sections, preserve target"
  echo "   customizations. See skill deploy-basic/skill.md § update-merge.)"
fi

echo ""
echo "=== Done: thin-client bootstrap → $DEST_ROOT ==="
echo "  SOC block in .cursorrules: $(grep -q 'SOC_DESIGN_OS_BEGIN' "$CURS_DEST" 2>/dev/null && echo present || echo MISSING)"
echo "  SOC_SOURCE: $(grep -oE 'SOC_SOURCE=[^ ]*' "$CURS_DEST" 2>/dev/null | head -1 | cut -d= -f2- || echo '<unset>')"
echo "  .work.soc/: $([ -d "${DEST_ROOT}/.work.soc" ] && echo present || echo MISSING)"
echo ""
echo "Next steps in target project:"
echo "  1. Skills load from \$SOC_SOURCE at runtime (thin-client mode)"
echo "  2. Verify source reachable: test -d \"\$(grep -oE 'SOC_SOURCE=[^ ]*' $CURS_DEST | cut -d= -f2-)\""
echo "  3. Run @session-soc start"