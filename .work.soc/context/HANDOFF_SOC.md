# HANDOFF_SOC — Security OS session state

**Session:** SOC-009 — scan logging + target run-directory output
**Date:** 2026-07-20
**Status:** Closed — committed and pushed (SOC-009, 2026-07-20)

## Summary

Operator asked where scan errors are logged, then required **all scan errors** to land in per-run `strix.log`, and **logs/reports under the target's run directory** (not the `.ai.soc` repo cwd). Shipped three related changes in one pass:

1. **Early + durable scan logging** — `setup_scan_logging()` now activates as soon as `run_name` is known (before Docker/env/LLM warm-up). Logging stays open for the full process; `teardown_scan_logging()` runs in `main()` finally. Runner no longer tears down handlers mid-flight. CLI/main exception paths call `logger.exception`.
2. **Target-default output directory** — local path targets auto-default `--output-dir` to `<target>/.work.soc`. Resume discovers prior runs under target `.work.soc` without re-passing `--output-dir`. `output_base` persisted in `run.json`.
3. **Operator quick reference** — `.quick/run-directly-no-limits.md` updated with simplified commands and log paths.

## Completed

- [x] `strix/telemetry/logging.py` — idempotent `setup_scan_logging`, `teardown_scan_logging`, active-run tracking
- [x] `strix/interface/main.py` — early logging lifecycle; `configure_scan_output_dir`; diff-scope errors logged; `output_base` in `run.json`
- [x] `strix/core/paths.py` — `resolve_default_output_dir`, `find_run_dir`, `configure_scan_output_dir`, `get_output_dir`
- [x] `strix/interface/cli.py` — `logger.exception` on scan failure
- [x] `strix/core/runner.py` — logging lifecycle owned by `main()` (no mid-run teardown)
- [x] `tests/test_logging_scrub.py` — idempotent logging setup test
- [x] `tests/test_scan_output_dir.py` — target `.work.soc` default + resume discovery (4 tests)
- [x] `.quick/run-directly-no-limits.md` — repo command omits `--output-dir`; documents `strix.log` path

## Verification (2026-07-20)

| Gate | Result |
|------|--------|
| `touch-scope-verify.sh` | PASS (6 files) |
| `blast-radius-check.sh` | PASS (6 files, 2 areas: `strix/`, `tests/`) |
| `gate-verify.sh` | PASS |
| `framework-verify.sh` | PASS |
| `make check-all` | PASS — **151/151** pytest; ruff; mypy; pyright; bandit |

## Key paths

| Artifact | Location |
|----------|----------|
| Per-run log | `<output-dir>/strix_runs/<run-name>/strix.log` |
| Run metadata | `<output-dir>/strix_runs/<run-name>/run.json` |
| Default output (local target) | `<target>/.work.soc` |
| URL scans | still require `--output-dir` (no inferable project path) |

## Open

- **Committed/pushed** 2026-07-20 — see git log on `main`.
- **Unverified live:** no end-to-end scan run this session to confirm log file appears under target `.work.soc` during a real gateway invocation (unit/static verification only). See U-SOC-06, U-SOC-08.
- **SOC-008 carryover** (I/J, live E2E) unchanged — see `NEXT_SOC.md`.
