# Technology stack — .ai.soc

**Derived from Strix by OmniSecure Inc. — see NOTICE and LICENSE.**

**Status:** Draft — fill before implementation.

**Updated:** 2026-06-29

---

## 1. Summary

| Layer | Choice | Version (pin) | Notes |
|-------|--------|---------------|-------|
| Language (primary) | Python | 3.12+ | 3.12–3.14 supported |
| Package manager | uv | — | Replace pip/poetry |
| AI agent framework | openai-agents (liteLLM) | 0.14.6 | Multi-provider LLM orchestration |
| Config | pydantic + pydantic-settings | 2.11+ | Type-safe settings |
| CLI framework | textual + rich | — | TUI + rich CLI output |
| Container runtime | Docker SDK | — | Python Docker client (sandbox mgmt) |
| Proxy | Caido SDK | 0.2.0 | HTTP proxy for security testing |
| Vulnerability scoring | CVSS | 3.2 | Standardized severity |
| Build system | hatchling | — | Wheel packaging |
| Linter | ruff | — | Fast Python linter + formatter |
| Type checker | mypy + pyright | — | Strict mode both |
| Security linter | bandit | — | Built-in security scanning |
| Test framework | pytest + pytest-asyncio | 8.3+ | Async test support |
| Pre-commit | pre-commit | 4.2+ | Hook framework |

---

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `strix/` | Application source (internal) |
| `strix/interface/` | CLI and TUI entry points |
| `strix/tools/` | Agent tool implementations |
| `strix/config/` | Configuration models and loading |
| `strix/agents/` | Agent orchestration and prompts |
| `strix/core/` | Core runner and execution |
| `tests/` | Test suite |
| `containers/` | Docker sandbox definition |
| `benchmarks/` | Performance benchmarks |
| `.work/` | Plans, SPECs, ADRs, HANDOFF |

---

## 3. Local development

| Item | Value |
|------|-------|
| Dev setup | `uv sync && uv run pre-commit install` |
| Test command | `uv run pytest tests/ -q` |
| Lint | `uv run ruff check .` |
| Type check | `uv run mypy strix/` and `uv run pyright strix/` (internal module) |
| Format | `uv run ruff format .` |
| Security | `uv run bandit -r strix/ -c pyproject.toml` (internal module) |
| All checks | `make check-all` |

---

## 4. CI/CD

| Item | Status |
|------|--------|
| Platform | GitHub Actions |
| Build | `scripts/build.sh` + `scripts/docker.sh` |
| Release | `.github/workflows/build-release.yml` |

---

## 5. Open decisions (track in `.work/plans/UNKNOWNS.md`)

| ID | Topic | Owner |
|----|-------|-------|
| U1 | Stack pins not finalized | — |
| U2 | CI pipeline full design | eng |

---

## 6. ADR cross-reference

Decisions live in `.work/decisions/`. This file holds **pins** only; rationale belongs in ADRs.
