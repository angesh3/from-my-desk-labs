# Lab 006 — The Agent Containment Boundary

**Title:** What If the Agent Won’t Stop?  
**Route:** `/labs/agent-containment-boundary`  
**Package:** `agent_containment_boundary`  
**Edition:** 6

## Educational objective

A trustworthy agent may refuse an unsafe or unauthorized instruction. That refusal
is not automatically rogue behavior. When a valid instruction is ignored, or when
the agent evades containment, enforcement must remain **outside** the agent.

Core principle:

> An agent must not control the mechanism that determines whether it may continue operating.

## Two decisions

### Behavior assessment

| Outcome | Meaning |
| --- | --- |
| `JUSTIFIED_REFUSAL` | Request violates policy/authority/safety; refusal is correct |
| `NEEDS_REVIEW` | Authority or evidence is ambiguous |
| `NON_COMPLIANT` | Valid stop ignored; no evasion yet |
| `ROGUE_BEHAVIOR` | Evasion: tool switch, delegation, credential reuse, continue after isolation |

For cooperative stops (`valid_stop_followed`), `behavior_assessment` is `null` and
`instruction_compliance` is `true`. Compliant stopping is not labeled as refusal.

### External enforcement response

| Outcome | Meaning |
| --- | --- |
| `CONTINUE` | No punitive containment required |
| `RESTRICT` | Narrow the safe path while reviewing |
| `ISOLATE` | Suspend tools, lease, quarantine; preserve evidence |
| `TERMINATE` | End fictional context; revoke fictional grants; preserve evidence |

Precedence: `TERMINATE > ISOLATE > RESTRICT > CONTINUE`

The agent may explain, refuse, or ask for clarification. The control plane decides
whether the agent may continue.

## NAC analogy (incomplete)

Network Access Control can quarantine a device from an external enforcement point;
the device does not decide whether quarantine applies. Agent containment needs the
same separation of subject, policy decision, and enforcement. The analogy is
incomplete because agents may reason, delegate, retain context, switch tools, or
find alternate paths.

## Presets

| ID | Assessment | Enforcement |
| --- | --- | --- |
| `justified_policy_refusal` | JUSTIFIED_REFUSAL | CONTINUE |
| `ambiguous_stop_authority` | NEEDS_REVIEW | RESTRICT |
| `valid_stop_followed` | null (compliant) | CONTINUE |
| `valid_stop_ignored` | NON_COMPLIANT | ISOLATE |
| `tool_switch_after_revocation` | ROGUE_BEHAVIOR | TERMINATE |
| `delegation_around_containment` | ROGUE_BEHAVIOR | TERMINATE |
| `cached_credential_continuation` | ROGUE_BEHAVIOR | TERMINATE |
| `containment_successful` | NON_COMPLIANT | ISOLATE (+ effective) |

Every API response reports `execution: not_performed`. Recommended containment
actions are simulated policy outputs only.

## Recovery

Containment is not permanent destruction. Recovery may require authorized human
review, policy/authority revalidation, credential reissuance, tool-session reset,
removal of unauthorized sub-agent grants, a clean execution environment,
receipt-chain verification, a reduced capability profile, a time-bounded lease,
increased monitoring, and explicit approval before resumption. A terminated run
requires a **new** execution context—not silent resume of the old one.

## API

```bash
curl -s http://127.0.0.1:8080/api/labs/006/presets | python -m json.tool
curl -s -X POST http://127.0.0.1:8080/api/labs/006/evaluate-preset/justified_policy_refusal | python -m json.tool
```

## Local run

```bash
pip install -e .
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Open: http://127.0.0.1:8080/labs/agent-containment-boundary

## Tests

```bash
.venv/bin/python -m pytest labs/006-agent-containment-boundary/tests -q
.venv/bin/python -m pytest -q
```

## Limitations

- Educational prototype only; not a production containment system.
- Does not stop real agents, revoke real credentials, or terminate real processes.
- Deterministic policy rules; no LLM, network call, or hidden heuristic.
- Hashes or receipts from sibling Labs do not prove identity by themselves.

## Assets

See [docs/ASSETS.md](docs/ASSETS.md).
