"""Decision precedence and all 14 scenario expectations."""

from __future__ import annotations

from agent_access_control.loader import load_bundle
from agent_access_control.service import evaluate_scenario

EXPECTED = {
    "managed_public_data_read": ("allow", "within_current_authority"),
    "sensitive_action_consent": ("confirm", "human_consent_required"),
    "stale_runtime_attestation": ("step_up", "posture_evidence_stale"),
    "unapproved_model": ("step_up", "model_version_noncompliant"),
    "undelegated_capability": ("deny", "capability_not_delegated"),
    "unknown_agent_protected_tool": ("deny", "unknown_agent_protected_action"),
    "unknown_agent_registration": ("allow", "restricted_registration_permitted"),
    "undeclared_tool": ("deny", "tool_inventory_changed"),
    "data_boundary_violation": ("deny", "data_classification_exceeds_authority"),
    "parent_delegation_expired": ("deny", "parent_delegation_expired"),
    "parent_delegation_revoked": ("deny", "parent_delegation_revoked"),
    "purpose_conflict": ("deny", "purpose_not_permitted"),
    "limit_requires_confirmation": ("confirm", "limit_requires_confirmation"),
    "material_context_change": ("step_up", "context_change_requires_step_up"),
}


def test_all_fourteen_scenarios():
    bundle = load_bundle()
    assert set(bundle.scenarios) == set(EXPECTED)
    for scenario_id, (decision, reason) in EXPECTED.items():
        result = evaluate_scenario(bundle, scenario_id)
        assert result.decision == decision, scenario_id
        assert result.reason_code == reason, scenario_id
        assert result.execution == "not_performed"
        assert result.audit_id.startswith("audit_demo_")


def test_deny_overrides_step_up_and_confirm():
    result = evaluate_scenario(load_bundle(), "parent_delegation_revoked")
    assert result.decision == "deny"


def test_restricted_registration_is_allow_not_operational():
    result = evaluate_scenario(load_bundle(), "unknown_agent_registration")
    assert result.decision == "allow"
    assert result.reason_code == "restricted_registration_permitted"
    assert result.restricted.available is True
    assert "register_agent" in result.restricted.permitted_operations
    assert "execute_action" in result.restricted.prohibited_operations
