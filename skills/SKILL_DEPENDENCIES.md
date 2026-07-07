# SOC OS — Skill dependency graph

**Purpose:** Single source of truth for which skill may run before which.

### Work tree path resolution

| Placeholder | Resolved path |
|-------------|---------------|
| `{WORK_SOC_ROOT}` | `.work.soc/` |
| `{HANDOFF_SOC}` | `.work.soc/context/HANDOFF_SOC.md` |
| `{NEXT_SOC}` | `.work.soc/plans/NEXT_SOC.md` |
| `{UNKNOWNS_SOC}` | `.work.soc/plans/UNKNOWNS_SOC.md` |

### Dependency matrix

| Skill / mode | Depends on | Gate |
|--------------|------------|------|
| **deploy-basic** `bootstrap` / `update` | Source `templates/cursorrules.soc.snippet.template` readable | Required |
| **deploy-basic** `status` | - | Read-only |
| **deploy-files** `copy` | Target parent dir exists | Required |
| **deploy-files** `status` | - | Read-only |
| **deploy-repo** `clone` / `archive` | Target must not exist (clone) or parent exists (archive) | Required |
| **deploy-repo** `status` | - | Read-only |
| **session-soc** `start` | `{HANDOFF_SOC}` | Recommended |
| **session-soc** `close` | Prior `start` or dirty tree | - |
| **session-soc** `context` | - | Read-only |
| **session-soc** `status` | - | Read-only |
| **soc-director** `- <free-text>` | `{HANDOFF_SOC}` readable | Recommended |
| **soc-director** `status` | - | Read-only |
| **soc-gateway** `status` | - | Read-only |

### Blocked report shape

When a gate stops execution:

```markdown
## @<skill> <command> - blocked (prerequisite)

**Required:** <state or upstream step>
**Detected:** <what's actually present>
**Run first:** `<exact command to fix>`
```

### Canonical verb vocabulary

| Canonical verb | Meaning | Skills |
|----------------|---------|--------|
| `status` | Read-only state | session-soc, soc-director, soc-gateway, deploy-basic |
| `start` / `close` / `context` | Session lifecycle | session-soc |
| `bootstrap` / `update` | Deploy lifecycle | deploy-basic |
| `copy` | File deploy | deploy-files |
| `clone` / `archive` | Repo deploy | deploy-repo |
| `- <free-text>` | Free-text routing | soc-director |
