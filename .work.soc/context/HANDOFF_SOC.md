# HANDOFF_SOC — Security OS session state

**Session:** SOC-003 — remove tools-project integration
**Date:** 2026-07-01
**Status:** Closed

## Summary

Removed all tools-project integration from `.ai.soc`. The parent `.ai` project now owns all inter-framework communications with tools-project. Deleted the `soc-project-query-setup` skill, the `project-mcp` MCP server, and their entries in `.cursorrules` and `skills/README.md`.

## Completed

- [x] Deleted `skills/soc-project-query-setup/` (skill.md + reference.md)
- [x] Deleted `.opencode/mcp/project-mcp/mcp_server.py` (MCP bridge)
- [x] Deleted `.opencode/` tree (now empty)
- [x] Removed `soc-project-query-setup` row from `.cursorrules` SOC skills table
- [x] Removed `soc-project-query-setup` row from `skills/README.md` registered skills table
- [x] Verified zero references to `soc-project-query-setup`, `project-mcp`, `tools-project-key`, `TOOLS_PROJECT_API_KEY` across entire codebase
- [x] Committed and pushed

## Produced artifacts

*(none — removal only)*

## Open

- Parent `.ai` project now owns all tools-project integration. No new unknowns.
