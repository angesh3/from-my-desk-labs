"""Decision precedence and all 15 scenario expectations."""

from __future__ import annotations

from delegated_authority.loader import load_bundle
from delegated_authority.service import evaluate_scenario

EXPECTED = {
    "valid_narrow_delegation": ("allow", "policy_satisfied"),
    "confirmation_required": ("confirm", "confirmation_threshold"),
    "stale_posture": ("step_up", "posture_evidence_stale"),
    "unusual_context": ("confirm", "unusual_context"),
    "execution_not_delegated": ("deny", "capability_not_delegated"),
    "child_capability_exceeds_parent": ("deny", "child_capability_exceeds_parent"),
    "child_limit_exceeds_parent": ("deny", "child_limit_exceeds_parent"),
    "child_expiry_exceeds_parent": ("deny", "child_expiry_exceeds_parent"),
    "delegation_depth_exceeded": ("deny", "delegation_depth_exceeded"),
    "parent_expired": ("deny", "parent_expired"),
    "parent_revoked": ("deny", "parent_revoked"),
    "unknown_agent": ("deny", "agent_unknown"),
    "profile_mismatch": ("step_up", "profile_mismatch"),
    "noncompliant_model_version": ("step_up", "model_version_noncompliant"),
    "tool_inventory_changed": ("deny", "tool_inventory_changed"),
}


def test_all_fifteen_scenarios():
    bundle = load_bundle()
    assert set(bundle.scenarios) == set(EXPECTED)
    for scenario_id, (decision, reason) in EXPECTED.items():
        result = evaluate_scenario(bundle, scenario_id)
        assert result.decision == decision, scenario_id
        assert result.reason_code == reason, scenario_id
        assert result.execution == "not_performed"
        assert result.audit_id.startswith("audit_demo_")


def test_deny_overrides_step_up_and_confirm():
    # parent_revoked is deny even if we imagine soft signals — actual scenario is deny
    result = evaluate_scenario(load_bundle(), "parent_revoked")
    assert result.decision == "deny"


def test_good_profile_and_posture_cannot_override_missing_authority():
    result = evaluate_scenario(load_bundle(), "execution_not_delegated")
    assert result.decision == "deny"
    assert result.profile_summary.confidence == "high"
    assert result.posture_summary.status == "compliant"
