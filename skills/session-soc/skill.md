---
name: session-soc
description: >-
  SOC session bookend. Open/close/status/context. Updates HANDOFF_SOC,
  NEXT_SOC, UNKNOWNS_SOC. Optional git commit.
  context loads all mandatory context read-only and is uncommitted-aware
  (surfaces dirty-tree status without writing HANDOFF). Use when the user says
  session-soc start, session-soc close, session-soc status, or
  session-soc context.
---

# session-soc

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
| `@session-soc start` | start | - |
| `@session-soc close` | close | draft message only |
| `@session-soc close commit` | close | commit all safe dirty paths |
| `@session-soc close commit push` | close | commit then push |
| `@session-soc status` | status | - |
| `@session-soc context` | context | - |

**Aliases:** `begin`, `open` → start; `end`, `handoff` → close.

---

## I1 — Start mode

```
@session-soc start
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
@session-soc close [commit] [push]
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
5. **If `commit` modifier:** Before staging, scan for secret paths (`.env`, `credentials/`, `*.pem`, `*.key`). If any match → abort commit; report failure. Stage safe paths via explicit `git add` of changed files (not `git add -A`). Commit with message. Show SHA + `git status -sb`.
6. **If `push` modifier:** `git push` after successful commit.
7. Confirm: *"SOC session closed. HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC updated."*

---

## I3 — Status mode

```
@session-soc status
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
@session-soc context
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
Run @session-soc start to open a session bookend.
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
| 5 | Session close wrote state + optional commit | |
| 6 | Context mode: no files written, uncommitted-aware summary produced | |

**Next:** `@soc-director - <target>` or whatever NEXT_SOC.md says first.