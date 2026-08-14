# Marker-file framework detection + deploy-repo removal + full framework audit

**Status:** Approved · 2026-08-14
**Needs:** execution per plan; no commit without explicit same-message approval.

> **`.ai`-only — already executed 2026-08-14.** Historical record of the Agent OS marker/deploy-repo/audit session. Do NOT copy to or run in sibling frameworks; the reusable audit procedure is `framework-audit.md`, orchestrated by `adopt-framework-improvements.md`.

Verify the 2026-08-14 changes (commits 29a668e, a12d69b) still pass all
verifiers, then:

1. `agent.os.framework.md` (repo root): fill with minimal identifying
   content (framework name, purpose, "never modify" notice); commit it;
   protect it in `standards/PROTECTED_SURFACES.json` and in §Protected
   Files of `.cursorrules` + `templates/cursorrules.template`.
   It is never modified thereafter.
2. deploy-* never deploy the marker:
   - `deploy-repo`: REMOVE the skill (`skills/deploy-repo/`) and
     `scripts/deploy-repo.sh` plus every reference (registries, routing
     docs, .cursorrules/template skills tables, verifier self-tests).
   - `deploy-files`: add explicit `agent.os.framework.md` exclusion to
     `scripts/deploy-files.sh` file-set pipeline + document the invariant
     in `skills/deploy-files/skill.md`.
   - `deploy-basic`: never copies root files already; add a one-line
     "marker never written" note.
3. session-control repo-mode detection = marker-only:
   framework source ⇔ root `agent.os.framework.md` exists; else consumer.
   Update `skills/session-control/skill.md` + `reference.md` (parse-table
   §Commit scope, C4b step 0, M5, edge cases, anti-patterns),
   `.cursorrules`, `templates/cursorrules.template`, and any other file
   performing the legacy check (deploy-basic source validation,
   project-bootstrap, ai-director, SKILL_DEPENDENCIES, skills/README).
4. Regression: `session-control start` behavior unchanged in both repo
   types (start performs no git writes; detection only affects commit
   scope).
5. Commit scopes unchanged: framework = whole repo; consumer = `.work/` +
   the three root general files. No new `add` verb — "add" means the
   staging step inside `commit`/`close commit`.
6. Review `.work/prompts/improve-clarity-of-{documentation,responses}.md`
   against the `skills/SKILL_DEPENDENCIES.md` contracts; fix drift/gaps,
   add Origin/Status header lines; sync contract text if semantics change.
7. Full framework audit: every skill vs SKILL_DEPENDENCIES contracts,
   registry congruence (.cursorrules skills table ↔ skills/README.md ↔
   SKILL_DEPENDENCIES.md ↔ skills/ dirs), routing docs (START_HERE.md,
   PROCESS_ROUTER.md, README.md), hooks, templates ↔ .cursorrules sync,
   PROTECTED_SURFACES coverage. Report to `.work/reports/`.

Constraints: MOD-06 required — run `concepts/ai-amplification/prompt.md`,
output `.work/analysis/20260814-mod06-*.md`; declare scope in
`.work/touch-scope` first; minimal diffs; no commit without explicit
same-message approval.

## Next action

Execute per the approved session plan (steps 0–11), starting with `.work/touch-scope` declaration and baseline verifier run.
