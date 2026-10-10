# Lab 007 assurance policy

Deterministic educational rules for Cedar Quill Markets. No LLM, no network,
no probabilistic scoring.

## Principles

1. Enforcement intention and assurance outcome remain separate.
2. Agent self-report is never sufficient independent evidence.
3. Known continued execution is FAILED even when telemetry is incomplete.
4. Residual capability without observed continuation is PARTIAL.
5. Missing independent evidence is UNVERIFIED.
6. CONFIRMED requires positive independent evidence for required dimensions.
7. CONFIRMED is time-bounded within the evidence window; regression is FAILED.
8. Real execution is always `not_performed`.

## Precedence

`FAILED > PARTIAL > UNVERIFIED > CONFIRMED`

## Required check dimensions

- primary_runtime_stopped
- active_sessions_revoked
- delegated_credentials_revoked
- tool_access_disabled
- queued_actions_cancelled
- scheduled_work_cancelled
- child_agents_stopped
- network_egress_blocked
- alternate_network_paths_checked
- persistent_state_quarantined
- restart_recovery_disabled
- telemetry_coverage_complete
- evidence_freshness_acceptable
- evidence_source_independence
- post_containment_activity_absent
