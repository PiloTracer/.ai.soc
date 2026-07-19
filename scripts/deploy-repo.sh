#!/usr/bin/env bash
# deploy-repo.sh — Full git-based deploy of .ai.soc into a target directory.
#
# Two modes:
#   clone   — git clone with full history into target dir (requires origin remote)
#   archive — git archive + extract into target dir (no git history, but includes
#             .github/, .gitignore, and root .cursorrules)
#
# "clone" is the default when the source has an origin remote and the target
# does not exist yet. "archive" is the fallback when there's no remote or the
# target exists and needs a partial update.
#
# Usage:
#   bash scripts/deploy-repo.sh --status [target-path]
#   bash scripts/deploy-repo.sh clone    /absolute/path/to/target
#   bash scripts/deploy-repo.sh archive  /absolute/path/to/target
#
set -euo pipefail

SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--status" || "${1:-}" == "status" ]]; then
  shift || true
  TARGET="${1:-}"
  echo "=== deploy-repo status (Security OS) ==="
  echo "  source: $SOC_ROOT"
  REMOTE="$(cd "$SOC_ROOT" && git remote get-url origin 2>/dev/null || true)"
  [[ -n "$REMOTE" ]] && echo "  origin: $REMOTE (clone available)" || echo "  origin: none (use archive mode)"
  echo "  branch: $(cd "$SOC_ROOT" && git branch --show-current 2>/dev/null || echo '?')"
  echo "  head: $(cd "$SOC_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo '?')"
  echo "  modes: clone | archive"
  if [[ -n "$TARGET" ]]; then
    T="$([ "$TARGET" = "." ] || [ "$TARGET" = "$PWD" ] && pwd || (cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET"))"
    echo ""
    echo "=== target: $T ==="
    [[ -e "$T" ]] && echo "  exists: yes" || echo "  exists: no"
    [[ -e "$T" ]] || exit 0
    [[ -d "$T/.git" ]] && echo "  .git/: present" || echo "  .git/: absent"
    [[ -f "$T/.cursorrules" ]] && echo "  .cursorrules: present" || echo "  .cursorrules: missing"
    [[ -d "$T/.github" ]] && echo "  .github/: present" || echo "  .github/: missing"
    [[ -d "$T/skills" ]] && echo "  skills/: present" || echo "  skills/: missing"
  fi
  exit 0
fi

MODE="${1:?Usage: $0 --status [path] | <clone|archive> <target-path>}"
RAW_TARGET="${2:?Usage: $0 <clone|archive> <target-path>}"

# Resolve target — use as-is (full repo deploy).
DEST_DIR="$RAW_TARGET"

PARENT="$(dirname "$DEST_DIR")"
if [[ ! -d "$PARENT" ]]; then
  echo "ERROR: parent directory does not exist: $PARENT" >&2
  exit 1
fi

echo "=== deploy-repo: $MODE → $DEST_DIR ==="

# Mode: clone
if [[ "$MODE" == "clone" ]]; then
  if [[ -d "$DEST_DIR/.git" ]]; then
    echo "  exists: $DEST_DIR (already a git repo — use 'archive' for partial update)" >&2
    exit 1
  fi

  REMOTE="$(cd "$SOC_ROOT" && git remote get-url origin 2>/dev/null || true)"
  if [[ -z "$REMOTE" ]]; then
    echo "ERROR: no git remote 'origin' in source repo $SOC_ROOT" >&2
    echo "  Cannot clone without a remote URL. Use 'archive' mode instead." >&2
    exit 1
  fi

  if [[ -e "$DEST_DIR" ]]; then
    echo "ERROR: $DEST_DIR already exists. Clone requires a non-existent or empty target." >&2
    exit 1
  fi

  git clone "$REMOTE" "$DEST_DIR"
  echo ""
  echo "=== Done: full repo cloned to $DEST_DIR ==="
  echo "Branch: $(cd "$DEST_DIR" && git branch --show-current)"
  echo "Origin: $REMOTE"
  exit 0
fi

# Mode: archive
if [[ "$MODE" != "archive" ]]; then
  echo "ERROR: unknown mode '$MODE'. Use 'clone' or 'archive'." >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
cd "$SOC_ROOT"

git archive --format=tar HEAD | tar xf - -C "$DEST_DIR"

echo ""
echo "=== Done: repo archive deployed to $DEST_DIR ==="
echo "Includes: .github/, .gitignore, .cursorrules (full tree, no .git history)"
echo ""
echo "Next steps in target project:"
echo "  1. Initialize git: git init && git add . && git commit -m 'init: .ai.soc'"
echo "  2. Set origin remote if needed"
echo "  3. When co-installed with Agent OS, register skills via parent .ai/opencode.json"
