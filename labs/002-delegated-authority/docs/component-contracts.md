# Component contracts — Lab 002

Contracts below mirror the typed models in `src/delegated_authority/models.py`. All identifiers and amounts are fictional.

## Action request

**Input** to identity, delegation, APE, APSE, and policy.

| Field | Type | Notes |
| --- | --- | --- |
| `request_id` | string | Correlation id for the demo request |
| `principal_id` | string | Human principal reference |
| `agent_id` | string | Acting agent |
| `requested_capability` | string | e.g. `research`, `execute` |
| `requested_resource` | string | e.g. `market-summaries` |
| `requested_amount` | Decimal | Non-negative; Decimal, not float |
| `request_time` | string | ISO-8601 evaluation time |
| `delegation_id` | string | Leaf envelope id |
| `context` | string | `normal` or `unusual` |
| `assurance_level` | string | Requested assurance hint |

Scenario evaluation accepts only `{ "scenario_id": "..." }` at the HTTP boundary; the service expands the allowlisted scenario into an `ActionRequest`.

## Identity result

| Field | Values |
| --- | --- |
| `identity_status` | `valid` \| `invalid` \| `unknown` |
| `agent_status` | `active` \| `suspended` \| `revoked` \| `unknown` |
| `principal_binding` | `valid` \| `invalid` |
| `assurance_level` | string |
| `evaluated_at` | ISO-8601 |
| `reason_code` | optional (e.g. `agent_unknown`, `principal_mismatch`) |

Hard outcomes: unknown, invalid, suspended, revoked, or principal mismatch → DENY candidates.

## Delegation result

| Field | Notes |
| --- | --- |
| `chain_status` | `valid` \| `broken` \| `expired` \| `revoked` \| `constraint_violation` |
| `chain_path` | Display names / roles along the chain |
| `effective_capabilities` | Intersection of capabilities |
| `effective_resources` | Intersection of resources |
| `effective_limit` | Min of maximum amounts (string Decimal) |
| `effective_expiry` | Earliest expiry |
| `redelegation_allowed` | bool |
| `violated_constraint` | optional machine hint |
| `chain_version` | version stamp |
| `reason_code` | optional denial code |

## APE result (`AgentProfile`)

| Field | Notes |
| --- | --- |
| `agent_id` | Profiled agent |
| `classification` | e.g. Research Agent |
| `declared_attributes` | type, model, tools, declared capabilities, owner |
| `observed_attributes` | typical access, tools, actions, period, behavior |
| `verified_attributes` | signed manifest, approved version, attested runtime, environment, verified tools |
| `expected_capabilities` / `expected_tools` | Profile expectations |
| `management_status` | managed / unmanaged hint |
| `confidence` | `high` \| `medium` \| `low` |
| `profile_mismatch` | bool |
| `profile_status` | `known` \| `unknown` \| `conflicting` |
| `profile_version` | string |

## APSE result (`PostureEvidence`)

| Field | Notes |
| --- | --- |
| `posture_status` | `compliant` \| `noncompliant` \| `unknown` \| `stale` |
| `risk_level` | `low` \| `medium` \| `high` |
| `model_version_status` | approved / noncompliant / outdated |
| `configuration_integrity` | integrity signal |
| `tool_inventory_status` | expected / changed / unexpected / unauthorized |
| `attestation_status` | educational placeholder |
| `credential_status` | educational placeholder |
| `behavior_status` | anomaly flag |
| `evidence_freshness` | `current` \| `stale` \| `missing` |
| `recommended_treatment` | `continue` \| `confirm` \| `step_up` \| `deny` \| `restricted_fallback` |
| `posture_version` | string |
| `reason_code` | optional |

## Policy result

Policy returns a tuple folded into `EvaluationResult`:

| Field | Notes |
| --- | --- |
| `decision` | `allow` \| `confirm` \| `step_up` \| `deny` |
| `reason_code` | Stable code from the allowlist in models |
| `reason_category` | Grouping for UI / telemetry categories |
| `explanation` | Human-readable educational text |
| `violated_constraint` | optional |
| `decision_valid_until` | set for ALLOW only (short TTL) |

## Fallback (`FallbackRecommendation`)

| Field | Notes |
| --- | --- |
| `available` | bool |
| `fallback_type` | Restricted enum (`register_agent`, `refresh_posture`, …) |
| `explanation` | Recovery guidance |
| `permitted_operations` | Never includes execute-on-deny |
| `prohibited_operations` | e.g. `override_deny`, `execute_action` |
| `new_evaluation_required` | true for all recovery paths |

## Audit record

| Field | Notes |
| --- | --- |
| `audit_id` | e.g. `audit_demo_0001` |
| `request_id` | From the action request |
| `timestamp` | Evaluation time |
| `principal_reference` / `agent_reference` | Sanitized placeholders |
| `delegation_chain_reference` | Leaf id reference |
| `delegation_chain_version` | From chain |
| `ape_profile_status` / `ape_profile_version` | Profile stamps |
| `apse_posture_status` / `apse_posture_version` | Posture stamps |
| `evidence_freshness` | From APSE |
| `policy_version` | From policy YAML |
| `decision` / `reason_code` | Outcome |
| `fallback_offered` | Fallback type string |
| `execution` | Always `not_performed` |

Public API responses expose `audit_id` and summaries; they do not expose raw credential or attestation material.
