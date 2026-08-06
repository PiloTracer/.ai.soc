---
name: soc-session
description: >-
  SOC session bookend. Open/close/status/context. Updates HANDOFF_SOC,
  NEXT_SOC, UNKNOWNS_SOC. Optional git commit scoped to the target repo's
  .work.soc/ working tree — commit includes new untracked files/dirs there
  and never touches paths outside .work.soc/. context loads all mandatory
  context read-only and is uncommitted-aware (surfaces dirty-tree status
  without writing HANDOFF). Use when the user says soc-session start,
  soc-session close [commit] [push], soc-session status, or
  soc-session context.
---

# soc-session

**Purpose:** Lightweight bookend for every SOC assessment session. Start loads context. Close saves state. No over-engineering.

---

## I0 — Files

| File | Purpose |
|------|---------|
| `{HANDOFF_SOC}` | Current SOC session context, what was done, what's next |
| `{NEXT_SOC}` | Ordered list of next SOC tasks / priorities |
| `{UNKNOWNS_SOC}` | Open security unknowns that need research or decisions |

**Location:** `.work.soc/context/HANDOFF_SOC.md`, `.work.soc/plans/NEXT_SOC.md`, `.work.soc/plans/UNKNOWNS_SOC.md`.

---

## Parse invocation

| User says | Verb | Git action |
|-----------|------|------------|
| `@soc-session start` | start | - |
| `@soc-session close` | close | draft message only |
| `@soc-session close commit` | close | commit `.work.soc/` changes (incl. new untracked files/dirs) |
| `@soc-session close commit push` | close | commit `.work.soc/` then push |
| `@soc-session close push` | close | invalid — `push` requires `commit`; draft message only |
| `@soc-session status` | status | - |
| `@soc-session context` | context | - |

**Aliases:** `begin`, `open` → start; `end`, `handoff` → close.

**Git permission scope:** `commit` / `push` modifiers authorize **only that close invocation**. They are never standing permission for later commits or pushes. Absent those modifiers in the **same message**, draft the commit message only — do not run `git commit` or `git push`.

**Git scope (hard limit):** any authorized `commit` is **scoped to `{WORK_SOC_ROOT}`** — the `.work.soc/` working directory in the **target repo**. Never stage or commit paths outside `.work.soc/` (no app code, no `.cursorrules`, no source-tree files); never `git add -A`. Files outside `.work.soc/` may be reported as dirty but are never included in a session commit. The session skill itself only ever writes inside `.work.soc/` (HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC). Note: the `.work.soc/`-only guarantee applies to what the session **stages and commits**; a `git push` transports the entire current branch, so it may also carry commits made outside this session (see I2 step 7).

---

## I1 — Start mode

```
@soc-session start
```

1. Read `{HANDOFF_SOC}` into context.
2. Read `{NEXT_SOC}` into context.
3. Read `{UNKNOWNS_SOC}` into context.
4. Run `git status -sb` and `git log -1 --oneline`.
5. Confirm: *"SOC session started with [N] next items and [M] unknowns. Tree: [clean|dirty]."*

**If HANDOFF_SOC doesn't exist:** Prompt to run bootstrap or create minimal HANDOFF_SOC.

---

## I2 — Close mode

```
@soc-session close [commit] [push]
```

1. Summarize what was done this session (bullet points).
2. Update `{HANDOFF_SOC}`:
   - Session date/time
   - What was accomplished
   - Key findings / decisions
   - Updated next steps
   - Updated unknowns
3. Update `{NEXT_SOC}` with revised priorities.
4. Update `{UNKNOWNS_SOC}` — resolve any that were answered, add new ones.
5. **Draft the commit message** (always — even without `commit`, so the operator can run it themselves). Scope: only files under `{WORK_SOC_ROOT}` (`.work.soc/` in the target repo). Never propose paths outside `.work.soc/`.
6. **If `commit` modifier (this invocation only):** commit the `.work.soc/` working tree:
   a. **Secret scan:** list the files that would be staged under `.work.soc/` (tracked modifications, deletions, and new untracked files/dirs). Scan for secret paths (`.env`, `credentials/`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `*token*`, `*secret*`). If any match → **abort commit**; report the matched paths (names only, never content); no git writes.
   b. **Stage scoped to `.work.soc/`:** `git add .work.soc/` — stages modified, deleted, **and new untracked files/dirs** under `.work.soc/`. Never `git add -A`; never `git add <path outside .work.soc/>`.
   c. **Verify the staged set:** `git diff --cached --name-only` — every staged path must start with `.work.soc/`. If anything outside appears, unstage it (`git restore --staged <path>`) and report.
   d. **Commit:** `git commit -m "<message>"`. Show SHA + `git status -sb` (files outside `.work.soc/` remain uncommitted — expected).
7. **If `push` modifier (this invocation only; requires `commit`):** `git push` after successful commit. Do not push unless `push` appears in the **same** close message. Note: `git push` transports the **entire current branch** — any commits already on the branch (including non-`.work.soc/` work) go with it; the `.work.soc/`-only guarantee covers what this session stages and commits, not what push transports. If the operator needs isolation, the session commit should go on its own branch or the operator should confirm the branch contains only intended commits before pushing.
   - `close push` **without** `commit` is invalid: report *"`push` requires `commit` in the same message — re-run `close commit push`"* and draft the message only (no git writes).
8. Confirm: *"SOC session closed. HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC updated. Committed `.work.soc/` → <sha>."* (omit the commit clause when no `commit` modifier was present).

---

## I3 — Status mode

```
@soc-session status
```

Read-only snapshot. No file writes.

1. Read `{HANDOFF_SOC}` and `{NEXT_SOC}`.
2. Run `git status -sb` and `git log -1 --oneline`.
3. Output:

```
**Session state:** active / closed
**Branch:** <branch> · **Tree:** clean | dirty
**Last session:** <date> — <summary>
**Next items:** <count> — <first item>
**Unanswered:** <count> from UNKNOWNS_SOC
```

---

## I4 — Context mode

```
@soc-session context
```

Read-only full context load. **No** HANDOFF/NEXT/UNKNOWNS writes. Sits between `status` (compact) and `start` (writes HANDOFF). Use when you want full session context for ad-hoc reasoning without opening/closing a session bookend.

### X1 — Mandatory context reads (read in full)

| # | File | Pass criteria |
|---|------|---------------|
| 1 | `.cursorrules` | Identity, core principles, protected files |
| 2 | `{HANDOFF_SOC}` | §Session status → §Open owner actions |
| 3 | `{NEXT_SOC}` | Recommended next + owner blockers |
| 4 | `{UNKNOWNS_SOC}` | Every open unknown + owner + Blocks |

### X2 — Uncommitted-aware snapshot (evidence)

Run:

```bash
git status -sb
git diff --stat
git diff --cached --stat
git log -1 --oneline
```

Classify the working tree:
- **clean:** report last commit only.
- **dirty:** summarize by top-level area (file paths + per-area counts). Flag any path matching secrets patterns without printing content.

### X3 — Context report (mandatory output)

```markdown
## SOC context

**Date:** <ISO date> · **Branch:** <branch> · **Working tree:** clean | dirty (N files)
**Last commit:** <sha - subject>

### Context loaded
| # | File | Result | Note |
|---|------|--------|------|
| 1 | .cursorrules | pass | |
| 2 | HANDOFF_SOC | pass/missing | |
| 3 | NEXT_SOC | pass/missing | |
| 4 | UNKNOWNS_SOC | pass/missing | |

### Uncommitted status
- Staged: <N files> · Unstaged: <N files> · Untracked: <N files>
- Areas touched: <top-level dirs with counts>
- (Clean tree → omit this section)

### Pick up here
<quote from NEXT_SOC.md>

### Open blockers (owner)
<none or list>

### No files written
This mode is read-only: HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC not modified.
Run @soc-session start to open a session bookend.
```

### Anti-patterns (context)
- Treating `context` as `start` (writing HANDOFF_SOC) — context writes nothing.
- Pasting raw `git diff` output (use per-area counts).
- Skipping the secrets-flag pass on a dirty tree.
- Claiming "context loaded" without reading all of X1 set.

---

## Completion

| # | Check | Result |
|---|-------|--------|
| 1 | HANDOFF_SOC.md exists and is current | |
| 2 | NEXT_SOC.md has ordered priorities | |
| 3 | UNKNOWNS_SOC.md tracks open questions | |
| 4 | Session start was acknowledged | |
| 5 | Session close wrote state + optional commit (`.work.soc/` only) | |
| 6 | Context mode: no files written, uncommitted-aware summary produced | |
| 7 | `commit` (when requested) staged **only** `.work.soc/` paths, including new untracked files/dirs; `git diff --cached --name-only` all start with `.work.soc/` | |
| 8 | No git writes performed outside `.work.soc/`; `push` never ran without `commit` | |

**Next:** `@soc-director - <target>` or whatever NEXT_SOC.md says first.
