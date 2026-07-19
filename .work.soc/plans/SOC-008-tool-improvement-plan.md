# SOC-008 — Tool improvement plan (grow, harden, add value)

**Date:** 2026-07-18
**Requested by:** operator, via `@soc-director`
**Scope:** improvements to **the `.ai.soc` tool itself** (the Python `strix/` agent framework that ships with this repo) — NOT a pentest plan for an external target.
**Constraint:** every item below is scoped to be implementable, tested, and verified in a single session. Nothing here requires a multi-day effort, a new dependency, or a Docker image rebuild.
**Evidence policy:** every claim below cites `file:line`. Where a claim could not be verified by reading code, it is marked **Unverified** rather than asserted. No item is based on assumption about what the tool "probably" does.

---

## 0. How this plan was produced

1. Full-repo survey (`pyproject.toml`, `Makefile`, `.github/workflows/`, `gateway.sh`, `containers/Dockerfile`, `.pre-commit-config.yaml`).
2. Thorough codebase exploration of `strix/` (runtime/sandbox, tools, target/scope handling, LLM config, reporting, scan modes, telemetry, agent loop, tests, CI) via a dedicated explore pass — findings below were then **independently re-verified by direct file reads** before being included (Dockerfile, `docker_client.py`, `inputs.py`, `system_prompt.jinja`, `caido_api.py`, CI workflow YAML, `main.py`, `writer.py`, `logging.py`, `loader.py`, existing test files).
3. One external verification (SARIF 2.1.0 schema shape) via live docs, since that item proposes new file syntax this codebase doesn't currently emit.

## 1. Assumption ledger

**Confirmed facts (file evidence):**
- No GitHub Actions workflow runs `pytest`, `mypy`, `ruff`, or `bandit` on any PR or push — `.github/workflows/framework-verify.yml:1-17` only runs `scripts/framework-verify.sh` (deploy-script self-tests), and `.github/workflows/build-release.yml:1-52` only builds PyInstaller binaries on tag push. `make check-all` (`Makefile:53-54`) runs format+lint+type+security but **not** `pytest`.
- The scan-scope object sent to the LLM claims `"authorization_source": "strix_platform_verified_targets"` (`strix/core/inputs.py:104`) and the system prompt tells the agent this scope is "platform-verified" and to "NEVER wait for approval or authorization" (`strix/agents/prompts/system_prompt.jinja:53-58,84`). In this self-hosted `.ai.soc` build there is no platform and no verification step — `authorized` is built directly, unmodified, from whatever string the operator passed to `--target` (`strix/core/inputs.py:90-100`, `strix/interface/main.py:524-536`). The claim is false in this deployment context.
- No code path asks the operator to confirm ownership/authorization for a target before a scan starts. `--target` accepts any URL/domain/IP and proceeds straight to Docker pull + active testing (`strix/interface/main.py:517-561`).
- `strix/telemetry/logging.py` (full file read) has no secret-redaction filter. Log lines are written verbatim to `{run_dir}/strix.log` and stderr via `_StrixContextFilter`, which only stamps `scan_id`/`agent_id` (`strix/telemetry/logging.py:39-43`). A grep for `redact|scrub|mask_secret` across `strix/` returns exactly one hit, and it's in a target-facing skill doc (`strix/skills/vulnerabilities/information_disclosure.md`) about vulnerabilities the tool looks for in *targets* — not a safeguard for the tool's own logs.
- `strix/tools/proxy/caido_api.py::build_raw_request` (`caido_api.py:140-166`) builds a raw HTTP connection from `ConnectionInfoInput(host=parsed.hostname, port=...)` with no check against link-local/cloud-metadata addresses. It only validates that a scheme and netloc are present (`caido_api.py:147-149`).
- `strix/interface/utils.py::_is_localhost_host` (`utils.py:1333-1348`) already exists and is a strict loopback check (`localhost`, `0.0.0.0`, `::1`, `127.0.0.0/8`) — it does **not** cover link-local (`169.254.0.0/16`, `fe80::/10`) or cloud-metadata hosts. It's reused by `rewrite_localhost_targets` (`utils.py:1351-1371`).
- Exit code on a completed non-interactive scan is `2` if **any** vulnerability of **any** severity was filed, with no way to tune the threshold (`strix/interface/main.py:855-858`). There is no `--fail-on` / severity-threshold flag today (confirmed via `parse_arguments()`, `main.py:320-481`).
- `strix/report/writer.py` (full file read) emits `penetration_test_report.md`, `vulnerabilities/<id>.md`, `vulnerabilities.csv`, `vulnerabilities.json` — no SARIF output. `strix/report/state.py:333-336` is the single call site for both writers.
- `strix/config/loader.py::persist_current` (`loader.py:56-75`) writes resolved env vars — including `LLM_API_KEY` — to `~/.strix/cli-config.json` in plaintext JSON, `chmod 0o600` after write (`loader.py:74-75`). Confirmed no encryption.
- `containers/Dockerfile:10-12` grants the sandbox's non-root `pentester` user passwordless root (`NOPASSWD:ALL`). `strix/runtime/docker_client.py:107-114` unconditionally appends `NET_ADMIN`/`NET_RAW` capabilities to every sandbox container and (`docker_client.py:116-117`) adds a `host.docker.internal` route to every container. No `network_mode`, cpu/mem limits, or seccomp override is set by this repo's code (Docker/SDK defaults apply — see Unknowns).
- Existing test suite (`tests/*.py`, 6 files) covers: budget enforcement, root-task/child-input string building, local-source sizing/dedup, resume/rate-limit behavior. It does **not** cover `build_scope_context`, `caido_api.py`, `strix/report/writer.py`, or `strix/telemetry/logging.py` — confirmed by reading all 6 test files and grepping for the relevant imports.
- `strix/tools/reporting/tool.py:142-298` already has non-trivial validation quality: required-field checks, CVSS 3.1 vector construction via the `cvss` dependency, CVE/CWE regex validation, path-traversal rejection on `code_locations[].file`, and an LLM-judge dedupe step (`strix/report/dedupe.py`, referenced at `reporting/tool.py:228-259`). This is genuinely solid — not a target for this plan.

**Inferences (plausible, not fully proven — flagged, not treated as fact):**
- The `"strix_platform_verified_targets"` string is very likely a holdover from the original hosted-SaaS product (where a real platform-side verification step may exist) that didn't get updated for the self-hosted `.ai.soc`/OSS execution path. Not something I can confirm without the original vendor's SaaS source, but irrelevant to the fix: in *this* codebase, today, the claim is false, which is what matters.
- Docker's default seccomp/AppArmor profile likely still applies unless the FUSE/SYS_ADMIN path is triggered (`docker_client.py:90-100`), since this repo's code never sets `security_opt` in the common case — but the *effective* default comes from the pinned `openai-agents==0.14.6` SDK's `DockerSandboxClient` base implementation, which I did not fully read line-by-line.

**Unknowns (explicitly not resolved by this plan):**
- Exact CPU/memory limits (if any) applied by the SDK's `DockerSandboxClient` base class — would require reading `agents.sandbox.sandboxes.docker` inside the pinned SDK. Not blocking for this plan; flagged for the deferred sandbox-hardening item.
- Whether the original Strix SaaS platform genuinely performs target verification (irrelevant to correctness of this plan's fix, noted for completeness only).

---

## 2. Improvement matrix

Legend — **Value**: how much this measurably improves safety or capability. **Risk if left alone**: what stays broken/exposed. **Effort**: size of the single-session task. **Touches protected file?**: per `.cursorrules` "Protected Files" list — if yes, this plan **stops and asks** before implementing it, it does not proceed unilaterally.

| ID | Improvement | Category | Value | Risk if left alone | Effort | Files (primary) | Protected file? | Status |
|----|---|---|---|---|---|---|---|---|
| **SOC-008-A** | Operator authorization-confirmation gate before scanning any non-loopback URL/domain/IP | Safety | High | Anyone can point the tool at a domain/IP they don't own with zero friction; the LLM is explicitly told scope is "already verified," so it will not push back either | M | `strix/interface/main.py`, `strix/interface/utils.py` | No | ✅ Done |
| **SOC-008-B** | Replace the false "platform-verified" scope claim with an honest, evidence-backed label tied to SOC-008-A's confirmation | Correctness / Safety | High | Tool actively lies to its own LLM about how scope was established — a correctness bug with safety consequences (false confidence, harder incident review) | S | `strix/core/inputs.py`, `strix/agents/prompts/system_prompt.jinja` | No | ✅ Done |
| **SOC-008-C** | Secret-scrubbing log filter (redact API keys / bearer tokens / common credential patterns before they hit `strix.log` or stderr) | Safety / Privacy | High | Full LLM API keys, `Authorization` header values, and other secrets the agent handles during a scan can land verbatim in on-disk logs shipped in bug reports, CI artifacts, screen shares | M | `strix/telemetry/logging.py` | No | ✅ Done |
| **SOC-008-D** | Block the tool's own outbound proxy replay from directly targeting cloud-metadata / link-local addresses (CWE-918 defense-in-depth) | Safety | Medium-High | If the sandbox network can route to a cloud metadata endpoint (a documented real-world risk class, e.g. AWS/GCP/Azure IMDS via containers), a compromised or confused agent could exfiltrate the **operator's own cloud credentials** — distinct from, and in addition to, testing a target's SSRF bugs | S-M | `strix/tools/proxy/caido_api.py` | No | ✅ Done |
| **SOC-008-E** | SARIF 2.1.0 export (`vulnerabilities.sarif`) alongside existing `.md`/`.csv`/`.json` reports | Value-add | Medium | Findings can't be ingested by GitHub Code Scanning / most CI security dashboards without a manual conversion step today | M | `strix/report/writer.py`, `strix/report/state.py` | No | ✅ Done |
| **SOC-008-F** | `--fail-on {critical,high,medium,low,any,none}` exit-code threshold (default `any`, preserving current behavior) | Value-add / CI ergonomics | Medium | CI pipelines have only one option today: fail the build on *any* finding including informational ones, or ignore exit code entirely and lose the signal | S | `strix/interface/main.py` | No | ✅ Done |
| **SOC-008-H** | `make test` target wired into `check-all`/`dev` | Quality gate | Medium | Convenience only — `uv run pytest` already worked standalone, but `check-all`/`dev` silently never ran tests | XS | `Makefile` | **Yes** | ✅ Done (operator approved modifying protected files) |
| SOC-008-G *(declined by operator)* | CI workflow that runs `pytest` + `ruff` + `mypy` + `bandit` on every PR | Quality gate | High | Regressions in `strix/` ship without any automated check; `make check-all` isn't run anywhere in CI today | S | new `.github/workflows/ci.yml` | **Yes** — `.github/workflows/*` | ⛔ Not implemented — operator explicitly declined ("I don't trust github's CI workflows... let's avoid touching any github workflows stuff") |
| SOC-008-I *(out of scope this session)* | Sandbox hardening: scope `sudo` instead of blanket `NOPASSWD:ALL`, review always-on `NET_ADMIN`/`NET_RAW`, set explicit resource limits | Safety | High (but high blast-radius) | Passwordless root + elevated network caps in every sandbox by default | L, needs live Docker build+smoke-test cycle | `containers/Dockerfile`, `strix/runtime/docker_client.py` | **Yes** (`Containers/Dockerfile`) | Not started — needs a dedicated session with Docker build time budgeted |
| SOC-008-J *(out of scope this session)* | Encrypt-at-rest for persisted API keys (`~/.strix/cli-config.json`) | Safety | Medium | Plaintext secret on disk today (mitigated by `0o600`, but not encrypted) | L, needs a keyring dependency decision | `strix/config/loader.py` | No, but needs a dependency choice — asked, not assumed | Not started — needs operator's keyring-library choice |

**A–F and H shipped this session** (7 of 8 in-scope items). **G was explicitly declined by the operator** and is not implemented, by instruction, not oversight — see the transcript. I and J remain out of scope per §5, unchanged.

---

## 3. Detailed specs (SOC-008-A through F)

### SOC-008-A — Authorization-confirmation gate

**Problem:** `strix/interface/main.py:517-561` builds `args.targets_info` from `--target` with no consent step. `web_application` and `ip_address` targets go straight to active testing (proxy replay, exploitation PoCs per `strix/tools/reporting/tool.py:317-321`) against whatever the operator typed.

**Design:**
- New helper `strix/interface/utils.py::needs_authorization_confirmation(target_info) -> bool` — `True` for `web_application`/`ip_address` targets whose host fails `_is_localhost_host` (reuses the existing helper at `utils.py:1333-1348`, so loopback dev targets are never gated — consistent with the tool's existing localhost-rewrite feature). `local_code` and `repository` targets are never gated (cloning/reading code is not "testing" a third party's live system).
- New CLI flag `--i-have-authorization` (`store_true`) on the parser in `strix/interface/main.py::parse_arguments`.
- New function `strix/interface/main.py::confirm_target_authorization(args, parser)` called right after `args.targets_info` is finalized (after line 546, before the oversized-local-target check):
  - Collect gated targets via `needs_authorization_confirmation`.
  - If none: no-op, proceed silently (zero friction for the common local-code/repo-you-own case).
  - If any, and `--i-have-authorization` was passed: log an INFO line recording the operator's attestation (target list + timestamp) into the run record, proceed.
  - If any, and non-interactive (`-n`) without the flag: `parser.error(...)` listing the gated targets and the exact flag to add — **hard fail before any Docker pull or LLM call**.
  - If any, and interactive without the flag: print the gated target list and prompt `Type "yes" to confirm you own or have explicit written authorization to test these targets: `. Anything other than `yes` aborts with exit code 1 before the TUI starts.
- Record the attestation (`i_have_authorization: true/false`, `confirmed_interactively: true/false`) in `_persist_run_record` (`main.py:566-584`) so it's part of `run.json` for audit/session review.

**Acceptance criteria:**
- `soc -t ./local-repo` (no gated targets): unchanged behavior, no prompt, no flag needed.
- `soc -t https://example.com -n` (no flag): exits non-zero via `parser.error` before Docker/LLM init; message names the flag.
- `soc -t https://example.com -n --i-have-authorization`: proceeds.
- `soc -t https://example.com` (interactive, declines prompt): exits 1, no scan started.
- `soc -t http://localhost:3000 -n` (no flag): proceeds — loopback is exempt.

**Test plan:** new `tests/test_authorization_gate.py` — unit tests on `needs_authorization_confirmation` (parametrized over `web_application`/`ip_address`/`local_code`/`repository` × loopback/non-loopback) and on `confirm_target_authorization` (mock `parser.error` to raise, assert it's called for the missing-flag non-interactive case and not called for the flag-present / loopback-only / no-gated-targets cases; simulate interactive decline via monkeypatched `input`).

---

### SOC-008-B — Honest scope/authorization language

**Problem:** `strix/core/inputs.py:102-107` labels scope `"authorization_source": "strix_platform_verified_targets"` and `system_prompt.jinja:55` echoes it verbatim to the LLM as `Authorization source: strix_platform_verified_targets`. There is no platform and no verification in this codebase (§1). Combined with `system_prompt.jinja:84` ("NEVER wait for approval or authorization — operate with full autonomy"), the agent is told a falsehood that also reads as "don't second-guess scope, ever."

**Design (depends on SOC-008-A landing first — it's what makes the new label true):**
- `build_scope_context` (`strix/core/inputs.py:82-107`) gains an `authorization: dict` parameter (attestation info from SOC-008-A's run record) and changes the label to `"authorization_source": "operator_attested_at_launch"`, adding `"attested_by": "operator"` and `"attested_interactively": <bool>`.
- `system_prompt.jinja:51-59` wording changes from "platform-verified" / "Strix platform" to: scope was confirmed by the human operator who launched this scan (not by this agent, and not by an automated platform check); the agent must still stay within the listed targets and must not expand scope from user chat text (that part of the existing guidance is correct and unchanged).
- `system_prompt.jinja:84` reworded from "NEVER wait for approval or authorization" to something that keeps the intended meaning (don't stall mid-scan asking the user to re-confirm things already confirmed at launch) without implying the agent should suppress ethical/scope objections it might otherwise raise.

**Acceptance criteria:** `build_scope_context` output no longer contains the string `strix_platform_verified_targets` or `strix_platform`; system prompt no longer claims platform verification; existing scope-restriction behavior (agent must not expand beyond listed targets) is unchanged in wording/intent.

**Test plan:** extend `tests/test_inputs.py` (currently tests `build_root_task`/`child_initial_input` only, not `build_scope_context` — new coverage, not a rewrite) with cases asserting the new field names/values for both the attested and not-yet-attested shapes.

---

### SOC-008-C — Secret-scrubbing log filter

**Problem:** `strix/telemetry/logging.py` (full file, 143 lines) attaches `_StrixContextFilter` (stamps `scan_id`/`agent_id` only) to both the file handler and the stderr handler (`logging.py:112-122`). Nothing scrubs message content. Tool output (shell commands, HTTP headers replayed via the proxy tool, LLM tool-call arguments) flows into these loggers and is written verbatim to `{run_dir}/strix.log`.

**Design:**
- New `strix/telemetry/secrets.py` with a pure function `scrub(text: str) -> str` applying a small, well-scoped set of regexes for common high-confidence secret shapes: `Authorization:\s*Bearer\s+\S+`, `sk-[A-Za-z0-9]{20,}` (OpenAI-style), `AKIA[0-9A-Z]{16}` (AWS access key ID), generic `(api[_-]?key|token|secret|password)\s*[=:]\s*\S+` (case-insensitive, quoted or bare). Each match replaced with `[REDACTED]`, preserving the key name where it's a `key=value` pattern so logs stay diagnosable (e.g. `api_key=[REDACTED]` not a fully blanked line).
- New `_SecretScrubFilter(logging.Filter)` that rewrites `record.msg`/`record.args` (formats first if `args` present, to avoid breaking `%`-style formatting) through `scrub()`. Added alongside `_StrixContextFilter` on both handlers in `setup_scan_logging` (`logging.py:112-122`).
- No behavior change to log routing, levels, or file layout — purely a content transform.

**Acceptance criteria:** a log record containing `Authorization: Bearer sk-abcdef0123456789ABCDEF` is written to `strix.log` as `Authorization: Bearer [REDACTED]`; a log record with no secret-shaped substring is byte-identical to today's output (no false-positive redaction of normal text, e.g. it must not redact something like `The user's password field was empty` — validated by an explicit non-match test).

**Test plan:** new `tests/test_logging_scrub.py` — unit tests on `scrub()` directly (parametrized positive/negative cases) plus one integration test that calls `setup_scan_logging(tmp_path)`, logs a secret-bearing message through the `strix` logger, reads back `tmp_path/strix.log`, and asserts the secret substring is absent while `[REDACTED]` is present.

---

### SOC-008-D — Cloud-metadata / link-local egress guard on the proxy replay tool

**Problem:** `strix/tools/proxy/caido_api.py::build_raw_request` (`caido_api.py:140-166`) turns any `(method, url, headers, body)` the agent supplies into a raw socket connect target (`ConnectionInfoInput(host=parsed.hostname, port=...)`, `caido_api.py:165`) with only a "scheme+netloc present" check (`caido_api.py:147-149`). Nothing stops the connection host from being a well-known cloud-metadata address. This is a distinct risk from "testing the target's SSRF" (where the *target application* — not this tool — is tricked into calling metadata endpoints server-side): here the tool itself would be the direct caller, which is never a legitimate step in any pentest methodology and only creates exposure for whichever cloud VM the sandbox happens to run on.

**Design:**
- New `strix/tools/proxy/ssrf_guard.py` with `is_blocked_connect_target(host: str) -> bool`, covering, by literal/IP-range match only (no DNS-rebinding heuristics — this is a narrow, high-confidence blocklist, not a general SSRF filter):
  - IPv4 link-local `169.254.0.0/16` (covers AWS/Azure/DigitalOcean/Alibaba-style IMDS at `169.254.169.254`, and Azure IMDS).
  - IPv6 link-local `fe80::/10`, plus the literal AWS IMDSv2 IPv6 address `fd00:ec2::254`.
  - Hostname literals `metadata.google.internal`, `metadata`, `metadata.internal` (GCP conventions).
  - Alibaba Cloud metadata IP `100.100.100.200`.
  - Deliberately **not** blocking RFC1918/loopback — those remain valid pentest targets (internal network assessments, `host.docker.internal`-rewritten localhost apps) and are already the tool's documented use case.
- `build_raw_request` calls the guard right after parsing `host = parsed.hostname or ""` (`caido_api.py:151`) and raises `ValueError(f"Refusing to connect directly to a cloud-metadata/link-local address: {host}")` before constructing `ConnectionInfoInput`. This surfaces to the agent as a tool error, not a silent no-op, so it's visible in the run log and doesn't look like a network failure.

**Acceptance criteria:** `build_raw_request(method="GET", url="http://169.254.169.254/latest/meta-data/", ...)` raises `ValueError` without attempting a connection; `build_raw_request` against `http://127.0.0.1:8080/...` and `http://10.0.0.5/...` (legitimate internal targets) is unaffected.

**Test plan:** new `tests/test_ssrf_guard.py` — parametrized over the blocked hosts above (must raise) and a set of legitimate hosts: `127.0.0.1`, `10.0.0.5`, `192.168.1.1`, `example.com`, `host.docker.internal` (must not raise).

---

### SOC-008-E — SARIF 2.1.0 export

**Problem:** `strix/report/writer.py` (full file) writes `.md`/`.csv`/`.json` only. GitHub Code Scanning and most CI security dashboards consume SARIF; today a user has to hand-roll a converter from `vulnerabilities.json` to get findings into those surfaces. Verified live (GitHub Docs, OASIS SARIF 2.1.0 spec, 2026-07-18) that the minimum valid shape GitHub's code-scanning ingestion requires is `$schema` + `version: "2.1.0"` + `runs[].tool.driver.{name,rules[]}` + `runs[].results[].{ruleId,message.text,locations[].physicalLocation.{artifactLocation.uri,region.startLine}}`.

**Design:**
- New `write_sarif(run_dir: Path, vulnerability_reports: list[dict[str, Any]]) -> None` in `strix/report/writer.py`:
  - One `rule` per distinct `(cwe or title)` seen across reports, `id` = CWE if present else a slugified title, `shortDescription.text` = title.
  - One `result` per report: `ruleId` as above, `level` mapped from severity (`critical`/`high` → `error`, `medium` → `warning`, `low`/`info` → `note`), `message.text` = `description`, and a `physicalLocation` per `code_locations[]` entry (falls back to a single location with `artifactLocation.uri` = `target` and no `region` when `code_locations` is empty, e.g. black-box web findings with no source line).
  - `properties.security-severity` set from the existing `cvss` field (already computed at `reporting/tool.py:213`) so GitHub's severity bucketing lines up with the CVSS score already in the JSON report — no new scoring logic, just re-exposing what's already computed.
  - Written via the existing `_atomic_write_text` helper (`writer.py:102-114`) to `run_dir / "vulnerabilities.sarif"`, mirroring how `vulnerabilities.json` is written (`writer.py:87-90`).
- Wired into `strix/report/state.py:336` alongside the existing `write_vulnerabilities(...)` call — same call site, same inputs, no new data plumbing needed.

**Acceptance criteria:** valid JSON; `$schema`/`version` present; one `results[]` entry per input vulnerability report; a report with `code_locations` produces a `region.startLine`; a report without produces a location with just `artifactLocation.uri`. No dependency added (hand-built dict → `json.dumps`, same pattern already used for the other writers).

**Test plan:** new `tests/test_sarif_writer.py` — build 2-3 fixture vulnerability dicts (one with `code_locations`, one without, varying severities), call `write_sarif`, load the JSON back, assert schema/version fields, per-result `ruleId`/`level`/`message`, and location shape.

---

### SOC-008-F — `--fail-on` severity threshold

**Problem:** `strix/interface/main.py:854-858` — any filed vulnerability, any severity, causes `sys.exit(2)` in non-interactive mode. No way to say "only fail my CI build on high/critical."

**Design:**
- New `--fail-on` choice argument (`critical|high|medium|low|any|none`, default `any` — **preserves current behavior exactly** when the flag is omitted) added in `parse_arguments()`.
- At the exit-check site (`main.py:854-858`), replace the "any vulnerability" check with: compute the highest severity present in `report_state.vulnerability_reports` (reuse `_SEVERITY_ORDER` from `strix/report/writer.py:19` for consistent severity ranking), compare against the `--fail-on` threshold, exit 2 only if the highest severity present is at or above the threshold (or `none` disables exit-2 entirely, still exit 0 on completion).

**Acceptance criteria:** default behavior (`--fail-on` omitted) is byte-for-byte identical to today (any finding → exit 2); `--fail-on critical` with only `high`/`medium` findings exits 0; `--fail-on none` always exits 0 on a completed scan regardless of findings.

**Test plan:** extend the CLI argument tests (new cases, e.g. alongside `test_local_sources.py`'s style or a new `tests/test_fail_on_threshold.py`) — pure function extracted for the comparison logic so it's testable without spinning up a full scan (e.g. `should_fail(severities: list[str], threshold: str) -> bool`).

---

## 4. Deferred items — need your explicit go-ahead (protected files)

Per `.cursorrules` §Protected Files, I must **stop and ask** before touching `.github/workflows/*`, `Makefile`, `pyproject.toml`, `Containers/Dockerfile`, or `.pre-commit-config.yaml` — even to add a new file inside `.github/workflows/`. I'm flagging these rather than silently working around them or skipping them:

- **SOC-008-G — CI quality gate** (`ci.yml` running `uv sync --frozen`, `uv run pytest tests/ -q`, `uv run ruff check .`, `uv run mypy strix/`, `uv run bandit -r strix/ -c pyproject.toml` on every PR). This is the single highest-leverage reliability improvement available — `make check-all` already defines the exact command sequence, it just isn't run anywhere automatically. **Why needed:** without it, SOC-008-A through F (or any future change) can regress silently; nothing currently blocks a broken PR from merging. **Ask:** may I add a new `.github/workflows/ci.yml`?
- **SOC-008-H — `make test` target.** Cosmetic/convenience only (`uv run pytest tests/ -q` already works without it); would also fold into `check-all`. **Ask:** may I add a `test:` target to `Makefile` and add it to `check-all`?

If you approve either, they're small enough to fold into this same session's execution; I've kept them out of the "committed" count in §2 only because of the protected-file rule, not because of size or risk.

## 5. Explicitly out of scope this session

- **SOC-008-I (sandbox hardening):** `containers/Dockerfile` is protected, and validating any capability/sudo change properly requires a full image rebuild (Kali-rolling base + ~20 tool installs) plus a live smoke-test scan — that's a dedicated session with Docker build time budgeted in, not a same-session addition alongside A–F. I'm naming the specific gaps (`Dockerfile:10-12` blanket `NOPASSWD:ALL`; `docker_client.py:107-114` always-on `NET_ADMIN`/`NET_RAW`; no resource limits set in this repo's code) so they're tracked, not lost.
- **SOC-008-J (encrypted secret storage):** replacing `strix/config/loader.py:56-75`'s plaintext-JSON persistence with OS-keyring-backed storage is a real improvement but requires picking a keyring dependency (`keyring`, `keyrings.cryptfile`, platform-specific) — a dependency decision I won't make unilaterally per "Do not add dependencies without asking," and it changes `pyproject.toml` (protected). Flagged for a future session with your input on which keyring library.

## 6. Execution order (for when you say go)

1. **A** (gate) → 2. **B** (honest labels, depends on A's attestation shape) → 3. **C** (log scrubbing, independent) → 4. **D** (SSRF guard, independent) → 5. **E** (SARIF, independent) → 6. **F** (fail-on, independent, touches the same exit-code block E's call site neighbors but not the same lines).

A→B is a hard dependency (B's new field values are meaningless without A existing). C, D, E, F have no dependencies on each other or on A/B and can be done in any order — listed roughly by safety-value first, ending with the two smaller CI-ergonomics items.

## 7. Completion gate (per item, before it's marked done)

For each of A–F: code change applied → new/updated unit tests pass (`uv run pytest tests/ -q`) → `uv run ruff check .` clean → `uv run mypy strix/` clean on touched files → `uv run bandit -r strix/ -c pyproject.toml` clean → this plan file's row updated with a ✅ and the commit SHA. No item is marked done on a failing check; failures are reported with the exact output, root-caused, and fixed before re-claiming completion (per house rules — no exceptions).

## 8. Residual risk after A–F ship (stated plainly)

- The confirmation gate (A) is an honesty/friction control, not a cryptographic one — it stops accidental/careless misuse, not a determined bad actor who simply types "yes." That's the correct scope for a local CLI tool; anything stronger (e.g. domain-ownership DNS-TXT verification) would be its own, larger feature and isn't proposed here because it isn't evidenced as needed for this tool's actual usage pattern (operator-run CLI, not a shared multi-tenant service).
- D closes a narrow, high-confidence blocklist — it is not a general SSRF filter and does not attempt DNS-rebinding protection. That's an explicit trade-off to keep the change small, testable, and non-disruptive to legitimate internal-network testing.
- I, J, and the sandbox network-egress question in general remain open after this session — tracked in §5, not silently dropped.
- SARIF (E) maps every finding's `severity` to a SARIF `level` and puts `cvss` (when present) into `properties.security-severity`, but does not attempt to assign real CWE-taxonomy `security-severity` scores beyond what the reporting tool already computed — it is a faithful re-serialization of existing findings, not a new scoring engine.

## 9. Session results — what actually shipped (evidence, not assumption)

**All 7 committed items (A, B, C, D, E, F, H) shipped this session.** G remains explicitly declined by the operator; I and J remain out of scope (§5), unchanged from the original plan.

**New files added:** `strix/telemetry/secrets.py`, `tests/test_authorization_gate.py`, `tests/test_logging_scrub.py`, `tests/test_ssrf_guard.py`, `tests/test_sarif_export.py`, `tests/test_fail_on_threshold.py`, `.work.soc/touch-scope`.

**Files modified:** `strix/interface/main.py`, `strix/interface/utils.py`, `strix/core/inputs.py`, `strix/agents/prompts/system_prompt.jinja`, `strix/telemetry/logging.py`, `strix/tools/proxy/caido_api.py`, `strix/report/writer.py`, `strix/report/state.py`, `strix/interface/cli.py`, `strix/interface/tui/app.py` (`scan_config` dict only — carries A/B's new attestation flags through to the TUI path), `tests/test_inputs.py`, `Makefile`.

**Unplanned but necessary fix — broken `uv run` toolchain (discovered, not caused, by this session):**
`.venv/bin/{pytest,mypy,bandit}` had shebangs hardcoded to `/mnt/work/External/.ai.soc/.venv/bin/python3` — a path that does not exist on this machine (`ls`: "No such file or directory"). Root cause: the venv was built while this repo lived at a different absolute path and was never regenerated after the move. Effect, confirmed by direct reproduction before any fix: `uv run mypy`/`uv run bandit` failed outright ("Failed to spawn... No such file or directory"), and `uv run pytest` silently ran an unrelated system-wide `pytest` under Python 3.10 (missing this project's dependencies, and even attempting to collect tests from outside the repo). This would have made SOC-008-H's new `make test` target (and every existing `make type-check`/`make security` target) unreliable or outright broken for any operator hitting the same drift. Fixed with `uv sync --reinstall` — an already-approved host command (`.cursorrules` "Docker / Dev Environment" table: `uv sync`), not a protected-file edit. Verified fixed: `uv run pytest`/`uv run mypy`/`uv run bandit`/`uv run ruff` all now correctly target `.venv/bin/python3` (3.12.13) and produce results matching direct `.venv/bin/python -m <tool>` invocations.

**Final verification (run after every item, and once more at the end against the full changeset):**

| Check | Command | Result |
|---|---|---|
| Tests | `uv run pytest tests/ -q` | **142 passed**, 0 failed |
| Lint | `uv run ruff check .` | All checks passed |
| Type check (mypy) | `uv run mypy strix/` | **70 errors, 6 files** — identical to the pre-session baseline (verified via `git stash` diff, byte-for-byte same error set); **zero new errors** from this session's changes |
| Type check (pyright) | `uv run pyright strix/` | **832 errors** — identical to the pre-session baseline (verified via `git stash` diff); an initial post-change run found +11 new errors in `strix/interface/utils.py` and `strix/report/writer.py` (unannotated `dict.get(...) or {}` fallbacks pyright couldn't narrow) — fixed with explicit type annotations, re-verified back to the 832 baseline |
| Security scan | `uv run bandit -r strix/ -c pyproject.toml` | No issues identified (13,569 lines scanned) |
| `make test` (new) | `make test` | Passes — 142 tests |
| `make check-all` | `make check-all` | Runs `format`→`lint`→`type-check`→`test`→`security`; stops at `type-check` on the **pre-existing** 70-error baseline (same failure that existed before this session — not a regression, and out of scope to fix per "Scope Discipline: do not refactor unrelated code"); `format`, `lint`, `test`, `security` all individually pass |
| `bash scripts/touch-scope-verify.sh` | — | **PASS** (12 files, all within declared `.work.soc/touch-scope`) |
| `bash scripts/gate-verify.sh` | — | **PASS** |
| `bash scripts/framework-verify.sh` | — | **PASS** (all framework self-tests, unrelated to this diff, unaffected) |
| `bash scripts/blast-radius-check.sh` | — | **FAIL** — flags "4 areas touched" (`strix/`, `tests/`, `Makefile`, `.work.soc/` — a naive top-level-path-segment count on tracked-modified files only; it doesn't see untracked new files at all, e.g. the new test files or `strix/telemetry/secrets.py`). This is an expected, disclosed outcome: the touch-scope file declared exactly these areas *before* any code was written (extended once more to add `.work.soc/context/` when the session handoff was updated), and all of this is one coherent, itemized initiative — not undisclosed scope creep. Not silently worked around; stated here for the record. |

**Residual, explicitly unverified items:**
- No live end-to-end scan (against a real repo or URL target) was run in this session to observe SOC-008-A's interactive/non-interactive authorization prompts, D's guard, or E's SARIF file actually firing during a full agent run — verification here is unit-test-level (mocked/direct function calls) and static analysis, not an integration smoke test. Flagged as **Unverified** rather than claimed.
- The pygments/`reportUnknownMemberType`-style baseline errors in `mypy`/`pyright` (unrelated TUI/renderer files) were confirmed pre-existing via `git stash` diff but were not investigated or fixed — out of scope for this session.
