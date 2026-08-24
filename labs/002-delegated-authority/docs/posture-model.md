# Posture model (APSE) — Lab 002

## Role

The Agent Posture and Security Engine (APSE) answers: **is this agent currently in a trusted condition to use authority it already has?**

> **Posture can restrict the use of existing authority. It cannot expand authority.**

## Signals evaluated

| Signal | Educational meaning |
| --- | --- |
| Registration / management status | Agent known to the management plane |
| Version compliance | Model/runtime on approved list |
| Configuration integrity | Expected configuration intact |
| Tool inventory | Tools match verified inventory |
| Attestation | Placeholder attestation status |
| Credential health | Placeholder credential signal |
| Behavioral anomalies | Unusual behavior flags |
| Delegation-chain integrity | Consumed via delegation stage; posture may amplify risk |
| Revocation | Lifecycle handled in identity/delegation; posture does not restore |
| Telemetry freshness | `evidence_freshness`: current / stale / missing |

## Treatments

| Condition | Typical decision |
| --- | --- |
| Compliant + current evidence | Continue (no posture challenge) |
| Stale evidence | STEP_UP (`posture_evidence_stale`) |
| Recoverable noncompliant / outdated version | STEP_UP (`model_version_noncompliant`) |
| Unexpected / changed / unauthorized tools | DENY (`tool_inventory_changed`) |
| Compromised runtime | DENY (`runtime_compromised`) |

`recommended_treatment` on the posture object is advisory input to policy. Policy still applies global precedence and never lets posture invent a capability.

## Evidence freshness

Stale or missing evidence means the system cannot trust that posture remains good. The educational response is STEP_UP plus a `refresh_posture` fallback, not silent ALLOW.

## Hard vs recoverable

Recoverable posture issues ask for stronger assurance or remediation before using existing authority. Hard posture failures stop the original action. Neither path grants new capabilities.

## Interaction with delegation

APSE never widens effective capabilities, resources, limits, or expiry. A compliant posture on a research-only agent still DENYs an `execute` request. A revoked parent still DENYs even if posture is pristine.

## Limitations

- No real runtime attestation or TPM-backed evidence
- No continuous streaming posture agent
- Credential and attestation fields are fictional
- Posture spoofing defenses are deferred

See `policies/posture-policy.yaml` and scenario fixtures in `examples/posture.yaml`.
