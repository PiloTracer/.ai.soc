#!/usr/bin/env bash
# deploy-files.sh — Deploy .ai.soc files into a target project.
#
# Copies ONLY files git considers (tracked + untracked-not-ignored): anything
# in .gitignore — credentials, private context, tmp/ — is never deployed.
# This makes "files excluded in .git are never copied" an invariant enforced
# by construction, not a hand-maintained exclude list.
#
# Then strips skill-level intentional omissions (.github/, .gitignore,
# .gitattributes, .cursorrules, deploy scripts).
#
# Default = NO-OVERWRITE: existing files in the target are skipped (target-side
# customizations are preserved by construction). Use --force for the legacy
# idempotent-overwrite behavior, or --update to additionally emit a candidate
# list of existing-but-differing files for agent-driven rules-aware merge.
#
# Source resolution: SOC_ROOT is derived from this script's location, so the
# script can be invoked from a TARGET directory using an external source .ai.soc:
#   bash /mnt/work/Projects/.ai.soc/scripts/deploy-files.sh .
# Override the source with SOC_SOURCE=/abs/path/.ai.soc if needed.
#
# Usage:
#   bash scripts/deploy-files.sh <target-path>              # no-overwrite (skip existing)
#   bash scripts/deploy-files.sh <target-path> --force      # overwrite existing (legacy)
#   bash scripts/deploy-files.sh <target-path> --update     # no-overwrite + emit merge candidates
#   SOC_SOURCE=/path/.ai.soc bash scripts/deploy-files.sh <target-path>
#
set -euo pipefail

RAW_TARGET="${1:?Usage: $0 <target-path> [--force|--update]}"
shift || true
MODE="skip"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)   MODE="force" ;;
    --update)  MODE="update" ;;
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

# Resolve target: if path ends with .ai.soc, use as-is; otherwise append .ai.soc
if [[ "$RAW_TARGET" == *.ai.soc ]]; then
  DEST_DIR="$RAW_TARGET"
else
  DEST_DIR="${RAW_TARGET}/.ai.soc"
fi

PARENT="$(dirname "$DEST_DIR")"
if [[ ! -d "$PARENT" ]]; then
  echo "ERROR: parent directory does not exist: $PARENT" >&2
  exit 1
fi

if [[ -e "$DEST_DIR" ]] && [[ ! -d "$DEST_DIR" ]]; then
  echo "ERROR: $DEST_DIR exists but is not a directory" >&2
  exit 1
fi

# Source must be a git repo so the tracked/not-ignored set is authoritative.
if ! (cd "$SOC_ROOT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
  echo "ERROR: source $SOC_ROOT is not a git repo." >&2
  echo "  deploy-files copies only git-tracked / non-ignored files (never .gitignored content)." >&2
  exit 1
fi

GIT_TOP="$(cd "$SOC_ROOT" && git rev-parse --show-toplevel)"
if [[ "$GIT_TOP" != "$SOC_ROOT" ]]; then
  echo "ERROR: $SOC_ROOT is not the git repo root (root is $GIT_TOP)." >&2
  echo "  deploy-files expects the .ai.soc directory to be the repository root." >&2
  exit 1
fi

echo "=== deploy-files → $DEST_DIR ==="
echo "  source: $SOC_ROOT"
echo "  mode:   $MODE (no-overwrite by default)"
if [[ -d "$DEST_DIR" ]]; then
  echo "  exists: $DEST_DIR — re-copying (no-overwrite; preserves existing target files)"
fi

# Build copy list: files git sees (tracked + untracked-not-ignored).
SKILL_EXCLUDE_REGEX='^(\.github/|\.gitignore$|\.gitattributes$|\.cursorrules$|scripts/deploy-files\.sh$|scripts/deploy-basic\.sh$|scripts/deploy-repo\.sh$)'

TMP_LIST="$(mktemp)"
MERGE_CANDS="$(mktemp)"
trap 'rm -f "$TMP_LIST" "$MERGE_CANDS"' EXIT

( cd "$SOC_ROOT" \
  && git ls-files --cached --others --exclude-standard \
  | grep -vE "$SKILL_EXCLUDE_REGEX" \
) > "$TMP_LIST"

COUNT="$(wc -l < "$TMP_LIST" | tr -d ' ')"

mkdir -p "$DEST_DIR"

# Pre-scan for no-overwrite modes.
SKIPPED=0
if [[ "$MODE" != "force" ]]; then
  while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if [[ -f "$DEST_DIR/$rel" ]]; then
      SKIPPED=$((SKIPPED+1))
      if [[ "$MODE" == "update" ]] && ! cmp -s "$SOC_ROOT/$rel" "$DEST_DIR/$rel"; then
        echo "$rel" >> "$MERGE_CANDS"
      fi
    fi
  done < "$TMP_LIST"
fi

if [[ "$MODE" == "force" ]]; then
  rsync -a --files-from="$TMP_LIST" "$SOC_ROOT"/ "$DEST_DIR"/
else
  rsync -a --ignore-existing --files-from="$TMP_LIST" "$SOC_ROOT"/ "$DEST_DIR"/
fi

COPIED=$((COUNT - SKIPPED))
echo "  copied: $COPIED files (git-ignored content excluded by policy)"
echo "  skipped (exists): $SKIPPED files"

if [[ "$MODE" == "update" ]] && [[ -s "$MERGE_CANDS" ]]; then
  MERGE_N="$(wc -l < "$MERGE_CANDS" | tr -d ' ')"
  echo ""
  echo "=== update merge candidates ($MERGE_N existing-but-differing files) ==="
  while IFS= read -r rel; do
    echo "  merge: $rel"
  done < "$MERGE_CANDS"
  echo "  (agent performs rules-aware merge: append new rules, update shared"
  echo "   sections, preserve target customizations; never wholesale-replace.)"
fi

echo ""
echo "=== Done: files deployed to $DEST_DIR ==="
echo ""
echo "Next steps in target project:"
echo "  1. Append SOC block to .cursorrules (run @deploy-basic or manually)"
echo "  2. Run @session-soc start"