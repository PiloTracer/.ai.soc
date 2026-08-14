# Session lifecycle (.ai.soc)

```text
@soc-session start               ← load HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC; mark Open
@soc-session context             ← read-only full context (no HANDOFF write)
@soc-session status              ← compact snapshot
@soc-session commit              ← commit .work.soc/ only; no close, no HANDOFF write
@soc-session commit push         ← commit .work.soc/ + push; no close
@soc-session close               ← refresh HANDOFF_SOC + NEXT_SOC + UNKNOWNS_SOC
@soc-session close commit        ← add + commit (.work.soc/ scope)
@soc-session close commit push   ← add + commit + push
```

Commit scope: in a deployed target project commits cover `.work.soc/` only (incl. new
untracked files there); in the framework source repo itself they cover the full repo —
all modified/added/new files. `commit`/`push` authorize only the invocation that names
them (DLP). Mirrors `.ai/skills/session-control` — same verbs, same modifiers.
