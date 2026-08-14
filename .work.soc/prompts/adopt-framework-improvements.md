# Adopt Framework Improvements (clarity contracts + audit)

**Status:** Approved · 2026-08-14 · **Portable:** yes — run inside any OS framework repo (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`)
**Needs:** execution in the target framework; no commit without explicit same-message approval.

Orchestrates the three portable prompts in this directory so a target OS
framework reaches the same state as Agent OS `.ai` (2026-08-14): operator
handoff contract, document clarity contract, and a verified-clean structure.

Referenced prompts (all paths target-relative, run from the target repo root):

1. `improve-clarity-of-responses.md` — Response Clarity Protocol (chat responses)
2. `improve-clarity-of-documentation.md` — Documentation Clarity Protocol (generated documents)
3. `framework-audit.md` — structural audit + adoption verification

## Prerequisites

- The three prompt files above are available to the agent (copied into the
  target's `.work/prompts/` or passed by path).
- Target repo has `skills/`, `skills/SKILL_DEPENDENCIES.md`, `.cursorrules`,
  and `templates/`. If any is missing, stop and report — do not improvise.

## Phase 1 — Operator handoff contract (per prompt 1)

1. Add `## Operator handoff contract` to `skills/SKILL_DEPENDENCIES.md`,
   canonically worded: terse output; approvals under `**Needs your
   approval:**` citing `path:L<n>`; questions numbered under `**Needs your
   answer:**`; exactly one `**Next step:**` command; Form A single line when
   nothing is needed; decisions and questions never mixed; empty sections
   omitted.
2. Every `skills/<id>/skill.md`: add a reference bullet to that contract;
   ensure every operator-facing report template closes with Form A or Form B.
3. Sync the target `.cursorrules` (Verification & Communication section) with
   the same closing requirement.
4. If the target has a skill verifier script, hard-fail on a missing contract
   reference; if not, record the enforcement gap for the Phase 3 report.

## Phase 2 — Document clarity contract (per prompt 2)

1. Add `## Document clarity contract` to `skills/SKILL_DEPENDENCIES.md`:
   Status/Needs header, separate Decisions / Open questions lists, exactly
   one `## Next action`, no leftover scaffolding.
2. Reference it from every doc-generating skill (plans, SPECs, ADRs, docs,
   reports).
3. Update the target's `templates/**` doc templates to carry the Status/Needs
   header and `## Next action`.
4. If the target has a verifier, fail doc-generating skills missing the
   reference; else record the gap.

## Phase 3 — Audit (per prompt 3)

Run `framework-audit.md` after Phases 1–2. It verifies the adoption (contract
sections present, every skill referencing them, templates synced) and sweeps
for structural drift. Findings go to
`.work/reports/YYYYMMDD-<framework>-audit.md`.

## Constraints

- One phase at a time, in order; do not start Phase N+1 while Phase N is
  unverified.
- Minimal diffs; no collateral edits; declare scope per the target's
  `.cursorrules` change-safety rules before editing.
- No `git commit`/`push` without explicit same-message approval.
- Do NOT copy or run `20260814-marker-detection-deploy-repo-removal-audit.md`
  in any target — it is `.ai`-only and already executed.

## Next action

Phase 1, step 1: add the Operator handoff contract section to the target's
`skills/SKILL_DEPENDENCIES.md`.
