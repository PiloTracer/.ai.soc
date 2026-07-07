# Session lifecycle (.ai.soc)

```text
@session-soc start              ← load HANDOFF_SOC, NEXT_SOC, UNKNOWNS_SOC
@session-soc context            ← read-only full context (no HANDOFF write)
@session-soc status             ← compact snapshot
@session-soc close              ← refresh HANDOFF_SOC + NEXT_SOC
@session-soc close commit       ← add + commit
@session-soc close commit push  ← add + commit + push
```
