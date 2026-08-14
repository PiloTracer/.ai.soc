# soc-session — reference

Supplement to `skill.md`. Invocation examples, HANDOFF_SOC templates, detailed protocols, and edge cases. Behavioral mirror of `.ai/skills/session-control/reference.md`, with SOC commit scope (see skill.md § Commit scope): full repo in framework-mode, `.work.soc/` only in target-mode.

---

## Invocation examples

| Action | Prompt |
|--------|--------|
| Open | `@soc-session` **start** |
| Open + goal | `soc-session` **start** - audit deploy skills |
| Close | `@soc-session` **close** |
| Close + commit (all safe `.work.soc/` changes incl. new files) | `soc-session` **close** **commit** |
| Close + commit (HANDOFF_SOC/NEXT_SOC only) | `soc-session` **close** **commit** **scoped** |
| Close + commit + push | `soc-session` **close** **commit** **push** |
| **Commit only (no close)** | `@soc-session` **commit** |
| **Commit + push (no close)** | `soc-session` **commit** **push** |
| **Full context load (no writes, uncommitted-aware)** | `@soc-session` **context** |
| Load check | `@soc-session` **status** |

Legacy aliases still work: `begin`, `open`, `end`, `handoff`.

### Close modifiers (git)

| Invocation | Commit? | Push? | Commit message in report | Closes session? |
|------------|---------|-------|---------------------------|-----------------|
| `close` | no | no | **always** (draft) | yes |
| `close commit` | yes | no | **always** (used + SHA if ok) | yes |
| `close commit scoped` | yes | no | **always** (used + SHA if ok) | yes |
| `close commit push` | yes | yes | **always** (used + push result) | yes |
| `close push` | yes | yes | same as `close commit push` | yes |
| `commit` | yes | no | **always** (used + SHA if ok) | **no** |
| `commit push` | yes | yes | **always** (used + push result) | **no** |

Default `close` never runs `git commit` or `git push`. The operator runs git manually from the drafted message if they want.

**`close commit` / `commit` default scope:** stage all **safe** changes in scope from `git status --porcelain`, **including new untracked files/dirs** — **not** HANDOFF_SOC/NEXT_SOC only. Scope is mode-dependent (skill.md § Commit scope): **framework-mode** (running inside the `.ai.soc` source repo) → the **full repo** (`git add -A` after the secrets scan); **target-mode** (deployed project) → **`.work.soc/` only** (`git add .work.soc/`). Agent **must** run shell `git add` + `git commit` and show SHA + post-commit `git status -sb`. See [§ Close protocol (detailed)](#close-protocol-detailed) (C4b).

**Standalone `commit` / `commit push`:** same git behavior as `close commit` / `close commit push` but **skips** HANDOFF_SOC and NEXT_SOC updates. Session stays open.

---

## Mode comparison

| | start | status | context | close | close commit | close commit push | **commit** | **commit push** |
|---|-------|--------|---------|-------|--------------|-------------------|-----------|----------------|
| Read HANDOFF_SOC/NEXT_SOC | yes | yes | yes | yes | yes | yes | **no** | **no** |
| Update HANDOFF_SOC | Open | no | no | Closed | Closed | Closed | **no** | **no** |
| Update NEXT_SOC/UNKNOWNS_SOC | no | no | no | yes | yes | yes | **no** | **no** |
| `git commit` | no | no | no | no | yes | yes | **yes** | **yes** |
| `git push` | no | no | no | no | no | yes | **no** | **yes** |
| Commit message in output | no | no | no | **always** | **always** | **always** | **always** | **always** |
| Completion checklist | yes | no | no | yes | yes | yes | **yes** | **yes** |
| Task ref auto-detected | yes | no | no | yes | yes | yes | **yes** | **yes** |

---

## HANDOFF_SOC — Session status templates

`{HANDOFF_SOC}` carries a `## Session status` block (see `templates/work/context/HANDOFF_SOC.md.template`). Two header shapes exist in the wild; update whichever the file uses.

### Template shape (preferred)

Open (after start):

```markdown
## Session status

**Open:** 2026-08-14 - goal: audit deploy skills

**Updated:** 2026-08-14

**Closed:** -
```

Closed (after close):

```markdown
## Session status

**Open:** -

**Updated:** 2026-08-14

**Closed:** 2026-08-14 - deploy-skill audit landed; live E2E still outstanding
```

### Legacy header shape (this repo's HANDOFF_SOC)

Open (after start):

```markdown
**Session:** SOC-014 - <goal>
**Date:** 2026-08-14
**Status:** Open
```

Closed (after close):

```markdown
**Session:** SOC-014 - <goal>
**Date:** 2026-08-14
**Status:** Closed - <one-line outcome>
```

Treat the next chat as a **new session**: do not assume unwritten goals from prior threads unless they appear in HANDOFF_SOC or linked artifacts.

---

## Git commands reference

| Purpose | Command |
|---------|---------|
| Short status | `git status -sb` |
| Close audit | `git status` + `git diff --stat` + `git diff --cached --stat` |
| After commit | `git log -1 --oneline` |
| Split advice | `git diff --name-only` grouped by top-level dir |

| When | Allowed |
|------|---------|
| `close` | audit only |
| `close commit` | `git status --porcelain` → stage safe in-scope paths (framework-mode: full repo via `git add -A`; target-mode: `.work.soc/` only; incl. new untracked files/dirs) → `git commit` → `git status -sb` |
| `close commit scoped` | `git add` HANDOFF_SOC + NEXT_SOC (+ session-listed paths only, all under `.work.soc/`) |
| `close commit push` | above + `git push` |
| `commit` | same as `close commit` but **no** HANDOFF_SOC/NEXT_SOC update |
| `commit push` | same as `close commit push` but **no** HANDOFF_SOC/NEXT_SOC update |

Never on default `close`: commit or push. **Standalone `commit` / `commit push`** always runs git.

---

## Commit message rules (summary)

- Plain text only — no surrounding quotes, no parentheses wrapping the message.
- Subject ≤72 chars (including ref prefix), imperative mood.
- Body: why, not file list; omit if subject suffices.
- With task ref: `SOC-014: subject line`. Without ref (genuinely none): `type: short description` — valid types `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`.
- Readable by non-technical stakeholders (per `.cursorrules` §Commit Message Format).

## Commit message examples

**Session bookend with SOC ref:**

```
SOC-014: close soc-session parity session

HANDOFF_SOC/NEXT_SOC updated; skill rewritten to mirror session-control.
```

**Docs-only session (no ref):**

```
docs: update HANDOFF_SOC for session close

Session state refreshed; no framework code changed.
```

---

## Bootstrap (no HANDOFF_SOC yet)

If `.work.soc/context/HANDOFF_SOC.md` is missing:

1. Tell the operator HANDOFF_SOC is required for soc-session.
2. Offer: run `@soc-deploy-basic update` (scaffolds `.work.soc/` from `templates/work/`) **or** create a minimal HANDOFF_SOC.
3. Minimal HANDOFF_SOC sections: Session status, Repository state, Recommended pick-up, Fresh start checklist.

Do not invent session history.

---

## Start protocol (detailed)

<a id="start-protocol-detailed"></a>

### S1 — Baseline reads (mandatory)

Read these files **in full** (or confirm missing). Record `pass` only after reading.

| # | File (repo-root path) | Pass criteria |
|---|----------------------|----------------|
| 1 | `.cursorrules` | Can state: identity, core principles, protected files, no-commit rule, SOC section |
| 2 | `.work.soc/context/HANDOFF_SOC.md` | Know: session status, last session outcome, carryover items |
| 3 | `.work.soc/plans/NEXT_SOC.md` | Know: recommended next action + iteration table state |
| 4 | `.work.soc/plans/UNKNOWNS_SOC.md` | Know: every open unknown, owner, and what it blocks |

### S2 — Conditional reads (task-based)

If the operator named a domain, read those paths before claiming start complete.

| Task touches | Read |
|--------------|------|
| Deploy skills | `skills/soc-deploy-*/skill.md`, `scripts/soc-deploy-*.sh` |
| Scanning / strix core | `skills/soc-director/skill.md`, `DOCS_TECH_STACK.md` |
| Session framework itself | this skill + `skills/SKILL_DEPENDENCIES.md` |

### S3 — Environment snapshot (evidence)

Run (or explain why skipped):

```bash
git status -sb
git log -1 --oneline
```

Optional — sandbox runtime availability (relevant for scan work):

```bash
docker info >/dev/null 2>&1 && echo "docker: up" || echo "docker: unavailable"
```

Record: branch, clean/dirty, last commit, docker availability if checked.

### S4 — Session goal (interaction)

Capture goal from (in order): text after `start -`, else HANDOFF_SOC **Recommended pick-up** / NEXT_SOC **Recommended next**, else ask **once**:

**Q:** What is the primary goal for this SOC session? (one line)

Do **not** ask if the goal is already clear from invocation or HANDOFF_SOC. Store in start report; do not rewrite HANDOFF_SOC beyond S5.

### S4c — Active ref (mandatory, no-network)

Choose the session/task ref in this priority order:

1. **HANDOFF_SOC session line** — ref matching `[A-Z][A-Z0-9_]*-(T-)?[0-9]+` (e.g. `SOC-013`).
2. **Goal text** — explicit ref in `start - <goal>`.
3. **NEXT_SOC iteration table** — the in-progress `SOC-NNN` row, if any.
4. **`.github/task-registry.json`** — if present, match entries against goal/changed files (same parsing as `.ai/skills/session-control`).
5. **Branch name** — `(feature|fix|chore|docs)/[A-Z]+-[0-9]+` or `[A-Z]+-[0-9]+/`.
6. **None found** — continue without a ref; commit messages fall back to `type:` format (per `.cursorrules` §Task Refs rule 3). If the work clearly belongs to a task, ask the operator **once** for the ref.

Write the chosen ref (when found) to `.work.soc/active-ref`:

```bash
echo "SOC-014" > .work.soc/active-ref
```

This file is the single source of truth for the session ref; close removes it.

### S5 — Mark session open (HANDOFF_SOC)

Update **only** the session-status block at the top of `{HANDOFF_SOC}` (see [templates](#handoff_soc--session-status-templates)):

- **Open:** `<YYYY-MM-DD>` - goal: \<goal or "not specified"\> (template shape), or `**Status:** Open` + goal in the Session line (legacy header shape).
- **Updated / Date:** today.
- Preserve prior "Closed" history; close — not start — records outcomes.

If the operator invoked **status** or **context** mode, skip S5 and S6.

### S6 — Start report (mandatory output)

```markdown
## SOC session started

**Date:** <ISO date> · **Branch:** <branch> · **Working tree:** clean | dirty

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | .cursorrules read | pass/fail | |
| 2 | HANDOFF_SOC read | pass/fail | |
| 3 | NEXT_SOC read | pass/fail | |
| 4 | UNKNOWNS_SOC read | pass/fail | |
| 5 | Conditional reads | pass/skip | <paths> |
| 6 | Git snapshot | pass/skip | <one-liner> |
| 7 | Session goal captured | pass | <goal> |
| 8 | Active ref | pass/skip | <ref or none> |
| 9 | HANDOFF_SOC marked Open | pass/skip | |

### You are cleared to work when
All mandatory checks (1–4, 6–7) are **pass**. If any mandatory **fail**, fix before starting work.

### Pick up here
<quote recommended next from NEXT_SOC.md>

### Open blockers (owner)
<from HANDOFF_SOC / NEXT_SOC, or none>

### Principles reminder (3 bullets max)
<from .cursorrules — not a full paste>
```

---

## Context protocol (detailed)

<a id="context-protocol-detailed"></a>

### X1 — Mandatory context reads (read in full)

Same set as [S1](#s1--baseline-reads-mandatory). Conditional reads per [S2](#s2--conditional-reads-task-based) only when the operator named a domain. **No** active-ref write.

### X2 — Uncommitted-aware snapshot (evidence)

Run:

```bash
git status -sb
git diff --stat
git diff --cached --stat
git log -1 --oneline
```

Classify the working tree:
- **clean:** state explicitly; report last commit only.
- **dirty:** summarize by top-level area (e.g. `2 files scripts/`, `1 file .work.soc/plans/`); list staged vs unstaged vs untracked counts. **Do not** paste full diffs — file paths + per-area counts only. Flag any path matching secrets scan patterns ([C1](#c1--working-tree-audit-mandatory)) without printing content.

### X3 — Context report (mandatory output)

```markdown
## SOC context

**Date:** <ISO date> · **Branch:** <branch> · **Working tree:** clean | dirty (N files)
**Last commit:** <sha - subject>

### Context loaded
| # | File | Result | Note |
|---|------|--------|------|
| 1 | .cursorrules | pass | |
| 2 | HANDOFF_SOC | pass (or missing) | Session: Open|Closed … |
| 3 | NEXT_SOC | pass (or missing) | |
| 4 | UNKNOWNS_SOC | pass (or missing) | |

### Uncommitted status (read-only)
- Staged: <N files> · Unstaged: <N files> · Untracked: <N files>
- Areas touched: <top-level dirs with counts>
- Secrets scan: clean | <flagged paths (not printed)>
- (Clean tree → omit this section; state "working tree clean".)

### Pick up here
<quote recommended next from NEXT_SOC.md, or "no NEXT_SOC.md">

### Open blockers (owner)
<from HANDOFF_SOC / NEXT_SOC, or none>

### No files written
This mode is read-only: HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC, and `.work.soc/active-ref` are **not** modified. To open a session bookend, run `@soc-session start`.
```

### Anti-patterns (context)

- Treating `context` as `start` (writing the HANDOFF_SOC "Open" line) — `context` writes nothing.
- Pasting raw `git diff` output (use per-area counts; respect no-PII/scope).
- Skipping the secrets-flag pass on a dirty tree.
- Claiming "context loaded" without reading all of the X1 set every time the verb runs.

---

## Commit protocol (detailed)

<a id="commit-protocol-detailed"></a>

**Execution order:** M1 → M2 → M3 → M4 → M5 → M6. Standalone: **no** HANDOFF_SOC/NEXT_SOC updates; session stays open.

### M1 — Working tree audit (same as C1)

Same as [C1](#c1--working-tree-audit-mandatory). On secrets **fail**, **stop** — no M4/M5.

### M2 — Verification gate (same as C2)

Same as [C2](#c2--verification-gate-this-session).

### M3 — Follow-ups

Same as [C3](#c3--follow-ups-required).

### M4 — Commit message with task ref (always)

**Always** produce the commit message block — even when tree is clean (`none - working tree clean`).

**Task ref extraction (auto-detect), priority order:**

1. **HANDOFF_SOC session line** — ref matching `[A-Z][A-Z0-9_]*-(T-)?[0-9]+`.
2. **`.work.soc/active-ref`** — read its first line and extract the ref:
   ```bash
   head -1 .work.soc/active-ref 2>/dev/null | grep -oE '[A-Z][A-Z0-9_]*-(T-)?[0-9]+' || true
   ```
3. **`.github/task-registry.json`** — if present, match entries against changed files/goal (see `.ai/skills/session-control` for the parsing snippet).
4. **Branch name** — `(feature|fix|chore|docs)/[A-Z]+-[0-9]+` or `[A-Z]+-[0-9]+/`.
5. **Last commit subject** — if `git log -1 --oneline` starts with `[A-Z]+-[0-9]+`, reuse it.
6. **No ref found** — if the work clearly belongs to a task, ask the operator **once**. If genuinely no ref exists, use conventional `type:` format (per `.cursorrules` §Task Refs rule 3). Never invent a ref.

**Subject format:**
- Ref found: `{REF}: {subject}` (e.g. `SOC-014: align soc-session with session-control`)
- No ref: `type: short description`

Label in report: **Commit message (draft)** vs **Commit message (used)**.

### M5 — Git actions (modifiers only)

Same as [C4b](#c4b--git-actions-modifiers-only) — mode-dependent default scope (framework-mode: full repo; target-mode: `.work.soc/` only), commit via HEREDOC, post-commit verification, push only if the invocation included `push`.

**Hard rule — agents MUST execute git:** Typing `@soc-session commit` does not commit by itself. The agent **MUST** run shell commands. The checklist git item is **fail** if the tree still has unstaged safe in-scope changes (framework-mode: repo-wide; target-mode: `.work.soc/`) and no commit SHA was produced.

**Hard rule — no Co-authored-by:** Never add `Co-authored-by:` trailers (per `.cursorrules` §No Attribution).

**Clean tree + `commit` modifier:** skip commit; report `Commit message (used): none - working tree clean`.

### M6 — Commit report (mandatory output)

```markdown
## SOC commit completed

**Date:** <ISO date> · **Branch:** <branch>

### Checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Git audit | pass/fail | clean / N files changed |
| 2 | Secrets safe | pass/fail | |
| 3 | Verification honest | pass/fail | |
| 4 | Follow-ups listed | pass | |
| 5 | Commit message shown | pass | always |
| 6 | Task ref extracted | pass/skip | ref or no ref found |
| 7 | Git commit | pass/fail/skip | SHA + `git status` evidence |
| 8 | Commit scope staged | pass/fail/skip | mode detected (framework/target); leftover safe in-scope paths listed |
| 9 | Git push (if requested) | pass/fail/skip | modifier `push` |

### Commit message
**Status:** draft | used
**Message:**

    SOC-014: subject line here

    Optional body.

**Git:** committed \<sha\> | push \<remote/branch\> result

**Session:** still open — no HANDOFF_SOC or NEXT_SOC changes.
```

---

## Close protocol (detailed)

<a id="close-protocol-detailed"></a>

**Execution order:** C1 → C2 → C3 → C4 (draft message) → C5 (HANDOFF_SOC) → C6 (NEXT_SOC + UNKNOWNS_SOC) → C4b (git, if `commit`/`push`) → C8 (report).

If C1 secrets **fail**, **stop** — do not run C5, C6, or C4b; report failure in C8.

### C1 — Working tree audit (mandatory)

```bash
git status
git diff --stat
git diff --cached --stat
```

Classify:

| Finding | Action |
|---------|--------|
| Uncommitted changes | Summarize by area; draft commit message(s) |
| Untracked files | Flag if unexpected; remind `.gitignore` / secrets |
| Staged only | Note ready to commit |
| Clean tree | State explicitly |

**Secrets scan (mandatory):** Before summarizing diffs, confirm `git status` does not list paths matching: `credentials/`, `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.p12`, `*.key`, `*.pfx`, `*.p8`, `*id_rsa*`, `*.token`, `*.secret`. If any match → checklist **fail**, **halt close** (no HANDOFF_SOC/NEXT_SOC/git); tell the operator to unstage/remove and never commit content.

### C2 — Verification gate (this session)

Per `.cursorrules` Completion Gate — answer honestly:

| Question | Answer |
|----------|--------|
| Code changed this session? | yes / no |
| Tests/lint/type/build run? (`make check-all` or the relevant subset) | yes / no / n/a |
| All passed? | yes / no / partial |
| Change-safety gates run? (touch-scope, blast-radius, gate-verify, framework-verify) | yes / no / n/a |
| What remains unverified? | list |

Do not claim "all good" if any check failed.

### C3 — Follow-ups required

Detect and list:

- [ ] Uncommitted work needing commit (or intentional WIP)
- [ ] HANDOFF_SOC / NEXT_SOC out of date vs actual repo
- [ ] Owner actions (cross-project writes, keyring choices, deploy targets awaiting update)
- [ ] Docker containers / scan runs left running (optional note)
- [ ] Temp files under `tmp/` that should be cleaned (agent-created only, per DLP)
- [ ] Live E2E still outstanding (standing carryover U-SOC-06/08)

### C4 — Commit message with task ref (always)

**Always** produce the commit message block in the close report — even when the tree is clean (`none - working tree clean`).

Task ref extraction: same priority order as [M4](#m4--commit-message-with-task-ref-always).

- One message if changes are cohesive; suggest **split** with multiple message blocks if not.
- Label in report: **Commit message (draft)** vs **Commit message (used)**.

### C4b — Git actions (modifiers only)

| Modifier | Action |
|----------|--------|
| *(none)* | Message only. Operator runs `git commit` themselves. |
| `commit` | Only if C1 secrets **pass**. After C5/C6 (close) **or** after M4 (standalone commit): stage per **default scope** → `git commit` (HEREDOC) → verify tree → record SHA. |
| `commit scoped` | After C5/C6: stage only `{HANDOFF_SOC}`, `{NEXT_SOC}`, `{UNKNOWNS_SOC}`, and paths explicitly tied to this session in the close report (all under `.work.soc/`). |
| `commit push` | After successful commit: `git push` (current branch). Never force-push unless the operator explicitly requests it in the same message. |
| `close push` (no `commit`) | Treat as `close commit push` (`push` requires commit). State the normalization in the report. |

**Hard rule — agents MUST execute git:** Typing `@soc-session close commit` or `@soc-session commit` does not commit by itself. The agent **MUST** run the shell commands below. The checklist git item is **fail** if the tree still has unstaged safe in-scope changes and no commit SHA was produced.

**Default commit scope** (when modifier is `commit` or `commit push`, not `scoped`):

0. **Detect mode** (skill.md § Commit scope): framework-mode when the repo root contains `skills/soc-session/skill.md` + `scripts/soc-deploy-basic.sh` (the `.ai.soc` source repo itself); otherwise target-mode.
1. Run `git status --porcelain` (from C1).
2. Build the stage list:
   - **framework-mode:** every path with status `M`, `A`, `D`, `R`, `C`, or `??` — the commit covers **all modified/added/new files repo-wide** — **except** paths matching the secrets scan patterns (C1) — never add.
   - **target-mode:** every path **under `.work.soc/`** with status `M`, `A`, `D`, `R`, `C`, or `??` (untracked — includes **new untracked files/dirs**) **except** secrets scan patterns (C1).
3. Stage:
   ```bash
   # framework-mode
   git add -A
   # target-mode
   git add .work.soc/
   ```
   `git add -A` in framework-mode and `git add .work.soc/` in target-mode naturally pick up new untracked files/dirs.
4. **Target-mode only:** do not stage anything outside `.work.soc/` (`strix/`, `scripts/`, `.cursorrules`, app code); list out-of-scope paths in the close report as follow-ups for the operator to commit deliberately. **Framework-mode:** out-of-scope paths do not exist by definition; flag any protected-file changes (`.cursorrules` §Protected Files) in the report so the operator sees them land.
5. **Do not** default to HANDOFF_SOC + NEXT_SOC only — that is **`commit scoped`**, not default `commit`.
6. If the only remaining dirty paths are excluded (secrets, or outside `.work.soc/` in target-mode), commit what was staged and report exclusions.

**Commit command shape:**

```bash
# framework-mode
git add -A
# target-mode
git add .work.soc/
git diff --cached --name-only   # target-mode: verify every staged path starts with .work.soc/
git commit -m "$(cat <<'EOF'
<exact message from C4>
EOF
)"
git status -sb
git log -1 --oneline
```

In target-mode, if `git diff --cached --name-only` shows any path outside `.work.soc/`, unstage it (`git restore --staged <path>`) before committing and report the correction.

**Post-commit verification (mandatory):**

| Check | pass when |
|-------|-----------|
| Commit created | `git log -1` shows new SHA |
| Staging complete | framework-mode: tree clean apart from excluded paths. target-mode: no remaining `M`/`D`/`??` under `.work.soc/` — **or** report lists each leftover path and why (secrets, out-of-scope, intentional WIP) |

**Push caveat:** `git push` transports the **entire current branch** — any commits already on the branch (including work outside this session) go with it. The scope guarantee covers what this session stages and commits, not what push transports. If the operator needs isolation, the session commit should go on its own branch or the operator should confirm the branch contains only intended commits before pushing.

**On commit failure:** report hook output; do not claim close complete for the git step; HANDOFF_SOC/NEXT_SOC updates still stand if already written.

**Clean tree + `commit` modifier:** skip commit; report `Commit message (used): none - working tree clean`.

**Never:** `git commit --no-verify`, `git push --force` — unless the operator explicitly requests that exact action in the same message (DLP). `git add -A` is the sanctioned staging command **only in framework-mode**; in target-mode it is always forbidden.

### C5 — Update HANDOFF_SOC (mandatory on close)

Rewrite top sections (keep history append-only):

1. **Session status:** `Closed: <date>` — one-line summary of session outcome (see [templates](#handoff_soc--session-status-templates)).
2. **Updated / Date:** today.
3. **Repository state:** current truth (what changed, blockers, committed vs uncommitted).
4. **Recommended pick-up:** point to `NEXT_SOC.md`.
5. **What this cycle produced / session summary:** append the new session; do not delete historical sessions.
6. **Open / carryover:** refresh uncommitted state, outstanding verifications, cross-project follow-ups.

**Cleanup:** Remove `.work.soc/active-ref` if it exists:

```bash
rm -f .work.soc/active-ref
```

(Agent-created session file under the work tree — allowed by DLP's ephemeral exception; it is recreated on the next start.)

### C6 — Update NEXT_SOC + UNKNOWNS_SOC (mandatory on close)

- Move completed iteration rows to **DONE** with date and evidence.
- Set **one** clear **Recommended next** list.
- Refresh **UNKNOWNS_SOC**: resolve answered unknowns, add new ones with owner.

### C8 — Close report (mandatory output)

```markdown
## SOC session closed

**Date:** <ISO date> · **Branch:** <branch>

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Git audit | pass/fail | clean / N files changed |
| 2 | Secrets safe | pass/fail | |
| 3 | Verification honest | pass/fail | |
| 4 | Follow-ups listed | pass | |
| 5 | Commit message shown | pass | always |
| 6 | Git commit (if requested) | pass/fail/skip | modifier `commit`; SHA + `git status` evidence |
| 6b | Commit scope staged (default `commit`) | pass/fail/skip | not `scoped`; mode detected (framework/target); leftover safe in-scope paths listed |
| 7 | Git push (if requested) | pass/fail/skip | modifier `push` |
| 8 | HANDOFF_SOC updated | pass/fail | |
| 9 | NEXT_SOC + UNKNOWNS_SOC updated | pass/fail | |

### Commit message
**Status:** draft | used
**Task ref:** <ref or none>
**Message:** (plain text below — always present)

    SOC-014: subject line here

    Optional body — why, not what.

**Git:** no commit (default) | committed \<sha\> | push \<remote/branch\> result

### Follow-ups before next session
<ordered list>

### Next session should
<one line from NEXT_SOC.md>
```

---

## Critical interactions

| When | Ask / do |
|------|----------|
| **Start** | Prior HANDOFF_SOC says `Closed` → treat as new session; do not assume prior chat memory |
| **Start** | Missing HANDOFF_SOC → offer `@soc-deploy-basic update` or create minimal HANDOFF_SOC |
| **Start** | Dirty tree at start → note in report; ask if continuing WIP |
| **Start** | HANDOFF_SOC already **Open**, new `start -` goal differs | Update Open line with new goal + date |
| **Close** | Large uncommitted diff outside `.work.soc/` in target-mode → suggest the operator commit it separately; target-mode session commit stays `.work.soc/`-scoped. In framework-mode the full tree is in scope by design. |
| **Close** | Protected files changed → flag for explicit operator review in the report (in target-mode they are also out of scope and never staged) |
| **Close** | `close commit` / `close commit push` → run C4b in shell after HANDOFF_SOC/NEXT_SOC; stage per **mode scope** (framework: full repo; target: `.work.soc/`) |
| **Close** | Operator expected commit but tree still dirty → **fail** item 6/6b |
| **Commit** | `@soc-session commit` → run Commit protocol; **do not** update HANDOFF_SOC or NEXT_SOC |
| **Commit** | No task ref found, work clearly task-bound → ask operator once (M4 priority 6) |

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| Merge conflict markers in tree | close checklist **fail**; list files |
| Only paths outside `.work.soc/` changed (target-mode) | Outside session-commit scope — stage nothing; list as follow-up for a separate operator-driven commit. In framework-mode these are in scope and staged normally. |
| `credentials/` in `git status` | **fail** secrets check; do not summarize content |
| Operator closes mid-task | HANDOFF_SOC notes "in-flight: …" under Repository state |
| Multiple logical commits | close report suggests 2+ message blocks |
| HANDOFF_SOC already Open, `start` re-run (same goal) | Refresh date only; do not duplicate history |
| Secrets scan fail | **Halt** close — no HANDOFF_SOC/NEXT_SOC/commit until resolved |
| Scan containers left running | Note in C3; do not kill without operator request (DLP) |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `close` expecting auto-commit | Default is draft only | `close commit` |
| `close commit` but tree still dirty | Agent staged HANDOFF_SOC-only or skipped shell git | Re-run close; agent must follow C4b default scope |
| `close commit` for bookend files only | Default commits the mode scope (framework: full repo; target: `.work.soc/`) | `close commit scoped` |
| `close push` without `commit` | Skill maps to commit+push | `close commit push` |
| `commit` expecting HANDOFF_SOC update | Standalone commit skips HANDOFF_SOC/NEXT_SOC | Use `close commit` instead |
| `commit push` expecting session close | Standalone commit keeps session open | Use `close commit push` instead |
| `start` without reading files | Skill requires evidence | Full start protocol |
| `delete HANDOFF_SOC and recreate` | Loses history | Append + update sections |
| `close` with failing tests unmentioned | Violates honesty (Core Principle 2) | Report failures in C2 |
| Omitting commit message from report | Violates skill | Always show ### Commit message |
| Staging `strix/` / `scripts/` in a target-mode session commit | Target-mode commits are `.work.soc/`-scoped (framework-mode stages them by design) | Run the commit from the framework repo, or commit code separately |

---

## Anti-patterns

- Claiming "context loaded" without reading HANDOFF_SOC and NEXT_SOC
- Closing session without updating HANDOFF_SOC and NEXT_SOC
- Committing on plain `close` (without `commit` modifier)
- **`close commit` with only HANDOFF_SOC/NEXT_SOC staged** while other safe in-scope paths remain dirty (framework-mode: any repo path; target-mode: `.work.soc/`)
- **Reporting close commit done without running `git commit`** or without a new SHA
- Omitting the commit message block from the close report
- Putting secrets or PII in HANDOFF_SOC
- Marking checklist `pass` without evidence
- Continuing close after secrets scan **fail**
- Running HANDOFF_SOC/NEXT_SOC updates on standalone `commit` or `commit push`
- Adding `Co-authored-by:` trailers or using `git commit --no-verify`
- Running `git push` when only `commit` (not `push`) was in the invocation

---

## Project layout (convention)

**`{WORK_SOC_ROOT}` = `.work.soc/`** at repo root (target repo for thin/fat deploys; this repo for framework work). Not the git root itself.

**Commit scope by mode** (skill.md § Commit scope): **framework-mode** — repo root contains `skills/soc-session/skill.md` + `scripts/soc-deploy-basic.sh`; session commits cover the **full repo** (all modified/added/new files). **target-mode** — anything else; session commits cover **`.work.soc/` only**.

```
.work.soc/                       ← {WORK_SOC_ROOT}
  context/HANDOFF_SOC.md         ← soc-session ({HANDOFF_SOC})
  plans/NEXT_SOC.md              ← soc-session ({NEXT_SOC})
  plans/UNKNOWNS_SOC.md          ← soc-session ({UNKNOWNS_SOC})
  active-ref                     ← session task ref (start writes, close removes)
  strix_runs/                    ← scan output (soc-director)
.ai.soc/skills/                  ← portable skills only (or $SOC_SOURCE/skills/ thin-client)
```

Projects without `.work.soc/context/HANDOFF_SOC.md`: run `@soc-deploy-basic update` (thin) or `@soc-deploy-files` (fat) to scaffold.
