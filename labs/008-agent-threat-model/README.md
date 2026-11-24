# Lab 008 — Agent Threat Model

Educational interactive Lab for Edition 8: **How Do We Threat-Model an AI Agent?**

Package version: `0.8.0`
Production route: `/labs/agent-threat-model`
Static assets: `/static/labs/008/`

## Educational objective

The model is only one component. Agent risk emerges across identity, authority, instructions, memory, tools, delegation, execution, evidence, and control—and across the full agent lifecycle.

Lab 008 completes the From My Desk storyline from Labs 001–007 by connecting earlier control questions into one system-level threat model. It also surfaces cross-cutting risks:

- behavioral and usage drift
- learning and memory drift
- exposure to public models and external AI services
- impact on networks, credentials, queues, compute, and other resources

This Lab is **not** a production threat-modeling system, security scanner, penetration-testing tool, compliance-certification tool, or risk calculator.

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

## Cross-cutting dimensions

These annotate scenarios without replacing primary surfaces:

| Machine value | UI label |
|---|---|
| `BEHAVIOR_USAGE_DRIFT` | Behavior and usage drift |
| `LEARNING_MEMORY_DRIFT` | Learning and memory drift |
| `EXTERNAL_MODEL_EXPOSURE` | External model exposure |
| `NETWORK_RESOURCE_IMPACT` | Network and resource impact |

## Important distinctions

- Behavioral/usage drift is not model-weight drift.
- Memory or context updates are not model retraining.
- Approved external-model use differs from uncontrolled public-model exposure.
- Availability or cost impact is related to, but distinct from, security compromise.
- Attempted control is not independently verified control.

## Risk matrix

Categorical (not a production score). See `policies/threat-model-policy.yaml`.

`COMPLETE` coverage does not mean zero risk. Insufficient independent evidence may yield `UNVERIFIED` / `UNKNOWN`.

## Twelve presets

Original eight plus:

9. `usage_drift_after_approval` — INSTRUCTIONS + BEHAVIOR_USAGE_DRIFT / HIGH / PARTIAL / HIGH
10. `public_model_sensitive_context_exposure` — TOOLS_EXECUTION (+ MEMORY_CONTEXT, EVIDENCE_CONTROL) + EXTERNAL_MODEL_EXPOSURE / CRITICAL / PARTIAL / HIGH
11. `learning_changes_future_behavior` — MEMORY_CONTEXT (+ INSTRUCTIONS) + LEARNING_MEMORY_DRIFT / HIGH / PARTIAL / HIGH
12. `agent_resource_and_network_expansion` — TOOLS_EXECUTION (+ AUTHORITY, DELEGATION, EVIDENCE_CONTROL) + NETWORK_RESOURCE_IMPACT / CRITICAL / PARTIAL / HIGH

## API

- `GET /api/labs/008/presets`
- `GET /api/labs/008/presets/{preset_id}`
- `POST /api/labs/008/evaluate`
- `POST /api/labs/008/evaluate-preset/{preset_id}`

Responses include surfaces, cross-cutting dimensions, organizational exposure, recommended controls/evidence, and always `"execution": "not_performed"`.

## Diagrams

- `agent-system-architecture.svg` — high-level components, public-model edge, network reach, independent evidence, external containment, and cross-cutting dimensions
- `agent-data-flow.svg` — numbered request, authority, context, tool, delegation, data, public-model egress, residual bypass, and telemetry flows
- `agent-threat-model.svg` — threat-case assessment flow from protected asset to residual risk

These are illustrative Cedar Quill Markets reference views, not a production architecture certification.

## Safety limitations

- Fictional Cedar Quill Markets data only.
- No real tool, credential, runtime, queue, or network action.
- Risk categories are illustrative, not production risk certification.
- Every evaluation returns `execution: not_performed`.

## Local testing

```bash
.venv/bin/python -m pytest labs/008-agent-threat-model/tests -q
```

## Production route

https://from-my-desk.com/labs/agent-threat-model
