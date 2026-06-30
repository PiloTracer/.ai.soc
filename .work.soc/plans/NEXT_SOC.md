# NEXT_SOC — Security OS tactical next action

## Recommended next

```
1. [DONE] Review license analysis: .work.soc/analysis/20260629-STRIX-to-AI-SOC-LICENSE-ANALYSIS.md
2. [DONE] Branding migration: pyproject.toml, README, .cursorrules, logos, docs
3. [NEXT] Address path rebasin for opencode.json / .cursorrules (replace /mnt/work/Project/ with {WORK_ROOT})
4. [DONE] Register `.ai.soc` skills with `opencode.json` and `.cursorrules` frameworks section
5. [NEXT] Optionally rename Python module `strix/` → `soc/` (requires import refactoring — see analysis §7)
```

## Current SOC iteration

| ID | Description | Status |
|----|-------------|--------|
| SOC-001 | License audit — Apache 2.0 → `.ai.soc` adoption | DONE |
| SOC-002 | Branding & identity migration (Strix → .ai.soc) | DONE |
| SOC-003 | NOTICE file + modification notices on all changed files | DONE |
| SOC-004 | Bootstrap templates for `.work.soc/` structure | DONE |
| SOC-005 | Path templating for portable `.ai.soc` framework | PENDING |
| SOC-006 | Register `.ai.soc` skills with `opencode.json` | DONE |

## Completed work

| Item | Detail |
|------|--------|
| NOTICE file | `NOTICE` at repo root with attribution + change log |
| Package rename | `pyproject.toml`: `strix-agent` → `ai-soc`, CLI `soc` added |
| .cursorrules identity | Updated from `strix-agent` to `.ai.soc` |
| README | Rebranded, removed Strix logos/badges, added attribution |
| Docs (25 .mdx files) | Product name + CLI command updated |
| Logo removal | `.github/logo.png`, `.github/screenshot.png`, `docs/images/*` removed |
| Gateway script | `gateway.sh` APP renamed, env vars preserved; `scripts/install.sh` removed (not needed — install via `uv sync`) |
| Templates | `templates/work/` + `templates/bootstrap.sh` created |
| Modification notices | Added to every changed file; `NOTICE` lists all modifications |
| session-soc skill | `skills/session-soc/skill.md` created; `.cursorrules` SOC section updated |

## What was intentionally NOT changed

| Item | Reason |
|------|--------|
| `STRIX_LLM` env var | Python code reads it (`strix/config/settings.py`) — not trademark use |
| `strix/` module directory | Python import path — internal only, not brand presentation |
| `strix_runs/` output directory | Python code writes to it — internal only |
| `~/.strix/` config directory | Python code reads from it — internal only |

## Unknowns

| ID | Question | Owner |
|----|----------|-------|
| U-SOC-01 | Does `.ai.soc` name collide with any existing `.work.*` in sibling projects? | — |
| U-SOC-02 | Should `.ai.soc` be a framework directory (like `.ai/`) or just a skill set? | — |
| U-SOC-03 | Should env vars be renamed (STRIX_LLM → SOC_LLM) in Python code too? That's a separate code migration. | — |
