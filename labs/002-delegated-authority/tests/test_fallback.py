"""Fallback never overrides DENY or performs execution."""

from __future__ import annotations

from delegated_authority.fallback import fallback_does_not_override, recommend_fallback
from delegated_authority.loader import load_bundle
from delegated_authority.service import evaluate_scenario


def test_deny_remains_deny_with_fallback():
    for scenario_id in (
        "execution_not_delegated",
        "parent_revoked",
        "parent_expired",
        "unknown_agent",
        "tool_inventory_changed",
    ):
        result = evaluate_scenario(load_bundle(), scenario_id)
        assert result.decision == "deny"
        assert result.fallback.available is True
        assert result.fallback.new_evaluation_required is True
        assert "execute_action" not in result.fallback.permitted_operations
        assert fallback_does_not_override(result.decision, result.fallback)


def test_unknown_agent_registration_fallback():
    result = evaluate_scenario(load_bundle(), "unknown_agent")
    assert result.fallback.fallback_type == "register_agent"


def test_revoked_not_auto_restored():
    fb = recommend_fallback("parent_revoked")
    assert "restore_revoked_authority" in fb.prohibited_operations
    assert fb.new_evaluation_required is True


def test_allow_has_no_fallback():
    result = evaluate_scenario(load_bundle(), "valid_narrow_delegation")
    assert result.decision == "allow"
    assert result.fallback.available is False
