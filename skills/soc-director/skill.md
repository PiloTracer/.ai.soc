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
2. Runs `./gateway.sh -t <target> -n` — gateway auto-loads `.env`, ensures Python/uv/Docker, and runs from source
3. Reports the run name and output directory when complete
4. Summarizes findings from the run directory

## Target parsing

| Instruction pattern | Resolves to |
|---------------------|-------------|
| `test http://localhost:38383` | `./gateway.sh -t http://localhost:38383 -n` |
| `perform penetration testing on project at /mnt/work/some-project` | `./gateway.sh -t /mnt/work/some-project -n` |
| `scan example.com for XSS` | `./gateway.sh -t example.com -n --instruction "Focus on XSS"` |
| `audit repo /path/to/repo with deep scan` | `./gateway.sh -t /path/to/repo -n -m deep` |
| `quick CI check on /path/to/repo` | `./gateway.sh -t /path/to/repo -n -m quick` |

## Scan modes

| Mode | Flag | Use case |
|------|------|----------|
| `quick` | `-m quick` | CI/CD fast checks |
| `standard` | `-m standard` | Routine testing |
| `deep` | `-m deep` | Thorough review (default unless user says otherwise) |

## Execution

The agent runs via gateway.sh (no install needed, auto-loads `.env`):

```bash
./gateway.sh -t <target> -n [-m <mode>] [--instruction "..."] [--mount <path>]
```

If `soc` CLI is explicitly installed on `$PATH`, the agent may also use it directly, but gateway.sh is the default and recommended path.

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

| Requirement | Check | Notes |
|-------------|-------|-------|
| `.env` file | Present at repo root | Must set `STRIX_LLM` and `LLM_API_KEY` (see `.env.example`) |
| Docker | `docker info` | Required for sandbox containers |

All other prerequisites (Python 3.12+, `uv`, dependencies) are auto-resolved by `gateway.sh`.

## Constraints

- The agent MUST NOT run `soc` interactively — always pass `-n`/`--non-interactive`.
- If `gateway.sh` fails (env, Docker, deps), report its error output to the user — do not silently fall back.
- The agent reports the run directory path so the user knows where to find results.
