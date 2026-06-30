#!/usr/bin/env bash
# Bootstrap .ai.soc into a repository root (run from repo root, not from inside .ai.soc/ only).
set -euo pipefail

SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${SOC_ROOT}/templates/work"

# Repo root: git root containing .ai.soc/
if [[ -d "${SOC_ROOT}/.git" ]]; then
  REPO_ROOT="${SOC_ROOT}"
elif [[ -d "${SOC_ROOT}/../.git" ]] && [[ -d "${SOC_ROOT}/templates" ]]; then
  REPO_ROOT="$(cd "${SOC_ROOT}/.." && pwd)"
else
  REPO_ROOT="${SOC_ROOT}"
fi

WORK="${REPO_ROOT}/.work.soc"

copy_if_missing() {
  local src="$1" dest="$2"
  if [[ -e "${dest}" ]]; then
    echo "  skip (exists): ${dest}"
  else
    mkdir -p "$(dirname "${dest}")"
    cp "${src}" "${dest}"
    echo "  created: ${dest}"
  fi
}

echo ".ai.soc bootstrap"
echo "  SOC_ROOT=${SOC_ROOT}"
echo "  REPO_ROOT=${REPO_ROOT}"
echo ""

mkdir -p "${WORK}"

copy_if_missing "${TPL}/README.md.template"          "${WORK}/README.md"
copy_if_missing "${TPL}/context/HANDOFF_SOC.md.template" "${WORK}/context/HANDOFF_SOC.md"
copy_if_missing "${TPL}/plans/NEXT_SOC.md.template"   "${WORK}/plans/NEXT_SOC.md"
copy_if_missing "${TPL}/plans/UNKNOWNS_SOC.md.template" "${WORK}/plans/UNKNOWNS_SOC.md"
copy_if_missing "${TPL}/analysis/README.md.template"  "${WORK}/analysis/README.md"

# Create output-sink dirs
for dir in assessments prompts decisions; do
  mkdir -p "${WORK}/${dir}"
  touch "${WORK}/${dir}/.gitkeep"
done

echo ""
echo "Next steps:"
echo "  1. Edit .work.soc/context/HANDOFF_SOC.md with your session state"
echo "  2. Edit .work.soc/plans/NEXT_SOC.md with your iteration plan"
echo "  3. Register .ai.soc in opencode.json if not already done"
echo "  4. Run @soc-assessment or custom SOC workflow"
echo ""
echo "Templates: ${SOC_ROOT}/templates/work/"
