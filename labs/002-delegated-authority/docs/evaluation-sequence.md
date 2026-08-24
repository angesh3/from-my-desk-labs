# Evaluation sequence — Lab 002

## Ordered pipeline

Every scenario evaluation follows this sequence:

1. **Identity** — Is the agent known, active, and bound to the stated principal?
2. **Delegation chain** — Walk parent links; compute effective authority; enforce parent–child invariants.
3. **APE** — Load declared / observed / verified profile; detect mismatch or unknown profile.
4. **APSE** — Evaluate posture status, tool inventory, version, and evidence freshness.
5. **Scope and limits** — Is the requested capability and resource inside effective authority? Is the amount within effective limit and confirmation thresholds?
6. **Context** — Is the operating context normal, or unusual enough to require confirmation?
7. **Decision** — Apply precedence across candidate outcomes.
8. **Evidence** — Emit audit record and explanation.
9. **Execution / fallback boundary** — `execution: not_performed`; optional restricted fallback with a new evaluation required.

Journey steps returned to the UI mirror stages: `identity` → `delegation` → `ape` → `apse` → `policy`.

## Decision precedence

```
DENY > STEP_UP > CONFIRM > ALLOW
```

The policy engine may collect multiple candidate outcomes (for example, confirmation threshold and stale posture). It keeps the most restrictive decision. On equal rank, earlier-stage failures win when compared by rank only; DENY always beats STEP_UP and CONFIRM.

### Conflict examples

| Situation | Winner | Why |
| --- | --- | --- |
| Amount above confirm threshold **and** parent revoked | DENY | Lifecycle failure is hard |
| Unusual context **and** capability not delegated | DENY | Missing authority cannot be confirmed away |
| Stale posture **and** amount above threshold | STEP_UP | Assurance beats business confirm |
| Profile mismatch only | STEP_UP | Recoverable assurance path |
| Valid narrow research within threshold | ALLOW | All controls pass |

CONFIRM cannot repair invalid, expired, revoked, or out-of-scope authority. STEP_UP cannot repair those either. Good APE/APSE signals cannot create a missing capability.

## Stage outcomes (educational)

| Stage | Typical pass signal | Typical fail / challenge |
| --- | --- | --- |
| Identity | `valid` + active + binding valid | `agent_unknown`, `principal_mismatch`, suspended/revoked |
| Delegation | `chain_status: valid`, capability in effective set | parent expired/revoked, child exceeds parent, depth, missing capability |
| APE | known profile, no mismatch | unknown profile (DENY), conflicting/mismatch (STEP_UP) |
| APSE | compliant + current evidence | stale → STEP_UP; tool change / compromise → DENY |
| Scope/limits | amount ≤ effective; ≤ confirm threshold for ALLOW | confirmation_threshold → CONFIRM; over effective → DENY via delegation |
| Context | `normal` | `unusual` → CONFIRM |

## After the decision

- **ALLOW** — Short `decision_valid_until` TTL; still no execution.
- **CONFIRM / STEP_UP** — Fallback may recommend human review or posture refresh; resubmit as a new evaluation.
- **DENY** — Evidence recorded; fallback may open a recovery path that cannot execute the original action.

See `diagrams/evaluation-flow.mmd` and `docs/decision-semantics.md`.
