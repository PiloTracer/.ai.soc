# Modified from Strix original. See NOTICE and LICENSE for details.

# .ai.soc Gateway — AI Agent Skill

Run .ai.soc (AI penetration testing) from source without any system install.

## Quick start

```bash
# 1. Set env (or they go in .env at repo root)
export STRIX_LLM='deepseek/deepseek-v4-flash'
export LLM_API_KEY='your-key'

# 2. Audit a local repo
./gateway.sh -t /path/to/target-repo

# 3. Audit with options
./gateway.sh -t /path/to/repo --mount /path/to/large-repo --scan-mode deep
```

## Entry point

`gateway.sh` at repo root — auto-bootstraps `uv`, Python 3.12+, and locked deps.

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Docker | `docker info` must work (sandbox container) |
| LLM provider | `STRIX_LLM` + `LLM_API_KEY` env vars |
| Internet | First run pulls `uv` + deps + sandbox Docker image |

## Common commands

```bash
# Scan a local repo (small — copies into sandbox)
./gateway.sh -t /path/to/repo

# Bind-mount large repos (>1 GB, skips copy)
./gateway.sh --mount /path/to/large-repo

# Quick CI-style scan (headless, fast)
./gateway.sh -t /path/to/repo --scan-mode quick -n

# Scan a web app
./gateway.sh -t https://example.com

# Resume a prior scan
./gateway.sh --resume <run-name>

# Multi-target
./gateway.sh -t /path/to/repo -t https://staging.example.com
```

## Config

`.env` at repo root is auto-sourced if present:

```bash
STRIX_TELEMETRY=0              # disable analytics
STRIX_LLM=deepseek/deepseek-v4-flash
LLM_API_KEY=sk-...
STRIX_MAX_LOCAL_COPY_MB=2048   # increase copy limit
```

## Key flags

| Flag | Purpose |
|------|---------|
| `-t, --target` | Target path/URL (repeatable) |
| `--mount` | Bind-mount dirs (large repos) |
| `-m, --scan-mode` | `quick` / `standard` / `deep` |
| `-n, --non-interactive` | Headless mode |
| `--instruction` | Custom pentest instructions |
| `--max-budget-usd` | LLM spend cap |
| `--resume` | Continue a prior run |

## Telemetry

Disabled by default via `.env`. Re-enable: `STRIX_TELEMETRY=1`. See `strix/telemetry/README.md`.

## Data sent to LLM

The configured LLM receives the target's full scan context (code, vulns, traffic). Pick a provider you trust. No target data is sent to analytics (PostHog / Scarf).

## Output

Results go to `$PWD/strix_runs/<run-name>/` — reports, agent logs, findings.
