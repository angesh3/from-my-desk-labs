# Audit evidence — Lab 002

## Why DENY is evidence

A DENY is not only a stop signal. It is proof that the Trust Gateway enforced a boundary at a specific time, against a specific request fingerprint, under named policy and evidence versions. In educational terms: **the system refused to pretend authority existed**.

ALLOW, CONFIRM, and STEP_UP are also audited. DENY is highlighted because organizations often under-invest in recording successful refusals.

## Audit fields

Each evaluation creates an `AuditRecord` (see `audit.py`):

| Field | Purpose |
| --- | --- |
| `audit_id` | Demo identifier returned to the client |
| `request_id` | Links to the fictional request |
| `timestamp` | Evaluation time |
| `principal_reference` | Sanitized placeholder (not raw principal secrets) |
| `agent_reference` | Sanitized placeholder |
| `delegation_chain_reference` | Leaf delegation reference |
| `delegation_chain_version` | Chain version stamp |
| `ape_profile_status` / `ape_profile_version` | Profile evidence versioning |
| `apse_posture_status` / `apse_posture_version` | Posture evidence versioning |
| `evidence_freshness` | current / stale / missing |
| `policy_version` | Policy YAML version |
| `decision` | allow / confirm / step_up / deny |
| `reason_code` | Stable machine reason |
| `fallback_offered` | Fallback type string |
| `execution` | Always `not_performed` |

## Evidence freshness

Stale or missing APSE evidence is recorded even when the decision is STEP_UP rather than DENY. Freshness is part of accountability: reviewers can see whether the system acted on current or aged signals.

## Versions

Policy, profile, posture, and delegation versions travel with the audit so later readers can tell **which** educational rules produced the outcome. This is not cryptographic notarization; it is demo provenance.

## Execution status

Audit always records `execution: not_performed`. That field is intentional: policy evaluation must not be confused with tool or brokerage execution.

## Privacy and sanitization

- Public responses expose `audit_id`, summaries, and explanations — not raw credential or attestation blobs
- Principal and agent fields in the audit use sanitized references in this spike
- Product telemetry must never receive `audit_id`, principal, agent, delegation, amounts, or raw JSON
- This educational audit is response-scoped; it is not a durable, access-controlled, tamper-evident store

## Production gap (intentional)

A production audit system would need durable storage, access control, integrity protection, retention policy, and legal hold. Lab 002 demonstrates the **shape** of evidence, not the operational archive.
