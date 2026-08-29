"""Policy invariants for Lab 003."""

from __future__ import annotations

from agent_access_control.loader import load_bundle
from agent_access_control.management import AgentManagementPlane
from agent_access_control.models import AccessRequest
from agent_access_control.profiler import evaluate_profile, profile_cannot_grant_authority
from agent_access_control.restricted import recommend_restricted, restricted_does_not_override
from agent_access_control.service import evaluate_scenario


def test_ape_cannot_manufacture_missing_authority():
    bundle = load_bundle()
    management = AgentManagementPlane(bundle.agents)
    request = AccessRequest.model_validate(
        bundle.scenarios["undelegated_capability"]["request"]
    )
    profile, _ = evaluate_profile(request, bundle.profiles, management)
    assert profile.confidence == "high"
    assert profile_cannot_grant_authority(profile, ["read"], "execute") is True
    result = evaluate_scenario(bundle, "undelegated_capability")
    assert result.decision == "deny"
    assert result.reason_code == "capability_not_delegated"


def test_apse_cannot_expand_authority_with_compliant_posture():
    result = evaluate_scenario(load_bundle(), "undelegated_capability")
    assert result.posture_summary.status == "compliant"
    assert result.decision == "deny"


def test_restricted_recovery_never_overrides_deny():
    for scenario_id in (
        "undelegated_capability",
        "unknown_agent_protected_tool",
        "data_boundary_violation",
    ):
        result = evaluate_scenario(load_bundle(), scenario_id)
        assert result.decision == "deny"
        restricted = recommend_restricted(result.reason_code)
        assert restricted_does_not_override("deny", restricted)


def test_good_profile_and_posture_cannot_override_missing_delegation():
    result = evaluate_scenario(load_bundle(), "undelegated_capability")
    assert result.profile_summary.confidence == "high"
    assert result.posture_summary.status == "compliant"
    assert result.decision == "deny"
