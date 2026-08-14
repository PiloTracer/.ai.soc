# Documentation Clarity Protocol

**Status:** Approved · 2026-08-14 (Agent OS `.ai`) · **Portable:** yes — adopt in any OS framework via `adopt-framework-improvements.md` (Phase 2)
**Enforced by (Agent OS):** `skills/SKILL_DEPENDENCIES.md` § Document clarity contract + `scripts/skill-functional-verify.py` (`DOC_GENERATING` set)
**Adoption target (any OS framework):** contract section in the target's `skills/SKILL_DEPENDENCIES.md` + a reference in every doc-generating `skill.md` + updated `templates/**`; wire the target's skill verifier if one exists, else record the enforcement gap as a follow-up

## Purpose
Every generated document (plan, proposal, tutorial, guide, reference, SPEC, ADR) must make it immediately obvious what it is, what state it is in, and what — if anything — the reader must do next. The reader should never have to ask "what is this for, and what do you need from me?"

Sibling protocol: `improve-clarity-of-responses.md` (chat responses). This file is the equivalent for **documents**.

## Rule 1 — Header answers three questions
Every document opens with a header block (≤4 lines) answering:
- **What** is this (one sentence).
- **Status** — `Draft` | `In review` | `Approved` | `Superseded` (+ date).
- **What it needs** — one line: the decision, review, or nothing.

## Rule 2 — Brevity
- No boilerplate, no filler transitions, no restating the obvious.
- Every section must inform a decision or an action; cut any that doesn't.
- Summary first: a reader who reads only the first 5 lines knows the gist.

## Rule 3 — Exact References
- Claims derived from code, plans, or other documents cite `path/to/file.md:L42` (relative to repo root).
- Quantitative claims are tagged `measured` | `estimated` | `assumption` | `unknown` (per `concepts/README.md` where the framework has one; the tags apply regardless).
- Never make the reader hunt for the source of a claim.

## Rule 4 — Decisions and Questions in Separate Lists
- **Decisions needed** — numbered; each answerable with a single yes/no or choice; each cites what is being decided (`path:L<n>` where applicable).
- **Open questions** — numbered, in their own list; each self-contained (answerable without re-reading the document).
- Never mix decisions and questions in one list. Never bury either in prose.

## Rule 5 — Next Action in Its Own Section
- Every document that requires follow-through ends with a `## Next action` section containing exactly **one** action, in the exact syntax to run/type (e.g. `@plan-master continue`).
- If multiple sequential actions exist, present only the immediate one.
- If nothing is needed, the document says so in one line (`Next action: none — <reason>`) instead of the section.

## Non-Negotiables
- Never render an empty or placeholder section — omit it or write `none` with a reason.
- Never leave a document without a Status line.
- Never end a document with an unstated expectation.
- One `Next action` per document.
- Template scaffolding text (`REPLACE:*`, instructional comments) must be stripped or filled before the document is presented as complete.
