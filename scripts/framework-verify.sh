#!/usr/bin/env bash
# framework-verify.sh — Self-verification for Security OS (.ai.soc) framework layer
set -euo pipefail

SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SOC_ROOT"

errors=0
note() { echo ""; echo "==> $1"; }
ok() { echo "    OK: $1"; }
die() { echo "    FAIL: $1"; errors=$((errors + 1)); }

echo "=== Security OS Framework Verify ==="

note "Required tools"
for cmd in git rsync bash grep find; do
  command -v "$cmd" &>/dev/null && ok "$cmd" || die "missing $cmd"
done

note "Git repo"
git rev-parse --is-inside-work-tree &>/dev/null && ok "inside git work tree" || die "not a git repository"

note "Core framework files"
for f in README.md START_HERE.md templates/bootstrap.sh \
  scripts/soc-deploy-basic.sh scripts/soc-deploy-files.sh scripts/soc-deploy-repo.sh \
  skills/README.md; do
  [[ -f "$SOC_ROOT/$f" ]] && ok "$f" || die "missing $f"
done

note "Agent skills"
skill_count=0
while IFS= read -r d; do
  id="$(basename "$d")"
  skill_count=$((skill_count + 1))
  [[ -f "$d/skill.md" ]] || die "skills/${id}/skill.md missing"
  grep -qE "^\| ${id} " "$SOC_ROOT/skills/README.md" || die "skills/${id} not in skills/README.md"
done < <(find "$SOC_ROOT/skills" -mindepth 1 -maxdepth 1 -type d ! -name '.*' | sort)
ok "${skill_count} skills present"

note "Clarity contracts (operator handoff)"
if grep -q '^## Operator handoff contract' "$SOC_ROOT/skills/SKILL_DEPENDENCIES.md"; then
  ok "SKILL_DEPENDENCIES.md has Operator handoff contract"
else
  die "skills/SKILL_DEPENDENCIES.md missing '## Operator handoff contract'"
fi
while IFS= read -r d; do
  id="$(basename "$d")"
  if grep -q "Operator handoff" "$d/skill.md" 2>/dev/null; then
    ok "skills/${id} references Operator handoff contract"
  else
    die "skills/${id}/skill.md missing Operator handoff contract reference"
  fi
done < <(find "$SOC_ROOT/skills" -mindepth 1 -maxdepth 1 -type d ! -name '.*' | sort)

note "Clarity contracts (document clarity)"
if grep -q '^## Document clarity contract' "$SOC_ROOT/skills/SKILL_DEPENDENCIES.md"; then
  ok "SKILL_DEPENDENCIES.md has Document clarity contract"
else
  die "skills/SKILL_DEPENDENCIES.md missing '## Document clarity contract'"
fi
DOC_GENERATING="soc-session"
for id in $DOC_GENERATING; do
  if grep -q "Document clarity" "$SOC_ROOT/skills/${id}/skill.md" 2>/dev/null; then
    ok "skills/${id} references Document clarity contract"
  else
    die "skills/${id}/skill.md (doc-generating) missing Document clarity contract reference"
  fi
done
note "Doc template headers (Status/Needs + Next action)"
tpl_errors=0
for t in templates/work/context/HANDOFF_SOC.md.template \
  templates/work/plans/NEXT_SOC.md.template \
  templates/work/plans/UNKNOWNS_SOC.md.template \
  templates/work/analysis/README.md.template \
  templates/work/README.md.template; do
  if [[ -f "$SOC_ROOT/$t" ]]; then
    grep -q "Status:" "$SOC_ROOT/$t" && grep -q "Needs:" "$SOC_ROOT/$t" \
      && ok "$t carries Status/Needs header" \
      || { die "$t missing Status/Needs header"; tpl_errors=$((tpl_errors + 1)); }
    grep -qE '^## Next action$|^Next action: none' "$SOC_ROOT/$t" \
      && ok "$t carries Next action" \
      || { die "$t missing '## Next action'"; tpl_errors=$((tpl_errors + 1)); }
  else
    die "missing $t"
  fi
done

note "Change-safety gate scripts"
for check in touch-scope-verify blast-radius-check gate-verify; do
  script="${SOC_ROOT}/scripts/${check}.sh"
  if [[ -f "$script" ]]; then
    bash "$script" --self-test >/dev/null && ok "${check}.sh self-test" || die "${check}.sh self-test failed"
  else
    die "missing scripts/${check}.sh"
  fi
done

note "soc-deploy-files in-place scaffold"
DF_SMOKE="$(mktemp -d)"
pushd "$DF_SMOKE" >/dev/null
bash "$SOC_ROOT/scripts/soc-deploy-files.sh" . >/dev/null
[[ -d .ai.soc/skills ]] || die "soc-deploy-files in-place missing .ai.soc/skills"
[[ -f .work.soc/context/HANDOFF_SOC.md ]] || die "soc-deploy-files in-place missing .work.soc/context/HANDOFF_SOC.md"
grep -q 'SOC_DESIGN_OS_BEGIN' .cursorrules 2>/dev/null || die "soc-deploy-files in-place missing SOC block in .cursorrules"
popd >/dev/null
ok "soc-deploy-files in-place creates .ai.soc/ + .work.soc/ + SOC block"

note "soc-deploy-repo --status"
bash "$SOC_ROOT/scripts/soc-deploy-repo.sh" --status >/dev/null
bash "$SOC_ROOT/scripts/soc-deploy-repo.sh" --status "$DF_SMOKE" >/dev/null
ok "soc-deploy-repo --status reports source + target"
rm -rf "$DF_SMOKE"

note "soc-deploy-basic thin-client scaffold"
DB_SMOKE="$(mktemp -d)"
bash "$SOC_ROOT/scripts/soc-deploy-basic.sh" "$DB_SMOKE" >/dev/null
grep -q 'SOC_DESIGN_OS_BEGIN' "${DB_SMOKE}/.cursorrules" && ok "soc-deploy-basic appends SOC block" || die "soc-deploy-basic SOC block missing"
[[ -d "${DB_SMOKE}/.work.soc" ]] && ok "soc-deploy-basic creates .work.soc/" || die "soc-deploy-basic .work.soc missing"
rm -rf "$DB_SMOKE"

echo ""
if [[ "$errors" -eq 0 ]]; then
  echo "framework-verify: all checks passed"
else
  echo "framework-verify: $errors error(s)"
fi
exit "$errors"
