# SOC skills (`.ai.soc/skills/`)

Portable, tool-agnostic workflows for security operations. Each skill is a folder with `skill.md`.

**Identifiers:** Folder name = stable skill id (YAML `name:` in `skill.md` must match). `@` mentions use that id.

**Invocation punctuation:** Use ASCII hyphen `-` between verb and argument (`@soc-deploy-basic - source /path`).

---

## Naming protocol

| Rule | Requirement |
|------|-------------|
| **Shape** | `{domain}-{role}` in **kebab-case** (lowercase ASCII, hyphens) |
| **Stable id** | Folder name = `name:` in frontmatter = `@` handle |
| **Avoid** | File extensions, vague names, vendor prefixes |

---

## Registered skills

| Skill id | Folder | Role |
|----------|--------|------|
| soc-deploy-basic | `soc-deploy-basic/` | **Thin-client deploy:** copies only `.cursorrules` SOC block + `.work.soc/` skeleton; skills/scripts stay in source, loaded at runtime via `SOC_SOURCE` pointer; `update` re-syncs pointer + merges local surface; `verify` audits the target `.cursorrules` (all deploys auto-verify). Args normalized: verb ±`--`, path any position |
| soc-deploy-files | `soc-deploy-files/` | **Files-only deploy (fat-client):** copies `.ai.soc/` files into target from git-tracked set (deploy scripts included so the target self-verifies); no-overwrite default; `update` performs rules-aware merge; scaffold points `SOC_SOURCE` at the local copy |
| soc-deploy-repo | `soc-deploy-repo/` | **Full repo deploy:** git clone (mirror) or archive (snapshot with `.github`); archive auto-verifies the deployed tree |
| soc-session | `soc-session/` | SOC session bookend (mirrors `.ai` session-control); start/close/status/context plus standalone `commit`/`commit push` checkpoints and `close commit [scoped] [push]`; commit scope: full repo in the framework source repo, `.work.soc/` only in deployed targets; updates HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC |
| soc-director | `soc-director/` | Run penetration tests against targets (local code, URLs, domains); deep/standard/quick scan modes |
| soc-gateway | `soc-gateway/` | Run .ai.soc from source without system install |


**Orientation:** `@soc-session context` or read `.work.soc/context/HANDOFF_SOC.md`.

**Skill dependencies and vocabulary:** see [`SKILL_DEPENDENCIES.md`](SKILL_DEPENDENCIES.md) for prerequisites, blocked-report shape, and canonical verbs.

---

## Work tree paths

`{WORK_SOC_ROOT}` = `.work.soc/` at repo root. All SOC session/planning files live under this tree.

| Artifact | Path |
|----------|------|
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |
| `{NEXT_SOC}` | `.work.soc/plans/NEXT_SOC.md` |
| `{UNKNOWNS_SOC}` | `.work.soc/plans/UNKNOWNS_SOC.md` |
