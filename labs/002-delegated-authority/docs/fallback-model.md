# Fallback model — Lab 002

## Core rule

> **Fallback may create a new recovery or authorization path. It never converts the original DENY into permission.**

Restricted fallback is advice attached to an evaluation result. The original decision remains immutable. Remediation requires a **new** policy evaluation with a new request (and often a new delegation id).

## Properties of every recovery fallback

- `available: true` (except when policy is fully satisfied)
- Explicit `fallback_type`
- Human-readable explanation
- `permitted_operations` — recovery actions only
- `prohibited_operations` — always includes execute / override paths for DENY cases
- `new_evaluation_required: true`

Fallback never sets `execution` to anything other than the evaluation’s `not_performed`.

## Fallback types in this spike

| Type | Typical reason codes | Intent |
| --- | --- | --- |
| `register_agent` | `agent_unknown` | Restricted registration, then re-evaluate |
| `collect_profile` | profile gaps / mismatch support | Gather APE inputs |
| `refresh_posture` | `posture_evidence_stale` | Refresh APSE evidence |
| `request_human_review` | mismatch, revoke, confirm paths | Human judgment |
| `request_new_delegation` | missing capability, expiry | Issue a new envelope |
| `request_narrower_action` | child exceeds parent | Shrink the request or child envelope |
| `correct_delegation` | capability subset fixes | Fix envelope definition |
| `correct_delegation_period` | child expiry exceeds parent | Fix validity windows |
| `request_direct_delegation` | depth exceeded | Skip illegal redelegation |
| `upgrade_version` | model version noncompliant | Move to approved version |
| `restore_approved_configuration` | config integrity issues | Return to approved config |
| `investigate_tool_change` | tool inventory changed | Investigate before any new auth |
| `none` | `policy_satisfied` | No recovery needed |

## Registration fallback

Unknown agents DENY with `register_agent`. Registration is not automatic authority. After registration, profile collection and a **new** evaluation are required. The original DENY remains on the audit trail for the failed request.

## Posture refresh

Stale evidence offers `refresh_posture`. Refreshing evidence does not rewrite the prior STEP_UP decision; it enables a subsequent evaluation.

## Human review

Used for profile mismatch, unusual context, confirmation, and revoked-authority paths. Reviewers may authorize a new path; they do not silently flip the stored decision to ALLOW.

## New or narrower delegation

Missing capability or parent expiry/revoke recovery points to new or corrected envelopes. Child-exceeds-parent cases point to narrower actions or corrected child limits — not parent expansion by the child.

## Upgrade / configuration recovery

Version and configuration issues recommend upgrade or restore paths. Neither path executes the original tool action.

## Invariants (tests encode these)

- DENY remains DENY when fallback exists
- Fallback requires a new evaluation
- Revoked authority is not automatically restored
- Expired authority is not automatically restored
- No fallback performs execution
- Original audit record remains unchanged by remediation UI

See `diagrams/fallback-flow.mmd` and `policies/fallback-policy.yaml`.
