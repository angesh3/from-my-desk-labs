# Lab 002 demo guide

Educational demo only. Fictional data. Every evaluation reports `execution: not_performed`.

## One-minute quick demo

1. Open `/labs/delegated-authority`.
2. Select **Valid narrow delegation** → Evaluate → point to **ALLOW** and “execution remains separate.”
3. Select **Execution not delegated** → Evaluate → point to **DENY**, journey failure on Delegation, and Preview safe fallback.
4. Say: “Good identity and posture cannot create missing authority.”

## Three-to-five-minute complete demo

Suggested preset order:

| Order | Preset | Expected | What to say |
| --- | --- | --- | --- |
| 1 | Valid narrow delegation | ALLOW | Authority narrowed correctly; policy approved; nothing executed. |
| 2 | Human confirmation required | CONFIRM | Authority is valid; business confirmation is still required. |
| 3 | Stale posture evidence | STEP_UP | APSE can challenge without expanding authority. |
| 4 | Execution not delegated | DENY + fallback | Research-only envelope cannot execute. Preview the recovery path. |
| 5 | Parent revoked | DENY | Revocation propagates; confirmation cannot repair it. |

### What to point out in the UI

1. End-to-end workflow poster / GIF: Human → agents → tool → Trust Gateway → decision.
2. Evaluation-flow diagram: ordered checks and DENY precedence.
3. Fallback-flow and revocation-flow: recovery vs lifecycle collapse.
4. System-architecture diagram: Trust Gateway internals (APE informs, APSE restricts).
2. Visual delegation chain: selected node highlights the affected handoff.
3. Evaluation journey stepper: human-readable pass / challenge / fail states.
4. Decision result: large label, takeaway, technical details collapsed.
5. Safe fallback flow: original decision unchanged; new evaluation required.
6. System architecture: APE does not grant; APSE does not expand; executor is separate.

## Exact API confirmation

```bash
curl -s -X POST http://127.0.0.1:8080/api/labs/002/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"execution_not_delegated"}'
```

Expect `decision: deny`, `reason_code: capability_not_delegated`, `execution: not_performed`.
