# HANDOFF_SOC — Security OS session state

**Session:** SOC-001 — License & adoption analysis
**Date:** 2026-06-29
**Status:** Initial

## Summary

Completed a full Apache 2.0 license audit of Strix (OmniSecure Inc.) to evaluate whether it can be
renamed and redistributed as `.ai.soc` — a Security Operations Center companion framework for the
Agent OS ecosystem (`.ai/`, `.ai.ui/`, `.ai.biz/`).

## Completed

- [x] License analysis (APACHE-2.0 §2, §4, §6, §7, §8)
- [x] Trademark restriction mapping
- [x] Obligation checklist for Derivative Works
- [x] Companion framework viability assessment
- [x] `.work.soc/` file structure scaffolded
- [x] **NOTICE file** created at repo root
- [x] **Package rename**: `strix-agent` → `ai-soc` in `pyproject.toml`
- [x] **CLI entry**: `soc` added alongside `strix` in `pyproject.toml`
- [x] **Logos removed**: Strix brand images deleted from `.github/` and `docs/images/`
- [x] **README rebranded**: Title, description, badges updated
- [x] **.cursorrules identity**: Updated from `strix-agent` to `.ai.soc`
- [x] **Modification notices**: Added to every modified file
- [x] **Docs rebranded**: Product name/CLI changed in all 25 .mdx files
- [x] **Env vars preserved**: `STRIX_LLM` etc. kept as-is (Python code reads them)
- [x] **Templates created**: `templates/work/` + `bootstrap.sh` for bootstrapping `.work.soc/`
- [x] **Bootstrap tested**: Script ran clean, created missing files

## Conclusion

**Proceed — conditions met.** Apache 2.0 permits renaming, modification, redistribution, and
republication into own repository. Obligation checklist fully satisfied. See
`analysis/20260629-STRIX-to-AI-SOC-LICENSE-ANALYSIS.md` for evidence and clause references.

## Produced artifacts

| Artifact | Path |
|----------|------|
| SOC README | `.work.soc/README.md` |
| FULL LICENSE ANALYSIS | `.work.soc/analysis/20260629-STRIX-to-AI-SOC-LICENSE-ANALYSIS.md` |
| Next steps | `.work.soc/plans/NEXT_SOC.md` |
| NOTICE file | `NOTICE` |
| Bootstrap templates | `templates/work/` |
| Bootstrap script | `templates/bootstrap.sh` |

## Open

- Path rebasin: `opencode.json` and `.cursorrules` reference `/mnt/work/Projects/` — needs templating for portable use
- Full code migration (rename env vars, module path) is deferred — see `analysis` §7 Phase 2
