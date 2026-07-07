#!/usr/bin/env bash
# install-git-hooks.sh — Install SOC OS git hooks alongside existing hooks.
#
# Each SOC hook is installed as <hook>.soc (e.g. pre-commit.soc) to coexist
# with sister frameworks (.ai, .ai.ui, .ai.biz) and the Python pre-commit
# framework. A dispatcher (.git/hooks/<hook>) is created only when no hook
# exists yet — existing hooks are never overwritten.
set -euo pipefail

SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Find .git directory
GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || true)"
if [ -z "$GIT_DIR" ] || [ ! -d "$GIT_DIR" ]; then
  if [ -d "${SOC_ROOT}/.git" ]; then
    GIT_DIR="${SOC_ROOT}/.git"
  elif [ -d "${SOC_ROOT}/../.git" ]; then
    GIT_DIR="$(cd "${SOC_ROOT}/.." && pwd)/.git"
  else
    echo "ERROR: no .git directory found" >&2
    exit 1
  fi
fi
HOOK_DEST="${GIT_DIR}/hooks"
mkdir -p "$HOOK_DEST"

HOOK_SRC="${SOC_ROOT}/hooks"
installed=0
created=0

for hook in pre-commit commit-msg post-commit prepare-commit-msg; do
  src="${HOOK_SRC}/${hook}.soc"
  soc_dest="${HOOK_DEST}/${hook}.soc"

  if [ ! -f "$src" ]; then
    echo "  skip (missing): ${src}"
    continue
  fi

  # Install SOC hook — never overwrite an existing .soc hook
  if [ -f "$soc_dest" ]; then
    if ! cmp -s "$src" "$soc_dest"; then
      echo "  skip (exists + differs): ${soc_dest}"
    else
      echo "  ok (already installed): ${soc_dest}"
    fi
    continue
  fi

  cp "$src" "$soc_dest"
  chmod +x "$soc_dest"
  installed=$((installed + 1))
  echo "  installed: ${soc_dest}"

  # Create dispatcher only if no hook exists yet
  dispatcher="${HOOK_DEST}/${hook}"
  if [ ! -f "$dispatcher" ] && [ ! -L "$dispatcher" ]; then
    cat > "$dispatcher" <<-DISP
	#!/bin/sh
	# Auto-generated dispatcher — chains .git/hooks/${hook}.* scripts.
	# This file was created by .ai.soc/scripts/install-git-hooks.sh.
	# Do not edit manually — remove it to let another framework create its own.
	for f in "\$(dirname "\$0")/${hook}."*; do
	  [ -x "\$f" ] || continue
	  "\$f" "\$@" || exit \$?
	done
	DISP
    chmod +x "$dispatcher"
    created=$((created + 1))
    echo "  created dispatcher: ${dispatcher}"
  fi
done

echo "SOC OS git hooks: ${installed} installed, ${created} dispatchers created in ${HOOK_DEST}"
echo "(Existing hooks were preserved — SOC hooks are named *.soc)"
