---
name: soc-deploy-basic
description: >-
  Thin-client bootstrap of .ai.soc into a target project. Copies ONLY the
  minimal scaffold — .cursorrules SOC block (with SOC_SOURCE pointer to the
  source .ai.soc), .work.soc/ skeleton (HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC,
  README, analysis, dirs). Framework assets (skills, scripts, templates)
  are NOT copied; the agent resolves them from the source
  .ai.soc at runtime per SOC_SOURCE pointer. Use soc-deploy-basic (default),
  soc-deploy-basic update, soc-deploy-basic status, or soc-deploy-basic - source <path>
  / soc-deploy-basic - target <path>. Never modifies the source.
  Contrast with soc-deploy-files (full fat-client copy of .ai.soc/).
  Every deploy/update ends with a `verify` pass auditing the target's
  .cursorrules (SOC_SOURCE, stale skill handles, skeleton, sister frameworks).
  Arguments are normalized: verbs accept an optional `--` prefix and may
  appear before or after the target path — `soc-deploy-basic /path update`
  is exactly equivalent to `soc-deploy-basic /path --update`.
---

# soc-deploy-basic

Thin-client deploy of the `.ai.soc` framework. The target project receives only the scaffold it owns (`.cursorrules` SOC block, `.work.soc/`); everything else (skills, scripts, templates) stays in the **source** `.ai.soc` and is loaded on demand via the `SOC_SOURCE` pointer written into `.cursorrules`.

**Shell:** `bash <source>/scripts/soc-deploy-basic.sh <target-path> [mode]`

**Canonical path:** `.ai.soc/skills/soc-deploy-basic/skill.md` · **Shell:** `.ai.soc/scripts/soc-deploy-basic.sh`

**Operator handoff:** every response that ends a turn follows the [Operator handoff contract](../SKILL_DEPENDENCIES.md#operator-handoff-contract) — terse output; approvals under `**Needs your approval:**` citing `path:L<n>`; questions numbered under `**Needs your answer:**`; exactly one `**Next step:**` command; one line when nothing is needed (Form A). Decisions and questions never mixed; empty sections omitted.

**Source not modified.** soc-deploy-basic only writes to the **target**. The source `.ai.soc` is read-only.

**Contrast with `soc-deploy-files`:** `soc-deploy-files` = **fat-client** (vendored full `.ai.soc/` into target, skills are local). `soc-deploy-basic` = **thin-client** (skills remote in source). Choose:
- `soc-deploy-files` — you want the framework files versioned inside the project, offline-editable, no external dependency.
- `soc-deploy-basic` — you want the project to track the live source framework, share one source of truth across many consumer repos.

---

## Two scenarios

| # | User location | Source | Target | Invocation |
|---|---------------|--------|--------|------------|
| 1 | Target project (e.g. `/mnt/work/Projects/tools-project`) | Explicit source path | `cwd` | `@soc-deploy-basic - source /mnt/work/Projects/.ai.soc` |
| 2 | Source `.ai.soc` directory | `cwd` (implied) | Explicit target path | `@soc-deploy-basic - target /mnt/work/Projects/tools-project` |

In both scenarios, the source `.ai.soc` is never modified. Only the target receives changes.

---

## Parse invocation

**Argument normalization:** verbs accept an optional `--` prefix, the target path may appear before or after the verb, and quoting the path is optional. The following are **exactly equivalent** — parse them to the same shell invocation:

```text
@soc-deploy-basic "/mnt/work/Projects/system-erp" update
@soc-deploy-basic /mnt/work/Projects/system-erp --update
@soc-deploy-basic --update /mnt/work/Projects/system-erp
```

| User says | Direction | Mode |
|-----------|-----------|------|
| `@soc-deploy-basic` | auto-detect | bootstrap (no-overwrite); if SOC_SOURCE already in .cursorrules → re-run in-place |
| `@soc-deploy-basic - source /path/to/.ai.soc` | in-place (cwd is target) | bootstrap from explicit source |
| `@soc-deploy-basic - target /path/to/project` | outbound (cwd is source) | bootstrap into explicit target |
| `@soc-deploy-basic update` (= `--update`) | in-place | no-overwrite + re-sync source pointer + agent merge candidates + verify |
| `@soc-deploy-basic status` (= `--status`) | report | read-only: SOC block presence, source reachability, .work.soc/ structure |
| `@soc-deploy-basic verify` (= `--verify`) | audit | read-only audit of target `.cursorrules` + `.work.soc/`; exit 1 on any hard failure |

**Default:** `status` if no verb matches.

**Target path is REQUIRED when invoked from the source directory (Scenario #2).** The shell aborts with a usage message if no `<target-path>` is supplied; prompt the user for it rather than guessing. When invoked in-place (target is cwd), the path is implicit and no argument is needed (the skill resolves `SOC_SOURCE` from the target's `.cursorrules` or the explicit `source` argument).

---

## What gets copied (the local surface)

| Path | Source | If target exists |
|------|--------|-------------------|
| `.cursorrules` SOC block | `templates/cursorrules.soc.snippet.template` with `SOC_SOURCE=<source>` substituted | Append block if missing; preserve existing SOC block |
| `.work.soc/README.md` | `templates/work/README.md.template` | skip (preserve) |
| `.work.soc/context/HANDOFF_SOC.md` | `templates/work/context/HANDOFF_SOC.md.template` | skip (preserve) |
| `.work.soc/plans/NEXT_SOC.md` | `templates/work/plans/NEXT_SOC.md.template` | skip (preserve) |
| `.work.soc/plans/UNKNOWNS_SOC.md` | `templates/work/plans/UNKNOWNS_SOC.md.template` | skip (preserve) |
| `.work.soc/analysis/README.md` | `templates/work/analysis/README.md.template` | skip (preserve) |
| `.work.soc/{assessments,decisions,prompts}/.gitkeep` | created empty | skip (preserve) |

**Explicitly NOT copied (stay in source, loaded at runtime):** `skills/**`, `scripts/**`, `templates/**`, `README.md`, `START_HERE.md`, `.github/`, `.gitignore`, `.gitattributes`.

---

## I0 — Pre-checks

| Condition | Action |
|-----------|--------|
| Source `templates/cursorrules.soc.snippet.template` missing | **Block**: source is not a valid `.ai.soc` framework root |
| Target dir does not exist | **Block**: report missing path |
| Target already has local `.ai.soc/skills/` | Warn fat-client leak: target was previously bootstrapped fat; thin-client would duplicate. Ask user to confirm intent. |
| Target `.cursorrules` exists + lacks `SOC_DESIGN_OS_BEGIN` block | In `update` mode → flag as **MERGE CANDIDATE**; in default mode → append block |

---

## I1 — Bootstrap protocol

1. Resolve source `SOC_ROOT` (explicit `- source <path>`, `SOC_SOURCE` env, or script's parent). Validate `templates/cursorrules.soc.snippet.template` exists.
2. Resolve target = `REPO_ROOT` of the consumer (cwd for in-place, or named path for outbound).
3. Append SOC block to target `.cursorrules` from the snippet template, substituting `REPLACE_SOCSOURCE` → the intended pointer (`SOC_SOURCE=<absolute SOC_ROOT>` for thin targets; `SOC_SOURCE=<target>/.ai.soc` when the target owns a local skills copy). **No-overwrite** if SOC block already present. The block adds the `SOC_SOURCE` pointer line, SOC context table, SOC placeholders, and SOC skills table.
4. Run the `.work.soc/` scaffold via `REPO_ROOT=<target> bash <source>/templates/bootstrap.sh` (bootstrap's `copy_if_missing` enforces no-overwrite).
5. Report: `SOC_SOURCE` pointer value, `.work.soc/` presence, fat-client leak check, next steps.

**Idempotent re-run.** Safe to re-run; no-overwrite preserves target customizations.

---

## I2 — update-merge protocol (`@soc-deploy-basic update` only)

After I1 (no-overwrite) the skill:

1. **Re-syncs the source pointer** if the target `.cursorrules` carries a stale `SOC_SOURCE` value. Performed in-place on the assignment line only — preserves all other target edits.
2. **Lists merge candidates** among the local surface: existing-but-differing files vs the current source templates.
3. The **agent** then performs a rules-aware merge per candidate.

### Merge rules per file class

| Class | Merge rule |
|-------|------------|
| `.cursorrules` SOC block | Update framework sections (Skills table, Source resolution, Context files, **Data Loss Prevention**). Preserve target customizations. Never wholesale-replace. |
| `.work.soc/<file>` | Append new template sections absent in target; **preserve all user content** (HANDOFF rows, NEXT iteration blocks, UNKNOWNS entries). |
| `.work.soc/<dir>/.gitkeep` + new scaffold dirs | Create any NEW scaffold dir that didn't exist; do not touch existing. |

### Preserve invariants (never drop)
- Target's filled content in `.work.soc/` files (HANDOFF dates, NEXT tasks, UNKNOWNS entries).
- Target's `SOC_SOURCE` line, in-place value (synced, not reset to `REPLACE_SOCSOURCE`).
- Target's **Data Loss Prevention** section in the SOC block (git / files / databases rules + per-case permission scope) — merge forward from source template if missing; never delete.
- Target's git history, `.gitignore`, app code — all untouched.

---

## I3 — status (read-only)

Reports:

| Check | Output |
|-------|--------|
| `SOC_DESIGN_OS_BEGIN` block present in `.cursorrules` | pass / missing |
| `SOC_SOURCE` value + reachable | value + `test -d` result |
| `.work.soc/` present | pass / missing (list present skeleton files) |
| Local `.ai.soc/skills/` exists (fat-client leak) | no (good, thin) / yes (warn — mixed) |

---

## I4 — verify (read-only audit)

`bash <source>/scripts/soc-deploy-basic.sh verify [target-path]` audits a deployed target. **Every deploy/update run ends with this pass automatically** — a deploy that does not verify exits non-zero.

Hard checks (failure → exit 1):

| Check | Pass condition |
|-------|----------------|
| `.cursorrules` + SOC block | File exists; `SOC_DESIGN_OS_BEGIN` marker present |
| Stale skill handles | No pre-0.5.0 handles (`session-soc`, `deploy-basic/-files/-repo` without `soc-` prefix) |
| `SOC_SOURCE` pointer | Not the `REPLACE_SOCSOURCE` placeholder. **Thin-client:** set, reachable, `$SOC_SOURCE/skills/README.md` present. **Fat-client** (local `.ai.soc/skills/` exists): unset, or pointing at the local copy |
| `.work.soc/` skeleton | `context/HANDOFF_SOC.md`, `plans/NEXT_SOC.md`, `plans/UNKNOWNS_SOC.md` present |

Soft checks (reported, never fail): SOC block sections present (`SOC context files`, `SOC placeholders`, `SOC skills`, `Data Loss Prevention`) — missing ones mean an older block, suggest `update`; sister frameworks (the six `.ai.<fw>` slots — `ui`, `biz`, `cto`, `flutter`, `mlt`, `soc` — via `scripts/sister-discovery.sh`, which resolves both legacy `.ai.<fw>` and family `pilo.ai.<fw>.logicbison` naming) under the resolved `WORK_ROOT` — reported as `installed` / `framework not installed here`. The parent orchestrator (`.ai` / `pilo.ai.logicbison`) is deliberately not checked — child frameworks don't track the parent.

Fat-client pointer rule: when the target owns local skills, `SOC_SOURCE` must be unset or equal `<target>/.ai.soc` so the deployment is self-contained. `update` re-syncs a stale pointer to the intended value (local copy for fat targets, source path for thin targets).

Use verify after any deploy/update, after moving the source `.ai.soc`, and whenever an operator asks "read .cursorrules" in a target project — it confirms the block is coherent before any SOC work starts.

---

## Completion

| # | Check | Result |
|---|-------|--------|
| 1 | Source `templates/cursorrules.soc.snippet.template` readable | pass |
| 2 | Target `.cursorrules` has `SOC_DESIGN_OS_BEGIN` block with valid `SOC_SOURCE` | |
| 3 | `.work.soc/` skeleton present (HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC at minimum) | |
| 4 | No-overwrite honored | |
| 5 | `update`: source pointer re-synced if stale; merge candidate list produced | |
| 6 | Fat-client leak checked | |
| 7 | User informed that skills load from `$SOC_SOURCE` at runtime | |
| 8 | `verify` pass ran at end of deploy/update; zero hard failures | |

## Next commands (in target project)

```text
# Verify the source is reachable:
test -d "$(grep -oE 'SOC_SOURCE=[^ ]*' .cursorrules | head -1 | cut -d= -f2-)"

# First SOC skill invocation — loads from source:
@soc-session start
```

End every bootstrap/update/status/verify report with the Operator handoff close (Form A `Next: …` or Form B `**Needs your approval:**` / `**Needs your answer:**` / `**Next step:**`) per `skills/SKILL_DEPENDENCIES.md`. Any operator-required decision (fat-client leak choice, merge candidates) must ALSO appear in the closing block, enumerated with `path:line`, not only in the report body. When a command is required, carry exactly one in `**Next step:**` — the immediate one.

---

## Critical interactions

| When | Ask / do |
|------|----------|
| Invoked from target with no source pointer yet | Chicken-and-egg escape: invoke the shell directly: `bash /abs/path/to/source/scripts/soc-deploy-basic.sh .` |
| Bootstrap target already has `.ai.soc/skills/` (fat-client) | Warn; ask: convert to thin (delete local `.ai.soc/`)?, keep mixed?, or abort? |
| `update` finds `.cursorrules` with no `SOC_SOURCE` line | Flag as merge candidate; agent appends the SOC block with current source value. |
| Source moved since last bootstrap | `update` re-syncs the pointer in-place; report old→new. If source unreachable, stop. |

---

## Anti-patterns

- Copying `skills/`/`scripts/` into the target (defeats thin-client; use `@soc-deploy-files`).
- Wholesale-replacing `.cursorrules` or `.work.soc/` files on `update`.
- Resetting `SOC_SOURCE` to `REPLACE_SOCSOURCE` instead of the resolved path.
- Running `@soc-deploy-basic` and expecting skills to work offline — thin-client requires the source path to remain reachable.
- Invoking `@soc-deploy-basic - target /path` from the source dir **without** a target path.
- Modifying the source `.ai.soc/` during deploy.
