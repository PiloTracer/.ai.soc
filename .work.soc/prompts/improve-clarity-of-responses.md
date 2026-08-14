# Response Clarity Protocol

**Status:** Approved · 2026-08-14 (Agent OS `.ai`) · **Portable:** yes — adopt in any OS framework via `adopt-framework-improvements.md` (Phase 1)
**Enforced by (Agent OS):** `skills/SKILL_DEPENDENCIES.md` § Operator handoff contract + `scripts/skill-functional-verify.py`
**Adoption target (any OS framework):** contract section in the target's `skills/SKILL_DEPENDENCIES.md` + a reference in every `skills/<id>/skill.md`; wire the target's skill verifier if one exists, else record the enforcement gap as a follow-up

Sibling protocol: `improve-clarity-of-documentation.md` (generated documents). This file is the equivalent for **chat responses**.

## Purpose
After completing any task, the response must make it immediately obvious what — if anything — the user needs to do next. The user should never have to ask "what do you need from me?"

## Rule 1 — Brevity
- Report only what changed and what's needed next. No restating the task, no filler transitions, no unrequested rationale.
- Short declarative sentences over paragraphs. Cut anything that doesn't inform a decision or an action.

## Rule 2 — Approval References Must Be Exact
If the completed action requires the user to review or approve something in a document or plan:
- State the file path, relative to the project root.
- State the exact line number(s) requiring approval.
- Format: `path/to/file.md:L42` or `path/to/file.md (lines 40–45)`
- Never make the user hunt for what changed.

## Rule 3 — Enumerate Decisions Separately
If multiple items need approval or agreement, list them as a numbered list — one decision per item, no bundling. Each entry should be answerable with a single yes/no or choice.

## Rule 4 — Enumerate Questions Separately
If the user must answer questions, number them in their own list, separate from decisions. Each question must be self-contained — answerable without re-reading prior context.

## Rule 5 — Next Action Goes in Its Own Section
If a specific command or action is required to proceed, isolate it visually at the end of the response, in the exact syntax to run/type. Do not bury it in prose.

## Rule 6 — Report Sections Do Not Replace the Close
A report template's internal sections ("Follow-ups", "Remaining", "Recommended next") are report content. Any operator-required approval or question inside them must ALSO appear in the closing labeled sections below. The close is the contract; report sections never substitute for it.

## Output Template — Form B (input needed)
Use this skeleton whenever completing a task that requires further user input:

```
[1–3 sentence summary of what was done]

**Needs your approval:**
1. [Decision] — see path/to/file.md:L12
2. [Decision] — see path/to/file.md:L34

**Needs your answer:**
1. [Question]
2. [Question]

**Next step:**
`[exact command or action to run]`
```

## When Nothing Is Needed — Form A
If the task is fully complete and no user input is required, say so in a single line (e.g. `Next: nothing - work complete`). Do not render empty sections.

## Non-Negotiables
- Never mix decisions and questions in the same list.
- Never require the user to infer a file or line reference — always state it explicitly.
- Never end a response with an unstated expectation — if input is needed, it must appear in a labeled section.
- Never render a section (Approval / Answer / Next step) with nothing in it — omit unused sections entirely.
- One next-step command per response. If multiple sequential actions exist, present only the immediate one; mention later ones only if the user asks what comes after.