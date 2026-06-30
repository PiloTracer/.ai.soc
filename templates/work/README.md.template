# `.work.soc/` — Security Operations project memory

**Purpose:** All **project-specific** SOC artifacts: license analysis, threat models, compliance reviews, risk assessments, security posture plans, and session handoff.

**Agnostic** process (skills, standards, concepts, guides) lives under **`.ai.soc/`** only.

## Layout

| Path | Contents |
|------|----------|
| `.work.soc/plans/` | SOC plans, `NEXT_SOC.md`, unknowns registry |
| `.work.soc/analysis/` | License audits, vulnerability reports, threat models, compliance reviews |
| `.work.soc/assessments/` | Per-target security assessments and penetration test reports |
| `.work.soc/prompts/` | Decision questionnaires for SOC scoping |
| `.work.soc/decisions/` | Security ADRs (`YYYYMMDD-NNN-*.md`) |
| `.work.soc/context/` | `HANDOFF_SOC.md` — SOC session boundary |

## Placeholder map

Configured in `.cursorrules` § `.ai.soc`:

| Placeholder | Resolves to |
|-------------|-------------|
| `{WORK_SOC_ROOT}` | `.work.soc/` |
| `{SOC_PLANS_ROOT}` | `.work.soc/plans/` |
| `{SOC_ANALYSIS_ROOT}` | `.work.soc/analysis/` |
| `{SOC_ITERATION_CARRIER}` | `.work.soc/plans/NEXT_SOC.md` |
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |

## Quick pick-up

1. `.work.soc/context/HANDOFF_SOC.md`
2. `.work.soc/plans/NEXT_SOC.md`

Operator entry: `.ai.soc/START_HERE.md`

## Bootstrap

If this tree was created empty, run from repo root:

```bash
bash .ai.soc/templates/bootstrap.sh
```

Or invoke `@soc-bootstrap init`.
