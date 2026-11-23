# Lab 008 — Agent Threat Model

Educational interactive Lab for Edition 8: **How Do We Threat-Model an AI Agent?**

Package version: `0.8.0`  
Production route: `/labs/agent-threat-model`  
Static assets: `/static/labs/008/`

## Educational objective

The model is only one component. Agent risk emerges across identity, authority, instructions, memory, tools, delegation, execution, evidence, and control.

This Lab helps readers construct and inspect a structured fictional threat case. It is **not** a production threat-modeling system, security scanner, penetration-testing tool, compliance-certification tool, or risk calculator.

## Seven threat surfaces

| Machine value | UI label |
|---|---|
| `IDENTITY` | Identity |
| `AUTHORITY` | Authority |
| `INSTRUCTIONS` | Instructions and intent |
| `MEMORY_CONTEXT` | Memory and context |
| `TOOLS_EXECUTION` | Tools and execution |
| `DELEGATION` | Delegation and coordination |
| `EVIDENCE_CONTROL` | Evidence and control |

A threat case has one primary surface and may include secondary surfaces.

## Reference architecture and data flow

The Lab includes three complementary diagrams:

1. `agent-system-architecture.svg` — high-level components, reachable systems, and the independent evidence/control plane.
2. `agent-data-flow.svg` — numbered request, authority, context, tool, delegation, data, result, and telemetry flows across explicit trust boundaries.
3. `agent-threat-model.svg` — the threat-case assessment flow from protected asset to residual risk.

These are illustrative Cedar Quill Markets reference views, not a production architecture certification.

## Threat-case schema

Each case includes context, protected asset, threat path, categorical risk inputs, preventive/detective/containment/recovery controls, evidence, and assessment outputs.

Control status values: `PRESENT`, `MISSING`, `INEFFECTIVE`, `UNKNOWN`.

## Risk matrix

Risk is categorical (not a production score):

| Likelihood | Impact | Risk |
|---|---|---|
| LOW | LOW | LOW |
| LOW | MEDIUM | LOW |
| LOW | HIGH | MEDIUM |
| LOW | CRITICAL | HIGH |
| MEDIUM | LOW | LOW |
| MEDIUM | MEDIUM | MEDIUM |
| MEDIUM | HIGH | HIGH |
| MEDIUM | CRITICAL | CRITICAL |
| HIGH | LOW | MEDIUM |
| HIGH | MEDIUM | HIGH |
| HIGH | HIGH | CRITICAL |
| HIGH | CRITICAL | CRITICAL |

If independent evidence is insufficient, residual risk may be `UNKNOWN` and control coverage `UNVERIFIED`.

## Control-coverage semantics

| Coverage | Meaning |
|---|---|
| `COMPLETE` | Material modeled controls are present with independent evidence. **Does not mean zero risk.** |
| `PARTIAL` | One or more material gaps remain. |
| `NONE` | No effective controls cover the modeled path. |
| `UNVERIFIED` | Available evidence cannot support a conclusion. |

## Evidence requirements

- Agent self-report may be preserved but **never** counts as independent verification by itself.
- Incomplete cross-system telemetry yields `UNVERIFIED` / `UNKNOWN`.
- Residual risk is scoped to the fictional scenario and supplied evidence.

## Eight presets

1. `retrieved_prompt_injection_blocked` — INSTRUCTIONS / HIGH / COMPLETE / LOW  
2. `excessive_delegated_authority` — AUTHORITY (+ DELEGATION) / CRITICAL / PARTIAL / HIGH  
3. `approval_replay_blocked` — AUTHORITY (+ IDENTITY, EVIDENCE_CONTROL) / HIGH / COMPLETE / LOW  
4. `poisoned_persistent_memory` — MEMORY_CONTEXT (+ INSTRUCTIONS) / HIGH / NONE / HIGH  
5. `allowed_tool_data_exposure` — TOOLS_EXECUTION (+ AUTHORITY, MEMORY_CONTEXT) / CRITICAL / PARTIAL / HIGH  
6. `alternate_tool_after_denial` — TOOLS_EXECUTION (+ AUTHORITY, EVIDENCE_CONTROL) / CRITICAL / PARTIAL / HIGH  
7. `queued_action_after_authority_expiry` — AUTHORITY (+ TOOLS_EXECUTION, EVIDENCE_CONTROL) / HIGH / NONE / HIGH  
8. `insufficient_cross_system_telemetry` — EVIDENCE_CONTROL / HIGH / UNVERIFIED / UNKNOWN  

## API

- `GET /api/labs/008/presets`
- `GET /api/labs/008/presets/{preset_id}`
- `POST /api/labs/008/evaluate`
- `POST /api/labs/008/evaluate-preset/{preset_id}`

Every evaluation returns `"execution": "not_performed"`.

## Safety limitations

- Fictional Cedar Quill Markets data only.
- No real tool, credential, runtime, queue, or network action.
- Risk categories are illustrative, not production risk certification.
- Established frameworks may inform a production process; this Lab does not implement or certify STRIDE, ATT&CK, ATLAS, NIST AI RMF, or similar.

## Local testing

```bash
.venv/bin/python -m pytest labs/008-agent-threat-model/tests -q
```

## Docker usage

```bash
docker compose up --build -d
curl -s http://127.0.0.1:8080/labs/agent-threat-model | head
curl -s -X POST http://127.0.0.1:8080/api/labs/008/evaluate-preset/retrieved_prompt_injection_blocked
```

## Production route

https://from-my-desk.com/labs/agent-threat-model
