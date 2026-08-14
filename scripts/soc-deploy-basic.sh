#!/usr/bin/env bash
# soc-deploy-basic.sh — Thin-client bootstrap of .ai.soc into a target project.
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
# update: no-overwrite + re-syncs the source pointer + lists existing-but-
# differing local-surface files as merge candidates for agent rules-aware merge.
# force: idempotent overwrite of the local scaffold surface only (legacy).
# verify: read-only audit of the target's deployed .cursorrules + .work.soc/
# (SOC_SOURCE correctness/reachability, stale skill handles, skeleton files,
# sister framework presence). Runs automatically after every deploy/update.
#
# Argument normalization: verbs accept an optional `--` prefix and may appear
# in any position relative to the target path. The following are exactly
# equivalent:
#   soc-deploy-basic.sh /path/to/target update
#   soc-deploy-basic.sh /path/to/target --update
#   soc-deploy-basic.sh --update /path/to/target
# Verbs without a path operate in-place (target = current directory).
#
# Source resolution: SOC_ROOT is derived from this script's location, so the
# script can be invoked from a TARGET using an external source .ai.soc:
#   bash /mnt/work/Projects/.ai.soc/scripts/soc-deploy-basic.sh /mnt/work/Projects/tools-project
# Override the source with SOC_SOURCE=/abs/path/.ai.soc if needed.
#
# Usage:
#   bash scripts/soc-deploy-basic.sh <target-path>               # no-overwrite (skip existing)
#   bash scripts/soc-deploy-basic.sh [target-path] status        # read-only report
#   bash scripts/soc-deploy-basic.sh [target-path] verify        # read-only audit (exit 1 on failure)
#   bash scripts/soc-deploy-basic.sh [target-path] update        # no-overwrite + merge candidate list
#   bash scripts/soc-deploy-basic.sh <target-path> force         # overwrite local scaffold (legacy)
#   SOC_SOURCE=/path/.ai.soc bash scripts/soc-deploy-basic.sh <target-path>
#
set -euo pipefail

# --- Argument normalization --------------------------------------------------
# Verbs with or without `--`, in any position relative to the target path.
RAW_TARGET=""
MODE="skip"
ACTION="deploy"
while [[ $# -gt 0 ]]; do
  arg="$1"; shift
  word="${arg#--}"
  case "$word" in
    status) ACTION="status" ;;
    verify) ACTION="verify" ;;
    update) MODE="update" ;;
    force)  MODE="force" ;;
    *)
      if [[ "$arg" == --* ]]; then
        echo "ERROR: unknown flag: $arg" >&2
        echo "Usage: $0 [<target-path>] [status|verify|update|force] (optional -- prefix)" >&2
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

# Target = repo root of the consumer.
if [[ ! -d "$RAW_TARGET" ]]; then
  echo "ERROR: target directory does not exist: $RAW_TARGET" >&2
  exit 1
fi
DEST_ROOT="$(cd "$RAW_TARGET" && pwd)"
CURS_DEST="${DEST_ROOT}/.cursorrules"

# --- Shared: fat/thin detection ----------------------------------------------
# Fat-client: target owns a local copy of the framework skills, either vendored
# under <target>/.ai.soc/ (soc-deploy-files) or AS the target itself when the
# target is a full .ai.soc repo root (soc-deploy-repo / the master repo).
LOCAL_SOC=""
detect_local_soc() {
  LOCAL_SOC=""
  if [[ -d "${DEST_ROOT}/.ai.soc/skills" ]]; then
    LOCAL_SOC="${DEST_ROOT}/.ai.soc"
  elif [[ -d "${DEST_ROOT}/skills" && -f "${DEST_ROOT}/templates/cursorrules.soc.snippet.template" ]]; then
    LOCAL_SOC="${DEST_ROOT}"
  fi
}

read_soc_source() {
  # Strip surrounding markdown/backtick/quote decoration from the raw value —
  # targets commonly write the pointer inline as `SOC_SOURCE=/path`.
  grep -oE 'SOC_SOURCE=[^ ]*' "$CURS_DEST" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '`"'"'" || true
}

# --- verify ------------------------------------------------------------------
# Read-only audit. Exit 0 when every hard check passes, 1 otherwise.
verify_target() {
  local errors=0
  detect_local_soc

  echo "=== soc-deploy verify → $DEST_ROOT ==="

  # 1. .cursorrules + SOC block
  if [[ ! -f "$CURS_DEST" ]]; then
    echo "  FAIL: .cursorrules missing"
    echo "verify: 1 error(s)"
    return 1
  fi
  echo "  OK:   .cursorrules present"
  if grep -q 'SOC_DESIGN_OS_BEGIN' "$CURS_DEST"; then
    echo "  OK:   SOC block present (SOC_DESIGN_OS_BEGIN/END)"
  else
    echo "  FAIL: SOC block missing — run: bash $SOC_ROOT/scripts/soc-deploy-basic.sh $DEST_ROOT"
    errors=$((errors + 1))
  fi

  # 2. Stale skill handles (pre-0.5.0 naming: session-soc / deploy-* without soc- prefix)
  # Scoped to the SOC block: sister frameworks (e.g. .ai) legitimately still
  # use bare `deploy-basic` skill names elsewhere in .cursorrules.
  local stale
  stale="$(sed -n '/SOC_DESIGN_OS_BEGIN/,/SOC_DESIGN_OS_END/p' "$CURS_DEST" 2>/dev/null | grep -oE '(^|[^A-Za-z-])(session-soc|deploy-basic|deploy-files|deploy-repo)' | sort -u | tr -d '[:space:]' | paste -sd, - || true)"
  if [[ -n "$stale" ]]; then
    echo "  FAIL: stale skill handles in SOC block ($stale) — pre-0.5.0 names; run update + rules-aware merge"
    errors=$((errors + 1))
  else
    echo "  OK:   no stale skill handles (soc-* naming)"
  fi

  # 3. SOC_SOURCE pointer vs thin/fat mode
  local src
  src="$(read_soc_source)"
  if [[ "$src" == "REPLACE_SOCSOURCE" ]]; then
    echo "  FAIL: SOC_SOURCE is still the REPLACE_SOCSOURCE placeholder"
    errors=$((errors + 1))
    src=""
  fi
  if [[ -n "$LOCAL_SOC" ]]; then
    # Fat-client: skills resolve locally.
    if [[ -z "$src" ]]; then
      echo "  OK:   SOC_SOURCE unset — fat-client local resolution ($LOCAL_SOC)"
    elif [[ "$src" == "$LOCAL_SOC" ]]; then
      echo "  OK:   SOC_SOURCE → local $LOCAL_SOC (fat-client, self-contained)"
    elif [[ -d "$src" ]]; then
      echo "  WARN: SOC_SOURCE → external $src but local skills exist (fat-client behaves thin)"
    else
      echo "  WARN: SOC_SOURCE unreachable ($src) — falls back to local $LOCAL_SOC"
    fi
    if [[ -f "${LOCAL_SOC}/skills/README.md" ]]; then
      echo "  OK:   local skills/README.md present"
    else
      echo "  FAIL: local skills/README.md missing under $LOCAL_SOC"
      errors=$((errors + 1))
    fi
  else
    # Thin-client: SOC_SOURCE must be set, reachable, and carry the skill registry.
    if [[ -z "$src" ]]; then
      echo "  FAIL: SOC_SOURCE unset and no local .ai.soc/skills/ — skills unresolvable"
      errors=$((errors + 1))
    elif [[ ! -d "$src" ]]; then
      echo "  FAIL: SOC_SOURCE unreachable: $src"
      errors=$((errors + 1))
    elif [[ ! -f "$src/skills/README.md" ]]; then
      echo "  FAIL: SOC_SOURCE has no skills/README.md: $src"
      errors=$((errors + 1))
    else
      echo "  OK:   SOC_SOURCE → $src (reachable, skills registry present)"
    fi
  fi

  # 4. .work.soc/ skeleton
  local wf missing=0
  for wf in context/HANDOFF_SOC.md plans/NEXT_SOC.md plans/UNKNOWNS_SOC.md; do
    if [[ ! -f "${DEST_ROOT}/.work.soc/${wf}" ]]; then
      echo "  FAIL: .work.soc/${wf} missing"
      errors=$((errors + 1))
      missing=1
    fi
  done
  [[ "$missing" -eq 0 ]] && echo "  OK:   .work.soc/ skeleton present (HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC)"

  # 5. SOC block sections (warn-level: older blocks may lack newer sections)
  local section
  for section in 'SOC context files' 'SOC placeholders' 'SOC skills' 'Data Loss Prevention'; do
    if grep -q "$section" "$CURS_DEST" 2>/dev/null; then
      echo "  OK:   section present: $section"
    else
      echo "  WARN: section missing: $section (older block — consider update)"
    fi
  done

  # 6. Sister frameworks (info-level): WORK_ROOT = parent of the .ai.soc repo
  local work_root=""
  if [[ -n "$LOCAL_SOC" ]]; then
    work_root="$(dirname "$LOCAL_SOC")"
  elif [[ -n "$src" && -d "$src" ]]; then
    work_root="$(dirname "$src")"
  fi
  if [[ -n "$work_root" ]]; then
    echo "  info: WORK_ROOT → $work_root"
    local fw
    for fw in .ai .ai.ui .ai.biz .ai.soc; do
      if [[ "$fw" == ".ai.soc" ]]; then continue; fi
      if [[ -f "$work_root/$fw/skills/README.md" ]]; then
        echo "  info: sister framework $fw: installed"
      else
        echo "  info: sister framework $fw: framework not installed here"
      fi
    done
  fi

  echo ""
  if [[ "$errors" -eq 0 ]]; then
    echo "verify: all checks passed ($DEST_ROOT)"
    return 0
  fi
  echo "verify: $errors error(s) — deploy is NOT coherent ($DEST_ROOT)"
  return 1
}

# --- status (read-only report) ------------------------------------------------
if [[ "$ACTION" == "status" ]]; then
  detect_local_soc
  echo "=== soc-deploy-basic status → $DEST_ROOT ==="
  if [[ -f "$CURS_DEST" ]]; then
    echo "  .cursorrules: present"
    if grep -q 'SOC_DESIGN_OS_BEGIN' "$CURS_DEST" 2>/dev/null; then
      echo "  SOC block: present"
    else
      echo "  SOC block: missing"
    fi
    src="$(read_soc_source)"
    if [[ -n "$src" && "$src" != "REPLACE_SOCSOURCE" ]]; then
      if [[ -d "$src" ]]; then echo "  SOC_SOURCE: $src (reachable)"; else echo "  SOC_SOURCE: $src (UNREACHABLE)"; fi
    else
      echo "  SOC_SOURCE: missing or unset"
    fi
  else
    echo "  .cursorrules: MISSING"
  fi
  [[ -d "${DEST_ROOT}/.work.soc/context" ]] && echo "  .work.soc/: present" || echo "  .work.soc/: missing"
  if [[ -n "$LOCAL_SOC" ]]; then
    echo "  local skills: present at $LOCAL_SOC (fat-client)"
  else
    echo "  local skills: absent (thin-client)"
  fi
  exit 0
fi

# --- verify action -------------------------------------------------------------
if [[ "$ACTION" == "verify" ]]; then
  verify_target
  exit $?
fi

# --- deploy / update ------------------------------------------------------------
TPL_CURS="${SOC_ROOT}/templates/cursorrules.soc.snippet.template"
TPL_WORK="${SOC_ROOT}/templates/work"

echo "=== soc-deploy-basic (thin-client) → $DEST_ROOT ==="
echo "  source: $SOC_ROOT"
echo "  mode:   $MODE (no-overwrite by default)"

detect_local_soc
# Fat-client targets point at their own local copy; thin-client targets at the source.
if [[ -n "$LOCAL_SOC" ]]; then
  INTENDED_SOURCE="$LOCAL_SOC"
  echo "  note:   local skills detected — fat-client pointer ($LOCAL_SOC)"
else
  INTENDED_SOURCE="$SOC_ROOT"
fi

# Pre-scan target .cursorrules for existing source pointer.
existing_source=""
if [[ -f "$CURS_DEST" ]]; then
  existing_source="$(read_soc_source)"
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
    cat "$TPL_CURS" | sed "s|REPLACE_SOCSOURCE|${INTENDED_SOURCE}|g"
  } >> "$CURS_DEST"
  echo "  cursorrules: appended SOC block (SOC_SOURCE=$INTENDED_SOURCE)"
}
append_soc_block

# Re-sync source pointer when --update and the existing pointer is stale.
if [[ "$MODE" == "update" ]] && [[ -n "$existing_source" ]] && [[ "$existing_source" != "$INTENDED_SOURCE" ]]; then
  if grep -q '^SOC_SOURCE=' "$CURS_DEST"; then
    sed -i "s#^SOC_SOURCE=.*#SOC_SOURCE=${INTENDED_SOURCE}#" "$CURS_DEST"
    echo "  cursorrules: re-synced SOC_SOURCE → $INTENDED_SOURCE (was: ${existing_source:-<unset>})"
  fi
fi

# Step 2: .work.soc/ skeleton via bootstrap.sh (no-overwrite).
BOOTSTRAP_SKIP_CURSERRULES=1 REPO_ROOT="$DEST_ROOT" bash "$SOC_ROOT/templates/bootstrap.sh" \
  > /tmp/soc-deploy-basic-bootstrap.$$.log 2>&1 || { cat /tmp/soc-deploy-basic-bootstrap.$$.log; rm -f /tmp/soc-deploy-basic-bootstrap.$$.log; exit 1; }
grep -E '(created:|skip )' /tmp/soc-deploy-basic-bootstrap.$$.log | sed 's/^/  work: /' || true
rm -f /tmp/soc-deploy-basic-bootstrap.$$.log

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
  echo "   customizations. See skill soc-deploy-basic/skill.md § update-merge.)"
fi

echo ""
echo "=== Done: thin-client bootstrap → $DEST_ROOT ==="
echo "  SOC block in .cursorrules: $(grep -q 'SOC_DESIGN_OS_BEGIN' "$CURS_DEST" 2>/dev/null && echo present || echo MISSING)"
echo "  SOC_SOURCE: $(read_soc_source || echo '<unset>')"
echo "  .work.soc/: $([ -d "${DEST_ROOT}/.work.soc" ] && echo present || echo MISSING)"

# Step 4: every deploy/update ends with a verification pass. A deploy that does
# not verify is reported as failed so the operator sees the gap immediately.
echo ""
if ! verify_target; then
  echo "ERROR: deploy completed but verification FAILED — see checks above." >&2
  exit 1
fi

echo ""
echo "Next steps in target project:"
echo "  1. Skills load from \$SOC_SOURCE at runtime (thin-client mode)"
echo "  2. Re-audit any time: bash $SOC_ROOT/scripts/soc-deploy-basic.sh verify $DEST_ROOT"
echo "  3. Run @soc-session start"
