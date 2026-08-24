# Decision semantics — Lab 002

## Precedence

**DENY > STEP_UP > CONFIRM > ALLOW**

Hard authorization failures always win. Confirmation and step-up never override them.

## ALLOW

The demonstrated policy currently permits the request.

Requirements include:

- Valid identity and principal binding
- Valid delegation chain
- Capability and resource within effective authority
- Amount within effective limit and at or below the autonomous confirmation threshold
- Valid time window
- Acceptable APE profile (known, no blocking mismatch)
- Compliant APSE posture with current evidence
- Acceptable context (`normal`)

ALLOW does **not** execute the action. Responses set `execution: not_performed` and may include a short `decision_valid_until` TTL. ALLOW is bound to the evaluated request fingerprint.

Example scenario: `valid_narrow_delegation`.

## CONFIRM

Authority is valid, but explicit business or principal confirmation is required.

Examples:

- Amount above the autonomous threshold (`confirmation_threshold`)
- Unusual but otherwise permitted context (`unusual_context`)

CONFIRM cannot repair invalid, expired, revoked, broken, or out-of-scope authority.

Example scenarios: `confirmation_required`, `unusual_context`.

## STEP_UP

Authority may be valid, but stronger assurance or fresher evidence is required.

Examples:

- Stale posture evidence (`posture_evidence_stale`)
- Recoverable noncompliant model/runtime version (`model_version_noncompliant`)
- Profile mismatch requiring human review (`profile_mismatch`)

STEP_UP cannot repair revoked, expired, missing, or out-of-scope authority.

Example scenarios: `stale_posture`, `noncompliant_model_version`, `profile_mismatch`.

## DENY

The original action is prohibited. DENY stops the action and produces evidence.

### Hard-denial conditions

- Unknown or invalid identity
- Wrong principal binding
- Suspended or revoked agent
- Parent expired or revoked
- Capability or resource not delegated
- Child broader than parent (capabilities, resources, limit, expiry)
- Redelegation prohibited or depth exceeded
- Broken delegation chain
- Compromised runtime
- Unapproved / changed tool inventory
- Unknown profile with no trusted registration path that grants authority

### Recoverable conditions (not DENY)

These typically produce CONFIRM or STEP_UP instead:

- Amount confirmation threshold
- Unusual context
- Stale posture evidence
- Recoverable version noncompliance
- Profile mismatch needing review

## Example conflicts

| Competing signals | Result |
| --- | --- |
| CONFIRM amount + DENY capability | DENY |
| STEP_UP stale posture + DENY parent revoked | DENY |
| CONFIRM unusual context + STEP_UP profile mismatch | STEP_UP |
| ALLOW-shaped request + tool inventory changed | DENY |
| Executor-looking profile + research-only envelope + execute request | DENY |

## Reason categories

Reason codes map to categories such as `policy_satisfied`, `business_confirmation`, `assurance_required`, `identity_failure`, `delegation_failure`, `profile_risk`, `posture_risk`, `lifecycle_failure`, and `system_failure` for UI and privacy-safe telemetry grouping.
