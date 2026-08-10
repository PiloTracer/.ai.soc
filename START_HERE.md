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
       ├── "Bootstrap / empty .work.soc"    ──► @soc-deploy-basic update
       │
       ├── "I just opened the project / lost"   ──► @soc-session context
       │
       ├── "Where am I / what's next?"         ──► @soc-session status
       │
       ├── "Start a SOC session"               ──► @soc-session start
       │
       ├── "Close SOC session"                 ──► @soc-session close [commit] [push]
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
| Thin-client (scaffold only) | `@soc-deploy-basic - source /path/to/.ai.soc` | `@soc-deploy-basic - target /path/to/project` |
| Fat-client (full files) | `@soc-deploy-files - source /path/to/.ai.soc` | `@soc-deploy-files copy - /path/to/project` |
| Full repo (git/archive) | — | `@soc-deploy-repo clone - /path/to/project` |
| Update existing | `@soc-deploy-basic update` or `@soc-deploy-files update` | — |
| Check deploy status | `@soc-deploy-basic status` | `@soc-deploy-files status` |
| Verify deploy (audit `.cursorrules`) | `@soc-deploy-basic verify` | `@soc-deploy-basic verify /path/to/project` |

Source `.ai.soc` is never modified. Only the target receives changes. Verbs accept an optional `--` prefix and may appear before or after the path (`@soc-deploy-basic /path update` ≡ `@soc-deploy-basic /path --update`). Every deploy/update ends with a `verify` pass.

---

## 3. Quick reference

| Action | Command |
|--------|---------|
| Load context (read-only) | `@soc-session context` |
| Open session | `@soc-session start` |
| Close session | `@soc-session close` |
| Close + commit | `@soc-session close commit` |
| Close + commit + push | `@soc-session close commit push` |
| Status snapshot | `@soc-session status` |
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
| 6 | `skills/SKILL_DEPENDENCIES.md` |

## 5. Quick cheat-sheets

- **Session lifecycle:** `.quick/session-lifecycle.md`
- **Director handles:** `.quick/directors.md`
- **Deploy to a project:** `.quick/deploy-to-project.md`
