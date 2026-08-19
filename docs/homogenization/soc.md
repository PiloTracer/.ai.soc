# `.ai.soc` (Social OS) — upgrade directions for the deploy skills

**Status:** Ready · **Needs:** none · **Repo:** `/mnt/work/Projects/.ai.soc` (clean git, `.work/` present)

Goal: make the deploy skills produce targets whose `.cursorrules` discover all six sisters under both namings — same as the current framework. `.ai.soc` is the only sibling with an **active sister-presence check** — but it is hardcoded to 4 names and legacy-only.

## Current state (measured 2026-08-19)

- `scripts/soc-deploy-basic.sh` (369 L): `verify_target()` at `:109-230`; **sister loop at `:212-221`** hardcoded `for fw in .ai .ai.ui .ai.biz .ai.soc` (info-level, never fails the deploy); appends `templates/cursorrules.soc.snippet.template` with `REPLACE_SOCSOURCE` substituted (`:306`); source env `SOC_SOURCE`.
- `scripts/soc-deploy-files.sh` (191 L), `soc-deploy-repo.sh` (153 L): no sister logic.
- `scripts/install-git-hooks.sh:4-5`: prose mentions only `.ai`, `.ai.ui`, `.ai.biz`.
- `.cursorrules` `## Framework paths` at `:85-104`: `{WORK_ROOT}`-based table (`:95-100`, 4 rows: `.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`) + resolution rules (`:87-93`); no `WORK_ROOT:` line set anywhere, so it infers parent-of-repo.
- Templates: `cursorrules.soc.snippet.template` — **no framework-paths section** (deployed targets cannot route cross-framework).
- `scripts/framework-verify.sh` (127 L): no sister checks.

## Steps

### 1. Copy the discovery lib
```bash
cp /mnt/work/Projects/pilo.ai.logicbison/scripts/sister-discovery.sh scripts/sister-discovery.sh
```

### 2. `.cursorrules` — extend `## Framework paths` to seven rows (keep soc's own format)
Replace the 4-row table (`:95-100`) with:

```markdown
| Framework | Path | Director |
|-----------|------|----------|
| Security OS (`.ai.soc`) | *this repository* | `@soc-director` |
| Agent OS (`.ai`) | `{WORK_ROOT}/.ai` | `@ai-director` |
| UI Design OS (`.ai.ui`) | `{WORK_ROOT}/.ai.ui` | `@ui-director` |
| Business OS (`.ai.biz`) | `{WORK_ROOT}/.ai.biz` | `@biz-director` |
| CTO Professor OS (`.ai.cto`) | `{WORK_ROOT}/.ai.cto` | `@cto-director` |
| Flutter Agent OS (`.ai.flutter`) | `{WORK_ROOT}/.ai.flutter` | `@flutter-director` |
| MLT Agent OS (`.ai.mlt`) | `{WORK_ROOT}/.ai.mlt` | `@mlt-director` |
```

And add under the table (before `### Path resolution`):
```markdown
Family naming: sisters may also live as `pilo.ai.<fw>.logicbison` — the shared discovery rule (`scripts/sister-discovery.sh`) resolves both forms; family-named sources derive sisters as `<source basename with <fw> inserted before its last .segment>` (`.ai`-prefixed sources resolve `.ai.<fw>` directly).
```
Also update the inference bullet (`:88`): "Sibling frameworks (`.ai`, `.ai.ui`, `.ai.biz`) are then `{WORK_ROOT}/<framework>`" → "Sibling frameworks are then `{WORK_ROOT}/<framework>` (list below)."

### 3. `soc-deploy-basic.sh` — replace the hardcoded sister loop (`:212-221`) with the six-slot lib

> **Correction (operator, 2026-08-19):** the Agent OS anchor loop (`.ai` / `pilo.ai.logicbison`) shown below was **removed after landing** — a child framework does not track/contact the parent orchestrator. Only the six-slot sister loop applies; the anchor `for ag in ...` block must NOT be re-added.
Replace:
```bash
    local fw
    for fw in .ai .ai.ui .ai.biz .ai.soc; do
      if [[ "$fw" == ".ai.soc" ]]; then continue; fi
      if [[ -f "$work_root/$fw/skills/README.md" ]]; then
        echo "  info: sister framework $fw: installed"
      else
        echo "  info: sister framework $fw: framework not installed here"
      fi
    done
```
with:
```bash
    # Sister frameworks: the six .ai.<fw> slots (legacy + family naming via
    # sister-discovery.sh) + the Agent OS anchor (.ai / pilo.ai.logicbison).
    local fw fw_dir ag src_root
    src_root="${SOC_SOURCE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
    source "$(dirname "${BASH_SOURCE[0]}")/sister-discovery.sh"
    for fw in $FRAMEWORK_SLOTS; do
      fw_dir="$(find_sister_dir "$src_root" "$fw" "$work_root" || true)"
      if [[ -n "$fw_dir" ]]; then
        echo "  info: sister framework .ai.$fw: installed ($fw_dir)"
      else
        echo "  info: sister framework .ai.$fw: framework not installed here"
      fi
    done
    for ag in .ai pilo.ai.logicbison; do
      [[ -f "$work_root/$ag/skills/README.md" ]] && echo "  info: sister framework $ag: installed"
    done
```

### 4. Snippet template — add the framework-paths section (required for target routing)
In `templates/cursorrules.soc.snippet.template`, add the 7-row table (with `{WORK_ROOT}`/snippet tokens per the file's conventions) + the family-naming note, so snippet-merged targets can route cross-framework.

### 5. `install-git-hooks.sh:4-5` — refresh the prose to the seven frameworks.

### 6. Verify
```bash
source scripts/sister-discovery.sh
sister_names ui "$PWD"     # → .ai.ui
for s in biz cto flutter mlt soc ui; do test -f "../.ai.$s/skills/README.md" && echo "$s ok"; done
bash scripts/soc-deploy-basic.sh /tmp/smoke-soc     # output must list the six + .ai
bash scripts/framework-verify.sh
```

## Gaps found (include in a follow-up)

- Deployed targets get **no cross-framework routing** today: the snippet template lacks the framework-paths section (fixed by step 4).
- The sister check is **info-only and never fails** — consider promoting to a warn when a registry row points at a missing dir.
- `install-git-hooks.sh:4-5` prose lags (only `.ai`, `.ai.ui`, `.ai.biz`).
- `soc-director` is a scanner, not a router — cross-framework routing relies on `@x-director`, which is not vendored here (it ships only with `pilo.ai.logicbison`; until vendored, route cross-framework work through the Agent OS's `@x-director`).
- `.ai` row points at the old on-disk Agent OS snapshot; update when the family rename lands.

## Checklist
- [ ] `scripts/sister-discovery.sh` copied
- [ ] `## Framework paths` = 7 rows + family note (soc's `{WORK_ROOT}` format)
- [ ] `soc-deploy-basic.sh` six-slot loop (+ `.ai`/`pilo.ai.logicbison` anchors)
- [ ] Snippet template carries the framework table
- [ ] Verify commands pass
- [ ] Nothing committed/staged

## Next action
Run steps 1–2 + 6 inside `/mnt/work/Projects/.ai.soc`; steps 3–5 complete deploy parity.
