# `.work/` - project working tree

**Purpose:** All **project-specific** artifacts: plans, SPECs, ADRs, prompts, and session handoff.

**Agnostic** process (skills, standards, concepts, guides) lives under **`.ai/`** only.

## Layout

| Path | Contents |
|------|----------|
| `.work/plans/` | Foundation docs (`*-01-*` … `*-04-*`), master plan (`full/*-full-plan.md`), registries, `NEXT.md`, operations runbooks |
| `.work/features/<slug>/` | Feature SPECs, amendments, `CHANGELOG.md` per FEATURE_STANDARD |
| `.work/prompts/` | Decision questionnaires; optional user scratch (`initial.md` - **not read by skills** unless user names it) |
| `.work/decisions/` | ADRs (`YYYYMMDD-NNN-*.md`) |
| `.work/context/` | `HANDOFF.md` - read/write via `@session-control` |

## Quick pick-up

1. `.work/context/HANDOFF.md`
2. `.work/plans/NEXT.md`

Operator entry: `.ai/START_HERE.md`

## Bootstrap

Created by `@project-bootstrap init`. Foundation docs **01–04** are created by `@plan-foundation greenfield`.
