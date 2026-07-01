# START HERE — Security OS operator decision tree

**Purpose:** Answer fast: *"What do I do right now for security work?"*

---

## 0. Two things to know

1. **Skills orchestrate the work.** Standards bind the assessments. Scripts run the tools.
2. **Truth lives in `.work.soc/`** — `HANDOFF_SOC.md`, `NEXT_SOC.md`, `UNKNOWNS_SOC.md`.

---

## 1. Decision tree

```text
┌──────────────────────────────────────────┐
│  Where am I right now?                    │
└──────────────────────────────────────────┘
       │
       ├── "Bootstrap / empty .work.soc"    ──► @deploy-basic update
       │
       ├── "I just opened the project / lost"   ──► @session-soc context
       │
       ├── "Where am I / what's next?"         ──► @session-soc status
       │
       ├── "Start a SOC session"               ──► @session-soc start
       │
       ├── "Close SOC session"                 ──► @session-soc close [commit] [push]
       │
       ├── "Run a security assessment"         ──► @soc-director - <target>
       │
       ├── "Deploy .ai.soc to a target project"  ──► §2
       │
       └── "I don't know which skill to use"   ──► @soc-director - <describe what you want>
```

---

## 2. Deploy .ai.soc to a target project

| You need… | From target project | From .ai.soc directory |
|-----------|-------------------|----------------------|
| Thin-client (scaffold only) | `@deploy-basic - source /path/to/.ai.soc` | `@deploy-basic - target /path/to/project` |
| Fat-client (full files) | `@deploy-files - source /path/to/.ai.soc` | `@deploy-files copy - /path/to/project` |
| Full repo (git/archive) | — | `@deploy-repo clone - /path/to/project` |
| Update existing | `@deploy-basic update` or `@deploy-files update` | — |
| Check deploy status | `@deploy-basic status` | `@deploy-files status` |

Source `.ai.soc` is never modified. Only the target receives changes.

---

## 3. Quick reference

| Action | Command |
|--------|---------|
| Load context (read-only) | `@session-soc context` |
| Open session | `@session-soc start` |
| Close session | `@session-soc close` |
| Close + commit | `@session-soc close commit` |
| Close + commit + push | `@session-soc close commit push` |
| Status snapshot | `@session-soc status` |
| Run SOC tool | `./gateway.sh -t <target>` |
| Full assessment | `@soc-director - scan <target> [quick\|standard\|deep]` |

---

## 4. Reading order

| Step | File |
|------|------|
| 1 | `.cursorrules` (SOC section) |
| 2 | `.work.soc/context/HANDOFF_SOC.md` |
| 3 | `.work.soc/plans/NEXT_SOC.md` |
| 4 | `.work.soc/plans/UNKNOWNS_SOC.md` |
| 5 | `skills/README.md` |