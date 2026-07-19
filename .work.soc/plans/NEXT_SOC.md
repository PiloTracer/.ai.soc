# NEXT_SOC — Security OS tactical next action

## Recommended next

```
1. [NEXT] Decide whether to commit SOC-008 (A,B,C,D,E,F,H) — dirty tree, no task ref provided yet
2. [NEXT] SOC-008-I — sandbox hardening (Dockerfile NOPASSWD:ALL, always-on NET_ADMIN/NET_RAW, no resource limits) — needs a dedicated session with Docker build+smoke-test time budgeted
3. [NEXT] SOC-008-J — encrypt-at-rest for ~/.strix/cli-config.json — needs operator's keyring-library choice before any code is written
4. [NEXT] Run a live end-to-end scan (real repo or URL target) to observe SOC-008-A's auth prompt, D's SSRF guard, and E's SARIF file firing for real — this session's verification was unit/static-analysis only
5. [PENDING] Address path rebasing for opencode.json / .cursorrules (replace /mnt/work/Project/ with {WORK_ROOT}) — status unconfirmed this session, carried over from SOC-005
6. [PENDING] Optionally rename Python module `strix/` → `soc/` (requires import refactoring — see analysis §7) — carried over, not touched this session
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
| SOC-007 | Remove tools-project integration (moved to parent `.ai`) | DONE |
| SOC-008 | Tool improvement plan (auth gate, honest scope language, secret scrubbing, SSRF guard, SARIF export, `--fail-on`, `make test`) — sub-items A–H | A,B,C,D,E,F,H DONE (uncommitted) · G declined by operator · I,J deferred |

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
| SOC-008-A/B | Authorization-confirmation gate (`--i-have-authorization`) + honest (non-"platform-verified") scope/authorization language — `strix/interface/main.py`, `strix/interface/utils.py`, `strix/core/inputs.py`, `strix/agents/prompts/system_prompt.jinja` |
| SOC-008-C | Secret-scrubbing log filter — new `strix/telemetry/secrets.py`, wired into `strix/telemetry/logging.py` |
| SOC-008-D | Cloud-metadata/link-local egress guard on the proxy's raw-request builder — `strix/tools/proxy/caido_api.py` |
| SOC-008-E | SARIF 2.1.0 export (`vulnerabilities.sarif`) — `strix/report/writer.py`, `strix/report/state.py` |
| SOC-008-F | `--fail-on {critical,high,medium,low,any,none}` exit-code threshold — `strix/interface/main.py` |
| SOC-008-H | `make test` target wired into `check-all`/`dev` — `Makefile` |
| Environment fix | `uv run pytest`/`mypy`/`bandit` were silently broken (stale `.venv` script shebangs pointing at a nonexistent moved-repo path) — fixed via `uv sync --reinstall`. See HANDOFF_SOC "Key findings" for detail; relevant to any session that ran `uv run mypy`/`bandit` before 2026-07-18. |

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
