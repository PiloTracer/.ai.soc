# SOC OS — Skill dependency graph

**Purpose:** Single source of truth for which skill may run before which.

## Operator handoff contract (mandatory for every skill)

<a id="operator-handoff-contract"></a>

Implements the operator-provided **Response Clarity Protocol** (origin: `.work.soc/prompts/improve-clarity-of-responses.md`). Every skill response that ends a turn must be **terse** and close with exactly one of two forms. No skill may invent a third.

**Form A — nothing needed:** a single line stating no user input is required (e.g. `Next: nothing - work complete`). Do not render empty sections.

**Form B — input needed:** end the response with this skeleton; omit any section that has nothing in it; nothing after `**Next step:**`:

```
**Needs your approval:**
1. <Decision> — see path/to/file.md:L42
2. <Decision> — see path/to/file.md (lines 40–45)

**Needs your answer:**
1. <Question>
2. <Question>

**Next step:**
`<exact command or action to run>`
```

Rules:

1. **Brevity.** Report only what changed and what's needed next. No restating the task, no filler transitions, no unrequested rationale. Short declarative sentences.
2. **Exact references.** Approvals cite the project-root-relative path **and** line number(s): `path/to/file.md:L42` or `path/to/file.md (lines 40–45)`. Never make the operator hunt.
3. **Decisions and questions are separate lists.** One decision per numbered item, each answerable with a single yes/no or choice. Questions numbered in their own list, self-contained — answerable without re-reading prior context. Never mix the two in one list.
4. **One next step.** Exactly one command/action, isolated at the end in exact syntax. If multiple sequential actions exist, present only the immediate one; mention later ones only if the operator asks.
5. **Nothing buried, nothing empty.** Never end a response with an unstated expectation; never render an empty section; never hide an operator action inside a paragraph.
6. **Report-internal sections don't replace the close.** A template's "Follow-ups" / "Remaining" / "Recommended next" section is report content; any operator-required approval or question in it must ALSO appear in the Form B close.

**Enforcement:** `scripts/framework-verify.sh` fails any `skills/*/skill.md` that does not reference this contract (`Operator handoff`).

## Document clarity contract (mandatory for document-generating skills)

<a id="document-clarity-contract"></a>

Implements the operator-provided **Documentation Clarity Protocol** (origin: `.work.soc/prompts/improve-clarity-of-documentation.md`). Applies to every document a skill generates or maintains: HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC, analyses, assessments, reports, ADRs.

1. **Header answers three questions (≤4 lines):** what it is (one sentence) · **Status** (`Draft` | `In review` | `Approved` | `Superseded` + date) · what it needs (one line, or `nothing`).
2. **Brevity.** Summary first; every section informs a decision or an action; no boilerplate.
3. **Exact references.** Claims cite `path/to/file.md:L42`; quantitative claims tagged `measured` | `estimated` | `assumption` | `unknown`.
4. **Decisions and questions in separate numbered lists** — `## Decisions needed` vs `## Open questions`; never mixed, never buried in prose; each item self-contained.
5. **`## Next action` section** — exactly one action in exact syntax, or one line `Next action: none — <reason>`.
6. **Non-negotiables:** no empty/placeholder sections (omit or write `none` + reason); no document without a Status line; no unstated expectations; template scaffolding (`REPLACE:*`, instructional comments) stripped or filled before a document is presented as complete.

**Enforcement:** `scripts/framework-verify.sh` fails any document-generating skill (`soc-session`) whose `skill.md` does not reference this contract (`Document clarity`).

### Work tree path resolution

| Placeholder | Resolved path |
|-------------|---------------|
| `{WORK_SOC_ROOT}` | `.work.soc/` |
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |
| `{NEXT_SOC}` | `.work.soc/plans/NEXT_SOC.md` |
| `{UNKNOWNS_SOC}` | `.work.soc/plans/UNKNOWNS_SOC.md` |

### Dependency matrix

| Skill / mode | Depends on | Gate |
|--------------|------------|------|
| **soc-deploy-basic** `bootstrap` / `update` | Source `templates/cursorrules.soc.snippet.template` readable | Required |
| **soc-deploy-basic** `status` | - | Read-only |
| **soc-deploy-files** `copy` | Target parent dir exists | Required |
| **soc-deploy-files** `status` | - | Read-only |
| **soc-session** `start` | `{HANDOFF_SOC}` | Recommended |
| **soc-session** `close` | Prior `start` or dirty tree | - |
| **soc-session** `commit` / `commit push` | C1 secrets scan pass; invocation names `commit` | Git write; scope: full repo in framework source repo, `.work.soc/` only in targets |
| **soc-session** `context` | - | Read-only |
| **soc-session** `status` | - | Read-only |
| **soc-director** `- <free-text>` | `{HANDOFF_SOC}` readable | Recommended |
| **soc-director** `status` | - | Read-only |
| **soc-gateway** `status` | - | Read-only |

### Blocked report shape

When a gate stops execution:

```markdown
## @<skill> <command> - blocked (prerequisite)

**Required:** <state or upstream step>
**Detected:** <what's actually present>
**Run first:** `<exact command to fix>`
```

### Canonical verb vocabulary

| Canonical verb | Meaning | Skills |
|----------------|---------|--------|
| `status` | Read-only state | soc-session, soc-director, soc-gateway, soc-deploy-basic |
| `start` / `close` / `context` / `commit` | Session lifecycle | soc-session |
| `bootstrap` / `update` | Deploy lifecycle | soc-deploy-basic |
| `copy` | File deploy | soc-deploy-files |
| `- <free-text>` | Free-text routing | soc-director |
