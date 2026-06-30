# `.work.soc/` — Security Operations project memory

**Location:** `<repo-root>/.work.soc/` — sibling to `.ai/`, `.ai.ui/`, `.ai.biz/`.

**Purpose:** All artifacts for the `.ai.soc` Security OS framework — license analysis, risk assessments, compliance documents, security posture plans, and session handoff.

## Layout

| Path | Role |
|------|------|
| `context/HANDOFF_SOC.md` | SOC session state |
| `plans/NEXT_SOC.md` | SOC iteration carrier |
| `plans/UNKNOWNS_SOC.md` | Open questions & blockers |
| `analysis/` | License audits, threat models, compliance reviews |

## Relationship

`.ai.soc` is the **Security Operations Center** companion to:

| Framework | Domain | Path |
|-----------|--------|------|
| Agent OS | Project SDLC and backend | `.ai/` |
| UI Design OS | Front-end / design system | `.ai.ui/` |
| Business OS | Strategy, brand, content | `.ai.biz/` |
| **Security OS (this)** | **Security testing, vulnerability management, compliance** | **`.ai.soc/`** |

Session bookends: `@session-control` (`.ai/`).
