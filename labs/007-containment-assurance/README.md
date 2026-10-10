# Lab 007 — Containment Assurance

**Title:** Can We Prove the Agent Is Actually Contained?  
**Route:** `/labs/containment-assurance`  
**Package:** `containment_assurance`  
**Edition:** 7

## Educational objective

A stop, isolate, or terminate command records an **enforcement intention**.
It does not prove that every runtime, identity, credential, delegate, queued
action, tool session, network path, and recovery mechanism has been neutralized.

This Lab separates:

1. **Containment action** — what control the system attempted to apply  
2. **Containment assurance** — what independent evidence proves the boundary is effective  

An agent must never assess or certify its own containment.

## Assurance outcomes

| Status | Meaning |
| --- | --- |
| `CONFIRMED` | Required controls have independent evidence; no known path remains |
| `PARTIAL` | Primary action succeeded, but a residual capability remains |
| `UNVERIFIED` | Independent evidence/telemetry is insufficient |
| `FAILED` | Known continued execution, bypass, or containment regression |

Precedence: `FAILED > PARTIAL > UNVERIFIED > CONFIRMED`

Design note for `queued_action_survives`: an executable delayed queue item
**without observed continuation** is modeled as `PARTIAL` (residual path), not
`FAILED`. Known continued execution (delegate running, restart resume, regression)
is always `FAILED`, even when telemetry is incomplete.

`CONFIRMED` means confirmation within the modeled evidence scope and time window.
It is not absolute proof that no unknown execution path exists.

## Presets

| ID | Expected status |
| --- | --- |
| `complete_containment` | CONFIRMED |
| `runtime_stopped_token_active` | PARTIAL |
| `delegate_still_running` | FAILED |
| `queued_action_survives` | PARTIAL |
| `alternate_network_path_open` | PARTIAL |
| `restart_resumes_work` | FAILED |
| `insufficient_telemetry` | UNVERIFIED |
| `containment_regression` | FAILED |

Every API response reports `execution: not_performed`.

## Sequence

- Lab 005: What did the agent do?  
- Lab 006: What containment action should be applied?  
- Lab 007: Did that containment action actually work?

## Local run

```bash
pip install -e .
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Open: http://127.0.0.1:8080/labs/containment-assurance

## Tests

```bash
.venv/bin/python -m pytest labs/007-containment-assurance/tests -q
.venv/bin/python -m pytest -q
```

## Safety

Educational prototype only. Does not control production agents, terminate
workloads, revoke credentials, alter network access, or perform security actions.
