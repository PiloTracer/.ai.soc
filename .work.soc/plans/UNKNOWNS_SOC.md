# UNKNOWNS_SOC — SOC unknowns registry

**Updated:** 2026-07-20 · **Maintained by:** soc-bootstrap / soc-assessment

| ID | Question / blocker | Blocks | Owner | Status |
|----|-------------------|--------|-------|--------|
| U-SOC-1 | | | | Open |
| U-SOC-04 | Which keyring dependency (`keyring`, `keyrings.cryptfile`, or platform-specific) should back SOC-008-J's encrypted `~/.strix/cli-config.json` storage? Adding any of them changes `pyproject.toml` (protected) and isn't a unilateral decision. | SOC-008-J | Operator | Open |
| U-SOC-05 | Exact CPU/memory limits (if any) applied to sandbox containers by the pinned `openai-agents==0.14.6` SDK's `DockerSandboxClient` base implementation — this repo's own code (`strix/runtime/docker_client.py`) never sets `security_opt`/resource limits explicitly, so the effective default comes from a dependency not fully read line-by-line. | SOC-008-I | — | Open |
| U-SOC-06 | Should `--fail-on`/SOC-008-F's severity ranking, SOC-008-E's SARIF severity mapping, or SOC-009's per-run `strix.log` output be exercised against a real, live scan (not just unit tests) before being relied on for operator workflows or CI? No end-to-end scan was run in SOC-008 or SOC-009. | Confidence in SOC-008-E/F and SOC-009 logging for real use | — | Open |
| U-SOC-07 | Did any session before 2026-07-18 rely on `uv run mypy`/`uv run bandit`/`uv run pytest` output while the `.venv` script shebangs were broken (see HANDOFF_SOC "Key findings," SOC-008)? If so, that session's "checks passed" claims may have been silently wrong (bandit/mypy failed outright; pytest ran the wrong interpreter). Not something this session can retroactively verify. | Trust in any pre-2026-07-18 `uv run`-based verification claims | — | Open — informational, not blocking new work |
| U-SOC-08 | Does auto-defaulting `--output-dir` to `<local-target>/.work.soc` cover every operator workflow (URL-only targets, multi-target scans, resume without local path)? URL scans still require explicit `--output-dir`; not live-tested in SOC-009. | Confidence SOC-009 output routing matches operator expectations | — | Open |

## Review log

| Date | Reviewer | Action |
|------|---------|--------|
| 2026-06-30 | bootstrap | Initial template |
| 2026-07-18 | SOC-008 session | Added U-SOC-04 (keyring choice, blocks SOC-008-J), U-SOC-05 (sandbox resource limits, blocks SOC-008-I), U-SOC-06 (no live-scan verification of E/F), U-SOC-07 (retroactive trust question re: the broken `uv run` toolchain found and fixed this session) |
| 2026-07-20 | SOC-009 session | Extended U-SOC-06 to include SOC-009 `strix.log`; added U-SOC-08 (URL/multi-target output-dir auto-default not live-tested) |
