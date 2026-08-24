# Architecture — Lab 002 Delegated Authority

## Purpose

Lab 002 demonstrates continuous policy evaluation for a multi-hop agent delegation chain. The Trust Gateway answers whether a request may proceed under delegated authority at the moment of action. Execution remains outside the lab boundary.

## End-to-end path

```
Reader
  → Lab page (/labs/delegated-authority)
  → GET /api/labs/002/scenarios
  → POST /api/labs/002/evaluate { scenario_id }
  → Trust Gateway (delegated_authority package)
  → Decision + explanation + audit_id + fallback
  → Reader (execution: not_performed)
```

The website hosts routing, templates, and static assets. The lab package owns policy evaluation.

Five unique teaching diagrams (do not substitute one for another):

| Layer | Source | Served as |
| --- | --- | --- |
| End-to-end workflow | `diagrams/delegated-authority-workflow.svg` | `/static/labs/002/delegated-authority-workflow.svg` |
| Trust Gateway internals | `diagrams/system-architecture.svg` | `/static/labs/002/system-architecture.svg` |
| Evaluation order | `diagrams/evaluation-flow.svg` | `/static/labs/002/evaluation-flow.svg` |
| Restricted fallback | `diagrams/fallback-flow.svg` | `/static/labs/002/fallback-flow.svg` |
| Revocation propagation | `diagrams/revocation-flow.svg` | `/static/labs/002/revocation-flow.svg` |

`architecture.svg` previously duplicated `system-architecture.svg` and was removed. See `docs/ASSETS.md`. Hosting-path Mermaid source (optional): `diagrams/lab-runtime.mmd`.

## Trust Gateway responsibilities

The gateway orchestrates:

| Stage | Module | Role |
| --- | --- | --- |
| Identity | `identity.py` | Agent lifecycle, principal binding, assurance |
| Delegation | `delegation.py` | Chain walk, parent–child invariants, effective authority |
| APE | `profiler.py` | Declared / observed / verified profile |
| APSE | `posture.py` | Posture status, freshness, hard vs recoverable risk |
| Management | `management.py` | Registration and managed status (educational registry) |
| Policy | `policy.py` | Combine signals; apply DENY > STEP_UP > CONFIRM > ALLOW |
| Fallback | `fallback.py` | Restricted recovery recommendations |
| Audit | `audit.py` | Evidence record for the decision |
| Service | `service.py` | Scenario materialization and journey steps |
| Gateway API | `gateway.py` | HTTP routes for scenarios and evaluate |

## Agent Profiling Engine (APE)

APE classifies what kind of agent appears to be acting using declared, observed, and verified attributes. Profile mismatch or conflict can raise STEP_UP. An “executor-looking” profile cannot grant a capability missing from the delegation envelope.

**Profiling can inform trust and policy selection. It must not manufacture authority.**

## Agent Posture and Security Engine (APSE)

APSE evaluates whether the agent is currently in a trusted condition: management status, version, configuration integrity, tool inventory, attestation placeholders, credential health indicators, behavioral flags, and evidence freshness. Stale evidence or recoverable version issues raise STEP_UP. Compromised runtime or unexpected tool inventory raise DENY.

**Posture can restrict the use of existing authority. It cannot expand authority.**

## Agent Management Plane

The management plane is a fictional registry of agents and lifecycle state (active, suspended, revoked, unknown). Unknown agents DENY with a restricted registration fallback. Suspended or revoked agents DENY. The plane does not mint delegations on its own; it informs identity and profile evaluation.

## Delegation evaluator

Walks parent links from the leaf envelope, computes effective capabilities, resources, limit, and expiry as the intersection (narrowing) of the chain, and enforces:

- Child ⊆ parent for capabilities and resources
- Child maximum amount ≤ parent maximum amount
- Child expiry ≤ parent expiry
- Redelegation and remaining depth rules
- Requested capability and resource ⊆ effective authority
- Parent expired / revoked → downstream invalid

## Policy

`policy.py` collects candidate outcomes from identity, delegation, profile, posture, and business context, then selects the most restrictive decision. ALLOW requires every mandatory control to pass. Amount confirmation uses Decimal thresholds from `policies/delegation-policy.yaml`.

## Audit

Every evaluation produces an `audit_id` and a structured record with sanitized references, version stamps, evidence freshness, decision, reason code, and `execution: not_performed`. This educational audit is response-scoped, not a durable WORM store.

## Fallback

When a reason code maps to a recovery path, the response includes a fallback recommendation: permitted operations, prohibited operations, and `new_evaluation_required: true`. Fallback never converts DENY into permission.

## Execution boundary

There is no executor, broker adapter, or tool runner in Lab 002. ALLOW means policy approval for a fictional request only. The response field `execution` is always `not_performed`.

## Data and policy layout

| Path | Contents |
| --- | --- |
| `examples/agents.yaml` | Fictional agent registry |
| `examples/profiles.yaml` | APE profile fixtures |
| `examples/posture.yaml` | APSE posture fixtures |
| `examples/delegations.yaml` | Delegation envelopes |
| `examples/scenarios.yaml` | Fifteen educational scenarios |
| `policies/delegation-policy.yaml` | Confirm threshold, TTL, notes |
| `policies/posture-policy.yaml` | Posture treatment hints |
| `policies/fallback-policy.yaml` | Fallback invariants |

## Separation from Lab 001

Lab 001 focuses on identity versus authority for a single paper-order proposal with amount bands. Lab 002 focuses on multi-hop narrowing, APE/APSE, revocation propagation, and restricted fallback. Lab 001 routes and policy behavior remain unchanged.
