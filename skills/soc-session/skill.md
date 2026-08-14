---
name: soc-session
description: >-
  Open or close a SOC working session with verified context load, HANDOFF_SOC
  and NEXT_SOC updates, and optional git commit/push. Commit scope:
  `.work.soc/` only when invoked from a deployed target project; the full
  repo (all modified/added/untracked files) when invoked from the framework
  source repo itself. Also supports standalone commit/push
  without closing (task ref, git add + git commit + git push, no
  HANDOFF_SOC/NEXT_SOC update). `context` loads all mandatory context
  read-only and is uncommitted-aware (surfaces dirty-tree status without
  writing HANDOFF_SOC). Use when the user says soc-session start, soc-session
  close, close commit, close commit push, commit, commit push, soc-session
  context, or soc-session status. Never commits unless the invocation
  includes commit. On commit, MUST run git add + git commit in the shell —
  including new untracked files/dirs (not HANDOFF_SOC-only).
---

# soc-session

Bookend SOC work sessions so the next chat (or human) can resume without guessing. **Tool-agnostic.** Behavioral mirror of `.ai/skills/session-control` — same verbs, same modifiers, same reports — scoped to the SOC work tree (`.work.soc/`) and SOC artifacts.

**Pairs with:** `.cursorrules` (SOC section), `{NEXT_SOC}`, `{UNKNOWNS_SOC}`.

**Registry:** [`skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Canonical path:** `.ai.soc/skills/soc-session/skill.md` · **Invocation examples:** [`reference.md`](reference.md)

**Hard rules:**

- **Default close / default commit:** never `git commit` or `git push`. Only when the invocation includes **`commit`** and/or **`push`** (see [Parse invocation](#parse-invocation)).
- **`close commit` / `close commit push` / `commit` / `commit push`:** **MUST** run `git add` + `git commit` in the shell (see [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C4b) / [Commit protocol](#commit-protocol)), staging per [Commit scope](#commit-scope) (incl. new untracked files/dirs). A dirty in-scope tree after close with only a draft message is **fail**.
- **Always** show the commit message — drafted, used for commit, or `none - working tree clean`.
- **`commit` / `commit push` (standalone):** run git add + commit + push **without** updating HANDOFF_SOC or NEXT_SOC. Session stays open. Useful for mid-session checkpoints.
- **Never commit with `type:` format when a task ref is known or could reasonably be asked for** (per `.cursorrules` §Task Refs). SOC session ids (`SOC-NNN`) are valid refs. If no ref is known but the work clearly belongs to a session/task, ask the operator once. If genuinely no ref exists, conventional `type:` format is acceptable.
- Never paste secrets from `.env`, `credentials/`, or tokens into chat or HANDOFF_SOC.
- Every mutating mode (start, close, commit) ends with a **Completion checklist** — each item `pass` | `fail` | `skip` with evidence.

### Path resolution (mandatory before any Read)

Resolve from **repository root** of the target repo. `{WORK_SOC_ROOT}` = **`.work.soc/`** — not the repo root.

| Artifact | Read / write this path |
|----------|-------------------------|
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |
| `{NEXT_SOC}` | `.work.soc/plans/NEXT_SOC.md` |
| `{UNKNOWNS_SOC}` | `.work.soc/plans/UNKNOWNS_SOC.md` |
| active ref | `.work.soc/active-ref` (written on start, removed on close) |

---

## Parse invocation

Normalize the user message to **verb** + optional **modifiers**. The word `session` is optional (legacy alias).

| User says | Verb | Git action |
|-----------|------|------------|
| `@soc-session` **start** | start | - |
| `soc-session` **start** - \<goal\> | start | - |
| `@soc-session` **close** | close | draft message only |
| `soc-session` **close** **commit** | close | commit all **safe** changes per [Commit scope](#commit-scope) (default scope — [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C4b)) |
| `soc-session` **close** **commit** **scoped** | close | commit only HANDOFF_SOC + NEXT_SOC + paths listed in close report |
| `soc-session` **close** **commit** **push** | close | commit then push |
| `soc-session` **close** **push** | close | treat as **commit push** (`push` requires commit) |
| `soc-session` **commit** | commit | commit all safe changes per [Commit scope](#commit-scope) (default scope), NO close |
| `soc-session` **commit** **push** | commit | commit then push, NO close |
| `@soc-session` **context** | context | - |
| `@soc-session` **status** | status | - |

**Aliases (same verb):** `begin`, `open` → start; `end`, `handoff` → close.

**Goal text:** anything after `-` or on a new line after `start` (not the words `commit`/`push`/`scoped`).

**Git permission scope:** `commit` / `push` modifiers authorize **only that invocation**. They are never standing permission for later commits or pushes (`.cursorrules` §Data Loss Prevention). Absent those modifiers in the **same message**, draft the commit message only.

### Commit scope

Any authorized commit's scope depends on **where the skill runs**. Detect once, state the result in the report:

```bash
ROOT="$(git rev-parse --show-toplevel)"
if [[ -f "$ROOT/skills/soc-session/skill.md" && -f "$ROOT/scripts/soc-deploy-basic.sh" ]]; then
  echo "framework-mode"   # repo root IS the .ai.soc framework source
else
  echo "target-mode"      # deployed thin/fat target project
fi
```

| Mode | Where | Default `commit` scope |
|------|-------|------------------------|
| **framework-mode** | The framework source repo itself (this `.ai.soc` master) | **The full repo** — all modified/added/untracked files (e.g. `git add -A` after the secrets scan). Session work here *is* framework work; the commit must cover it all. |
| **target-mode** | A deployed target project (thin or fat) | **`.work.soc/` only** — never app code, `.cursorrules`, or source-tree files; never `git add -A`. |

Hard limits in **both** modes: the C1 secrets scan still halts the close/commit on any match, and `commit scoped` (bookend files only) is available in both. In framework-mode, protected-file changes (`.cursorrules` §Protected Files) are staged like everything else only when the operator's invocation covers them — flag them in the report so the operator sees what is landing. Note: the staging guarantee applies to what the session **stages and commits**; a `git push` transports the entire current branch either way (see [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) C4b).

**Standalone commit:** `commit` / `commit push` run the same git steps as `close commit` / `close commit push` but **skip** HANDOFF_SOC and NEXT_SOC updates. The session remains open.

---

## Step 0 — Pick a mode

| Mode | Triggers | Action |
|------|----------|--------|
| **start** | `start`, optional goal | [Start protocol](#start-protocol) |
| **close** | `close` [commit] [scoped] [push] | [Close protocol](#close-protocol) |
| **commit** | `commit` [push] | [Commit protocol](#commit-protocol) — git only; no HANDOFF_SOC/NEXT_SOC writes |
| **context** | `context` | [Context protocol](#context-protocol) — full mandatory context load + uncommitted-aware summary; no writes |
| **status** | `status` | [Status protocol](#status-protocol) — compact snapshot; no writes |

If the operator gives a **session goal** with start (e.g. `start - audit deploy skills`), capture it in the start report.

---

## Start protocol

### S1 — Baseline reads (mandatory)

Four-file read table (`.cursorrules`, HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC): [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S1).

### S2 — Conditional reads (task-based)

Task-based conditional read table: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S2).

### S3 — Environment snapshot (evidence)

Git snapshot + optional Docker check: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S3).

### S4 — Session goal (interaction)

Capture goal; ask once if unclear: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S4).

### S4c — Active ref (mandatory, no-network)

Extract session/task ref (`SOC-NNN` or operator ref); write `.work.soc/active-ref`: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S4c).

### S5 — Mark session open (HANDOFF_SOC)

Update `## Session status` Open line only: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S5).

### S6 — Start report (mandatory output)

Start report template and checklist: [reference.md § Start protocol (detailed)](reference.md#start-protocol-detailed) (S6).

---

## Status protocol

Read-only snapshot. **No** HANDOFF_SOC/NEXT_SOC writes. **No** completion checklist.

1. Read `{HANDOFF_SOC}` and `{NEXT_SOC}`.
2. Run `git status -sb` and `git log -1 --oneline`.
3. Output:

```markdown
## SOC session status

**Session:** Open | Closed — <date> — <goal if Open>
**Branch:** <branch> · **Tree:** clean | dirty
**Pick up:** <one line from NEXT_SOC.md>
**Unanswered:** <count> from UNKNOWNS_SOC.md
**Owner blockers:** <short list or none>
```

Optional: one line on dirty files (no full diff). For full context load, use **start**; for full load **without** writes, use **context**.

---

## Context protocol

Read-only full context load. **No** HANDOFF_SOC/NEXT_SOC/UNKNOWNS_SOC/active-ref writes. **No** completion checklist (read-only, like `status`); end with the context report. Sits between `status` (one-line compact) and `start` (full load + marks HANDOFF_SOC Open).

### X1 — Mandatory context reads (read in full)

Same set as [S1](reference.md#s1--baseline-reads-mandatory) minus the active-ref write: [reference.md § Context protocol (detailed)](reference.md#context-protocol-detailed) (X1).

### X2 — Uncommitted-aware snapshot (evidence)

`git status -sb` + diff stats, classified per-area, secrets-flagged: [reference.md § Context protocol (detailed)](reference.md#context-protocol-detailed) (X2).

### X3 — Context report (mandatory output)

Report template: [reference.md § Context protocol (detailed)](reference.md#context-protocol-detailed) (X3).

### Anti-patterns (context)

- Treating `context` as `start` (writing the HANDOFF_SOC "Open" line) — `context` writes nothing.
- Pasting raw `git diff` output (use per-area counts; respect no-PII/scope).
- Skipping the secrets-flag pass on a dirty tree.
- Claiming "context loaded" without reading all of the X1 set every time the verb runs.

---

## Commit protocol

**Execution order:** M1 → M2 → M3 → M4 (draft message with task ref) → M5 (git, if `commit`/`push`) → M6 (report).

Runs git commit and optional push **without** updating HANDOFF_SOC or NEXT_SOC. Session remains open. Idempotent — re-runnable mid-session.

If M1 secrets **fail**, **stop** — do not run M4 or M5.

### M1 — Working tree audit (same as C1)

Same as [C1 in reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed).

### M2 — Verification gate (same as C2)

Same as [C2 in reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed).

### M3 — Follow-ups

Same as [C3 in reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed).

### M4 — Commit message with task ref (always)

Always produce the commit message block — even when tree is clean. Task ref extraction, subject/body format, and report labels: [reference.md § Commit protocol (detailed)](reference.md#commit-protocol-detailed) (M4).

### M5 — Git actions (modifiers only)

Same as [C4b in reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed). **Hard rules:** agents MUST run shell git; no `Co-authored-by:` trailers; never `--no-verify` or `--force`.

### M6 — Commit report (mandatory output)

Report template and checklist: [reference.md § Commit protocol (detailed)](reference.md#commit-protocol-detailed) (M6).

---

## Close protocol

**Execution order:** C1 → C2 → C3 → C4 (draft message) → C5 (HANDOFF_SOC) → C6 (NEXT_SOC + UNKNOWNS_SOC) → C4b (git, if `commit`/`push`) → C8 (report).

If C1 secrets **fail**, **stop** — do not run C5, C6, or C4b; report failure in C8.

### C1 — Working tree audit (mandatory)

`git status` + diff stats; classify findings; **secrets scan** (halt close on match). Full table and patterns: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C1).

### C2 — Verification gate (this session)

Completion Gate honesty table (per `.cursorrules` Core Principle 7): [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C2).

### C3 — Follow-ups required

Detect uncommitted work, stale HANDOFF_SOC/NEXT_SOC, owner actions, temp files. Checklist: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C3).

### C4 — Commit message with task ref (always)

Always show commit message in close report. Task ref priority order and format: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C4).

### C4b — Git actions (modifiers only)

Modifier table, **default commit scope** (`.work.soc/` only), HEREDOC commit shape, post-commit verification, push caveat. Full spec: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C4b).

### C5 — Update HANDOFF_SOC (mandatory on close)

Section rewrite list + `.work.soc/active-ref` cleanup: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C5).

### C6 — Update NEXT_SOC + UNKNOWNS_SOC (mandatory on close)

Done / Recommended next / Unknowns refresh: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C6).

### C8 — Close report (mandatory output)

Close report template and checklist: [reference.md § Close protocol (detailed)](reference.md#close-protocol-detailed) (C8).

---

## Critical interactions

| When | Ask / do |
|------|----------|
| **Start** | Prior HANDOFF_SOC says `Closed` → treat as new session; do not assume prior chat memory |
| **Start** | Missing HANDOFF_SOC → offer `@soc-deploy-basic update` (bootstrap `.work.soc/`) or create minimal HANDOFF_SOC |
| **Close** | `close commit` / `close commit push` → run C4b in shell after HANDOFF_SOC/NEXT_SOC; stage **`.work.soc/` scope** |
| **Commit** | Operator says `@soc-session commit` → run [Commit protocol](#commit-protocol); **do not** update HANDOFF_SOC or NEXT_SOC |

Full table: [reference.md § Critical interactions](reference.md#critical-interactions).

---

## Anti-patterns

- Claiming "context loaded" without reading HANDOFF_SOC and NEXT_SOC
- Closing session without updating HANDOFF_SOC and NEXT_SOC (on **close**)
- **`close commit` without running `git commit`** or without a new SHA
- **Staging outside `.work.soc/` in target-mode** (app code, `.cursorrules`, `strix/`) — target-mode session commits are `.work.soc/`-scoped (framework-mode commits the full tree by design)
- Omitting the commit message block from close/commit reports
- Adding `Co-authored-by:` trailers or using `git commit --no-verify`
- Running `git push` when only `commit` (not `push`) was in the invocation

Full list: [reference.md § Anti-patterns](reference.md#anti-patterns).

---

## Project layout (convention)

**`{WORK_SOC_ROOT}` = `.work.soc/`** at repo root. Session git commits follow [Commit scope](#commit-scope): full repo in framework-mode, `.work.soc/` only in target-mode. See [reference.md § Project layout](reference.md#project-layout-convention).
