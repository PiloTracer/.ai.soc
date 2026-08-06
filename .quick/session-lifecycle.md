# Session lifecycle (.ai.soc)

```text
@soc-session start              ← load HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC
@soc-session context            ← read-only full context (no HANDOFF write)
@soc-session status             ← compact snapshot
@soc-session close              ← refresh HANDOFF_SOC + NEXT_SOC
@soc-session close commit       ← add + commit
@soc-session close commit push  ← add + commit + push
```
