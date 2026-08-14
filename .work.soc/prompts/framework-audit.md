# Framework Audit (portable)

**Status:** Approved · 2026-08-14 · **Portable:** yes — run inside any OS framework repo (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`)
**Needs:** execution + a written report; fixes only with explicit same-message approval.

Structural audit of an OS framework repo. Verifies clarity-contract adoption
(see `adopt-framework-improvements.md`) and sweeps for drift. Read-only by
default: produce findings with evidence; apply fixes only when the operator
approves them in the same message.

## Checks

1. **Registry congruence** — `.cursorrules` skills table ↔ `skills/README.md`
   ↔ `skills/SKILL_DEPENDENCIES.md` ↔ actual `skills/<id>/` directories.
   Every skill registered in all places, or flagged.
2. **Operator handoff adoption** — `skills/SKILL_DEPENDENCIES.md` contains
   `## Operator handoff contract`; every `skills/<id>/skill.md` references it;
   every operator-facing report template closes with Form A (`Next: …`) or
   Form B (`**Needs your approval:**` / `**Needs your answer:**` /
   `**Next step:**`).
3. **Document clarity adoption** — `## Document clarity contract` present;
   every doc-generating skill references it; `templates/**` doc templates
   carry a Status/Needs header and exactly one `## Next action`.
4. **Routing docs** — `START_HERE.md`, `PROCESS_ROUTER.md`, `README.md` (and
   equivalent entry docs) reference only skills and files that exist.
5. **Templates ↔ .cursorrules sync** — paths and rules in `.cursorrules`
   match the cursorrules template and the real directory layout.
6. **Hooks** — mandated git hook scripts present and executable; no stale
   references to removed scripts.
7. **Protected surfaces** — protected-files lists (JSON + `.cursorrules`
   section) cover the framework's high-blast paths; no path protected in one
   list but missing from the other.
8. **Verifiers** — if the repo has verify scripts, run them and record exit
   codes. A missing verifier is a finding, not a pass.

## Report

Write `.work/reports/YYYYMMDD-<framework>-audit.md` with: scope, per-check
pass/fail with evidence (`path:L<n>`), findings classified
`confirmed` | `inference` | `unknown`, and a proposed fix list (not applied).

## Constraints

- Minimal diffs on approved fixes; no collateral edits.
- No `git commit`/`push` without explicit same-message approval.

## Next action

Check 1: diff the skill registries against the actual `skills/` directories.
