# Profile model (APE) — Lab 002

## Role

The Agent Profiling Engine (APE) answers: **what kind of agent appears to be acting?** It supplies classification and confidence for policy selection and human review. It does not issue capabilities.

> **Profiling can inform trust and policy selection. It must not manufacture authority.**

## Attribute layers

### Declared

What the agent (or its owner) claims:

- Agent type / classification label
- Model identifier (fictional)
- Tool list
- Declared capabilities
- Owner reference

### Observed

What educational telemetry suggests about typical behavior:

- Typical data access
- Typical tool usage
- Typical action types
- Typical operating period
- Observed execution behavior

### Verified

What the management / attestation placeholders assert:

- Signed manifest present (boolean demo flag)
- Approved software version
- Attested runtime (boolean demo flag)
- Registered environment
- Verified tool inventory

## Profile status and confidence

| Status | Meaning | Typical decision effect |
| --- | --- | --- |
| `known` | Profile available and consistent | Continues if other stages pass |
| `unknown` | No trusted profile | DENY (`agent_unknown` / profile unknown path) |
| `conflicting` | Declared vs observed/verified disagree | STEP_UP (`profile_mismatch`) |

Confidence is `high`, `medium`, or `low`. Lower confidence may inform UI messaging; it does not expand authority.

## Profile mismatch

When declared attributes conflict with observed or verified attributes (for example, a research registration behaving like an executor), APE sets `profile_mismatch` and policy raises STEP_UP for human review. Fallback may recommend `request_human_review` or `collect_profile`.

## Management status

APE consults the management plane for whether the agent is registered and managed. Unmanaged or unknown agents cannot rely on profile alone to proceed.

## Critical invariant

If the requested capability is not in the delegation’s **effective** capabilities, policy DENYs even when the profile classification looks like an executor:

> Profiling cannot manufacture missing delegated authority.

Scenario `execution_not_delegated` demonstrates a research-only envelope rejecting `execute` despite any profile flavor.

## Limitations

- Profiles are YAML fixtures, not live behavioral ML
- Verified attributes are educational placeholders, not real attestation
- Confidence does not decay over time in this spike
- Profile poisoning and adversarial registration are deferred (see limitations doc)
