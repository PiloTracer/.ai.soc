---
name: session-soc
description: >-
  SOC session bookend. Open close start and status.
  Updates HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC. Optional git commit.
  session-soc start, session-soc close, session-soc status.
---

# session-soc

**Purpose:** Lightweight bookend for every SOC assessment session. Start loads context. Close saves state. No over-engineering.

---

## I0 — Files

| File | Purpose |
|------|---------|
| `HANDOFF_SOC.md` | Current SOC session context, what was done, what's next |
| `NEXT_SOC.md` | Ordered list of next SOC tasks / priorities |
| `UNKNOWNS_SOC.md` | Open security unknowns that need research or decisions |

**Location:** `.work.soc/context/HANDOFF_SOC.md`, `.work.soc/plans/NEXT_SOC.md`, `.work.soc/plans/UNKNOWNS_SOC.md`.

---

## I1 — Start mode

```
@session-soc start
```

1. Read `HANDOFF_SOC.md` into context.
2. Read `NEXT_SOC.md` into context.
3. Read `UNKNOWNS_SOC.md` into context.
4. Confirm: *"SOC session started with [N] next items and [M] unknowns."*

**If HANDOFF_SOC.md doesn't exist:** Prompt to run bootstrap or create minimal HANDOFF_SOC manually.

---

## I2 — Close mode

```
@session-soc close
```

1. Summarize what was done this session (bullet points).
2. Update `HANDOFF_SOC.md`:
   - Session date/time
   - What was accomplished
   - Key findings / decisions
   - Updated next steps
   - Updated unknowns
3. Update `NEXT_SOC.md` with revised priorities.
4. Update `UNKNOWNS_SOC.md` — resolve any that were answered, add new ones.
5. **Optional:** `git add -A && git commit -m "soc session <date>: <summary>"` (only if user confirms).
6. Confirm: *"SOC session closed. HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC updated."*

---

## I3 — Status mode

```
@session-soc status
```

Reports:

- **Session state:** active (start was called) or closed
- **Last session:** date and summary (from HANDOFF_SOC.md)
- **Next items:** count and first 3 from NEXT_SOC.md
- **Unanswered:** count from UNKNOWNS_SOC.md

---

## Completion

| # | Check | Result |
|---|-------|--------|
| 1 | HANDOFF_SOC.md exists and is current | |
| 2 | NEXT_SOC.md has ordered priorities | |
| 3 | UNKNOWNS_SOC.md tracks open questions | |
| 4 | Session start was acknowledged | |
| 5 | Session close wrote state + optional commit | |

**Next:** `@soc-director - <target>` or whatever NEXT_SOC.md says first.

---

*Modeled after `.ai.biz/skills/session-biz/` concept. Kept intentionally minimal.*
