# NEXT_SOC — Security OS tactical next action

## Recommended next

```
1. [NEXT] Run a live end-to-end scan (real repo or URL target) to confirm strix.log lands under target .work.soc and observe SOC-008-A/D/E behavior for real
2. [NEXT] SOC-008-I — sandbox hardening (Dockerfile NOPASSWD:ALL, always-on NET_ADMIN/NET_RAW, no resource limits) — needs a dedicated session with Docker build+smoke-test time budgeted (U-SOC-05 open). Deferred again in SOC-010 — changes to the attacker-facing sandbox image without a Docker build+smoke budget could silently break the running agent, which conflicts with the operator's "keep this framework easy to use" criterion.
3. [NEXT] SOC-008-J — encrypt-at-rest for ~/.strix/cli-config.json — needs operator's keyring-library choice before any code is written (U-SOC-04 open). Declined in SOC-010 — adds a dependency pin to protected `pyproject.toml` AND new operator-facing init/set-up UX, both of which add difficulty contrary to the SOC-010 task brief.
4. [DONE in SOC-010] Address path rebasing for `.cursorrules` (replace `/mnt/work/Projects/.ai*` with `{WORK_ROOT}/.ai*` + `WORK_ROOT:` resolution rules). Note: `.ai/opencode.json` already uses relative `../.ai.soc` paths and is portable as-is; consumer-project `opencode.json` (e.g. system-erp/opencode.json) is the consumer's responsibility, not `.ai.soc`'s.
5. [PENDING] Optionally rename Python module `strix/` → `soc/` — operator declined in SOC-010 ("may break the code, leave untouched").
```

## Current SOC iteration

| ID | Description | Status |
|----|-------------|--------|
| SOC-001 | License audit — Apache 2.0 → `.ai.soc` adoption | DONE |
| SOC-002 | Branding & identity migration (Strix → .ai.soc) | DONE |
| SOC-003 | NOTICE file + modification notices on all changed files | DONE |
| SOC-004 | Bootstrap templates for `.work.soc/` structure | DONE |
| SOC-005 | Path templating for portable `.ai.soc` framework | DONE in SOC-010 (`.cursorrules` portion) |
| SOC-006 | Register `.ai.soc` skills with `opencode.json` | DONE |
| SOC-007 | Remove tools-project integration (moved to parent `.ai`) | DONE |
| SOC-008 | Tool improvement plan (auth gate, honest scope language, secret scrubbing, SSRF guard, SARIF export, `--fail-on`, `make test`) — sub-items A–H | A,B,C,D,E,F,H DONE (uncommitted) · G declined by operator · I,J deferred |
| SOC-009 | Scan logging lifecycle + target `.work.soc` default output dir + `strix.log` in run dir | DONE (uncommitted, verified 2026-07-20) |
| SOC-010 | URL/IP/repo default output dir to `<cwd>/.work.soc` + run-name format regression tests + `.cursorrules` path templating (SOC-005) — verified 2026-07-27 | DONE (uncommitted) |

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
| SOC-010 URL default | URL/IP/repo targets without a local inference + without `--output-dir` now default to `<cwd>/.work.soc/strix_runs/<run-name>` (previously fell through to bare `<cwd>/strix_runs/<run-name>`). Operator-supplied `--output-dir` remains authoritative. Resume adds `<cwd>/.work.soc` first then legacy `<cwd>` as candidate bases so pre-SOC-010 URL runs stay resumable. — `strix/core/paths.py` (`configure_scan_output_dir` fallback, `output_dir_candidates` ordering) |
| SOC-010 run-name tests | `tests/test_run_name_format.py` pins operator-spec'd `YYYYMMDD-<slug>_<4hex>` format against the operator's exact example inputs (`/mnt/work/Projects/system-erp` → `-system-erp_<4hex>`; `http://localhost:13000` → `-localhost-13000_<4hex>`). `tests/test_scan_output_dir.py` extended with 4 new tests for the URL default + explicit-override + legacy resume discovery. |
| SOC-005 `.cursorrules` templating | Absolute `/mnt/work/Projects/.ai*` paths in `.cursorrules` replaced with `{WORK_ROOT}/.ai*` placeholders. A `WORK_ROOT:` resolution ladder (explicit `WORK_ROOT:` line → inferred parent of `.ai.soc` repo → `framework not installed here`) was added to the "Framework paths" section. `{UI_SKILLS_ROOT}`, `{UI_CONCEPTS_ROOT}`, `{SKILLS_ROOT}` (biz) placeholder resolutions updated to use `{WORK_ROOT}/...`. No user-facing complexity added: agents substitute `{WORK_ROOT}` at read time using the same convention `SOC_SOURCE` already established. |

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
