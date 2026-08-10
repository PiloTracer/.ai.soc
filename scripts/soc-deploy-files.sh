#!/usr/bin/env bash
# soc-deploy-files.sh — Deploy .ai.soc files into a target project.
#
# Copies ONLY files git considers (tracked + untracked-not-ignored): anything
# in .gitignore — credentials, private context, tmp/ — is never deployed.
# This makes "files excluded in .git are never copied" an invariant enforced
# by construction, not a hand-maintained exclude list.
#
# Then strips skill-level intentional omissions (.github/, .gitignore,
# .gitattributes, .cursorrules).
#
# Default = NO-OVERWRITE: existing files in the target are skipped (target-side
# customizations are preserved by construction). Use force for the legacy
# idempotent-overwrite behavior, or update to additionally emit a candidate
# list of existing-but-differing files for agent-driven rules-aware merge.
#
# Argument normalization: verbs accept an optional `--` prefix and may appear
# in any position relative to the target path. The following are exactly
# equivalent:
#   soc-deploy-files.sh /path/to/target update
#   soc-deploy-files.sh /path/to/target --update
#   soc-deploy-files.sh --update /path/to/target
# Verbs without a path operate in-place (target = current directory).
#
# The in-place direction chains the .work.soc/ + .cursorrules scaffold via
# soc-deploy-basic.sh, which writes SOC_SOURCE pointing at the LOCAL deployed
# copy (<target>/.ai.soc) — fat-client deployments are self-contained — and
# ends with a verification pass of the target's .cursorrules.
#
# Source resolution: SOC_ROOT is derived from this script's location, so the
# script can be invoked from a TARGET directory using an external source .ai.soc:
#   bash /mnt/work/Projects/.ai.soc/scripts/soc-deploy-files.sh .
# Override the source with SOC_SOURCE=/abs/path/.ai.soc if needed.
#
# Usage:
#   bash scripts/soc-deploy-files.sh <target-path>               # no-overwrite (skip existing)
#   bash scripts/soc-deploy-files.sh <target-path> force         # overwrite existing (legacy)
#   bash scripts/soc-deploy-files.sh [target-path] update        # no-overwrite + emit merge candidates
#   SOC_SOURCE=/path/.ai.soc bash scripts/soc-deploy-files.sh <target-path>
#
set -euo pipefail

# --- Argument normalization --------------------------------------------------
# Verbs with or without `--`, in any position relative to the target path.
RAW_TARGET=""
MODE="skip"
while [[ $# -gt 0 ]]; do
  arg="$1"; shift
  word="${arg#--}"
  case "$word" in
    update) MODE="update" ;;
    force)  MODE="force" ;;
    *)
      if [[ "$arg" == --* ]]; then
        echo "ERROR: unknown flag: $arg" >&2
        echo "Usage: $0 [<target-path>] [update|force] (optional -- prefix)" >&2
        exit 1
      fi
      if [[ -n "$RAW_TARGET" ]]; then
        echo "ERROR: multiple target paths given: '$RAW_TARGET' and '$arg'" >&2
        exit 1
      fi
      RAW_TARGET="$arg"
      ;;
  esac
done
RAW_TARGET="${RAW_TARGET:-.}"

# Source .ai.soc root: explicit override wins, else derive from script location.
if [[ -n "${SOC_SOURCE:-}" ]]; then
  SOC_ROOT="$(cd "$SOC_SOURCE" && pwd)"
else
  SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Resolve target: if path ends with .ai.soc, use as-is; otherwise append .ai.soc
if [[ "$RAW_TARGET" == *.ai.soc ]]; then
  DEST_DIR="$(cd "$RAW_TARGET" 2>/dev/null && pwd || echo "$RAW_TARGET")"
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
  echo "  soc-deploy-files copies only git-tracked / non-ignored files (never .gitignored content)." >&2
  exit 1
fi

GIT_TOP="$(cd "$SOC_ROOT" && git rev-parse --show-toplevel)"
if [[ "$GIT_TOP" != "$SOC_ROOT" ]]; then
  echo "ERROR: $SOC_ROOT is not the git repo root (root is $GIT_TOP)." >&2
  echo "  soc-deploy-files expects the .ai.soc directory to be the repository root." >&2
  exit 1
fi

echo "=== soc-deploy-files → $DEST_DIR ==="
echo "  source: $SOC_ROOT"
echo "  mode:   $MODE (no-overwrite by default)"
if [[ -d "$DEST_DIR" ]]; then
  echo "  exists: $DEST_DIR — re-copying (no-overwrite; preserves existing target files)"
fi

# Build copy list: files git sees (tracked + untracked-not-ignored).
# Deploy scripts ARE included so a fat-client target can self-verify and
# self-update ($SOC_SOURCE/scripts/... resolves locally).
SKILL_EXCLUDE_REGEX='^(\.github/|\.gitignore$|\.gitattributes$|\.cursorrules$)'

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
  echo "  (agent performs rules-aware merge — append new sections, preserve target"
  echo "   customizations. See skill soc-deploy-basic/skill.md § update-merge.)"
fi

echo ""
echo "=== Done: files deployed to $DEST_DIR ==="
echo ""

# In-place direction (target is cwd): chain the .work.soc/ + .cursorrules
# scaffold. soc-deploy-basic detects the local skills copy and writes
# SOC_SOURCE pointing at it (fat-client = self-contained), then verifies.
TARGET_ROOT="$(cd "$PARENT" && pwd)"
if [[ "$RAW_TARGET" == "." || "$TARGET_ROOT" == "$PWD" ]]; then
  REPO_ROOT="$TARGET_ROOT" SOC_SOURCE="$SOC_ROOT" bash "$SOC_ROOT/scripts/soc-deploy-basic.sh" . \
    > /tmp/soc-deploy-files-scaffold.$$.log 2>&1 || { cat /tmp/soc-deploy-files-scaffold.$$.log; rm -f /tmp/soc-deploy-files-scaffold.$$.log; exit 1; }
  grep -E '(===|cursorrules:|work:|SOC block|Done:|verify|OK:|FAIL:|WARN:)' /tmp/soc-deploy-files-scaffold.$$.log | sed 's/^/  scaffold: /' || true
  rm -f /tmp/soc-deploy-files-scaffold.$$.log
  SCAFFOLD_DONE=1
fi

if [[ -n "${SCAFFOLD_DONE:-}" ]]; then
  echo "  Scaffold: .work.soc/ + SOC block in .cursorrules (SOC_SOURCE → local .ai.soc)"
  echo "  Next: @soc-session start"
else
  echo "Next steps in target project:"
  echo "  1. Run @soc-deploy-basic or append SOC block to .cursorrules"
  echo "  2. Run @soc-session start"
fi
