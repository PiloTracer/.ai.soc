# SOC skills (`.ai.soc/skills/`)

Portable, tool-agnostic workflows for security operations. Each skill is a folder with `skill.md`.

**Identifiers:** Folder name = stable skill id (YAML `name:` in `skill.md` must match). `@` mentions use that id.

**Invocation punctuation:** Use ASCII hyphen `-` between verb and argument (`@deploy-basic - source /path`).

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
| deploy-basic | `deploy-basic/` | **Thin-client deploy:** copies only `.cursorrules` SOC block + `.work.soc/` skeleton; skills/standards/scripts stay in source, loaded at runtime via `SOC_SOURCE` pointer; `update` re-syncs pointer + merges local surface |
| deploy-files | `deploy-files/` | **Files-only deploy (fat-client):** copies `.ai.soc/` files into target from git-tracked set; no-overwrite default; `update` performs rules-aware merge |
| deploy-repo | `deploy-repo/` | **Full repo deploy:** git clone (mirror) or archive (snapshot with `.github`) |
| session-soc | `session-soc/` | SOC session bookend; start/close/status/context; updates HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC |
| soc-director | `soc-director/` | Run penetration tests against targets (local code, URLs, domains); deep/standard/quick scan modes |
| soc-gateway | `soc-gateway/` | Run .ai.soc from source without system install |
| soc-project-query-setup | `soc-project-query-setup/` | **Optional integration:** guide through tools-project API key, MCP registration, connectivity test. OS-aware (tailors guidance per framework). |

**Orientation:** `@session-soc context` or read `.work.soc/context/HANDOFF_SOC.md`.

---

## Work tree paths

`{WORK_SOC_ROOT}` = `.work.soc/` at repo root. All SOC session/planning files live under this tree.

| Artifact | Path |
|----------|------|
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |
| `{NEXT_SOC}` | `.work.soc/plans/NEXT_SOC.md` |
| `{UNKNOWNS_SOC}` | `.work.soc/plans/UNKNOWNS_SOC.md` |