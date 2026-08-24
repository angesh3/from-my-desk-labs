"""APE profiling tests — profiling cannot manufacture authority."""

from __future__ import annotations

from delegated_authority.loader import load_bundle
from delegated_authority.management import AgentManagementPlane
from delegated_authority.models import ActionRequest
from delegated_authority.profiler import evaluate_profile, profile_cannot_grant_authority
from delegated_authority.service import evaluate_scenario


def test_declared_observed_verified_present():
    bundle = load_bundle()
    management = AgentManagementPlane(bundle.agents)
    request = ActionRequest.model_validate(bundle.scenarios["valid_narrow_delegation"]["request"])
    profile = evaluate_profile(request, bundle.profiles, management)
    assert profile.declared_attributes.agent_type
    assert profile.observed_attributes.typical_action_types
    assert profile.verified_attributes.signed_manifest is True
    assert profile.profile_status == "known"


def test_unknown_profile_handled():
    bundle = load_bundle()
    management = AgentManagementPlane(bundle.agents)
    request = ActionRequest.model_validate(
        {
            **bundle.scenarios["valid_narrow_delegation"]["request"],
            "agent_id": "missing-agent",
            "request_id": "req-missing",
        }
    )
    profile = evaluate_profile(request, bundle.profiles, management)
    assert profile.profile_status == "unknown"
    assert profile.confidence == "low"


def test_profile_mismatch_detected():
    result = evaluate_scenario(load_bundle(), "profile_mismatch")
    assert result.decision == "step_up"
    assert result.reason_code == "profile_mismatch"
    assert result.profile_summary.profile_mismatch is True


def test_execution_profile_cannot_bypass_research_only_delegation():
    bundle = load_bundle()
    management = AgentManagementPlane(bundle.agents)
    request = ActionRequest.model_validate(
        {
            "request_id": "req-exec-profile",
            "principal_id": "principal-demo-001",
            "agent_id": "execution-profile-agent",
            "requested_capability": "execute",
            "requested_resource": "market-summaries",
            "requested_amount": "100.00",
            "request_time": "2026-03-15T14:00:00Z",
            "delegation_id": "del-portfolio-exec-profile-research-only",
            "context": "normal",
        }
    )
    profile = evaluate_profile(request, bundle.profiles, management)
    assert "Execution" in profile.classification
    assert profile_cannot_grant_authority(profile, ["research"], "execute") is True
    # Full evaluation must DENY — profile does not grant execute
    from delegated_authority.delegation import evaluate_delegation
    from delegated_authority.identity import evaluate_identity
    from delegated_authority.policy import decide
    from delegated_authority.posture import evaluate_posture

    identity = evaluate_identity(request, bundle.agents)
    delegation = evaluate_delegation(request, bundle.delegations)
    posture = evaluate_posture(request, bundle.posture, management)
    decision, reason, _, _ = decide(
        request, identity, delegation, profile, posture, bundle.policies["delegation"]
    )
    assert decision == "deny"
    assert reason == "capability_not_delegated"
