# Modified from Strix original. See NOTICE and LICENSE for details.

# @soc-director — AI Agent Skill

Run `.ai.soc` penetration testing against a target and deliver findings.

## Usage

```
@soc-director - <instruction>
```

The instruction is a natural-language description of what to test. The skill parses it for a target (path, URL, domain, IP) and optional scan constraints.

## What it does

1. Parses the instruction for a **target** (required) and any scan options
2. Runs `soc --target <target> --non-interactive` (or via `./gateway.sh` if `soc` CLI isn't installed)
3. Reports the run name and output directory when complete
4. Summarizes findings from the run directory

## Target parsing

| Instruction pattern | Resolves to |
|---------------------|-------------|
| `test http://localhost:38383` | `soc --target http://localhost:38383 -n` |
| `perform penetration testing on project at /mnt/work/some-project` | `soc --target /mnt/work/some-project -n` |
| `scan example.com for XSS` | `soc --target example.com -n --instruction "Focus on XSS"` |
| `audit repo /path/to/repo with deep scan` | `soc --target /path/to/repo -n -m deep` |
| `quick CI check on /path/to/repo` | `soc --target /path/to/repo -n -m quick` |

## Scan modes

| Mode | Flag | Use case |
|------|------|----------|
| `quick` | `-m quick` | CI/CD fast checks |
| `standard` | `-m standard` | Routine testing |
| `deep` | `-m deep` | Thorough review (default unless user says otherwise) |

## Execution

The agent runs one of:

```bash
# If soc CLI is installed (via uv sync / pip):
soc --target <target> --non-interactive [--scan-mode <mode>] [--instruction "..."]
```

```bash
# Fallback via gateway.sh (no install needed):
./gateway.sh -t <target> -n [-m <mode>] [--instruction "..."]
```

## Output

Reports land at `$PWD/strix_runs/<run-name>/`:

| File | Contents |
|------|----------|
| `penetration_test_report.md` | Executive summary |
| `vulnerabilities/<id>.md` | Per-finding detail |
| `vulnerabilities.json` | Machine-readable index |
| `vulnerabilities.csv` | Spreadsheet |
| `run.json` | Run metadata |

After the scan completes, the agent reads `penetration_test_report.md` and `vulnerabilities.csv` and presents a summary to the user.

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Docker | `docker info` (sandbox) |
| LLM provider | `STRIX_LLM` + `LLM_API_KEY` env vars |
| Dependencies | `uv sync` (or `pip install ai-soc`) |

## Constraints

- The agent MUST NOT run `soc` interactively — always pass `-n`/`--non-interactive`.
- If Docker is not running, report the error and stop — do not attempt to start Docker.
- If `STRIX_LLM` is not set, report the missing env var and stop.
- The agent reports the run directory path so the user knows where to find results.
