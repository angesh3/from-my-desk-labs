"""APSE posture tests — posture cannot expand authority."""

from __future__ import annotations

from delegated_authority.loader import load_bundle
from delegated_authority.management import AgentManagementPlane
from delegated_authority.models import ActionRequest
from delegated_authority.posture import evaluate_posture
from delegated_authority.service import evaluate_scenario


def test_compliant_stale_version_tools():
    assert evaluate_scenario(load_bundle(), "valid_narrow_delegation").decision == "allow"
    assert evaluate_scenario(load_bundle(), "stale_posture").decision == "step_up"
    assert evaluate_scenario(load_bundle(), "noncompliant_model_version").decision == "step_up"
    assert evaluate_scenario(load_bundle(), "tool_inventory_changed").decision == "deny"


def test_compromised_runtime_denies():
    bundle = load_bundle()
    management = AgentManagementPlane(bundle.agents)
    request = ActionRequest.model_validate(bundle.scenarios["valid_narrow_delegation"]["request"])
    posture_map = {
        request.agent_id: {
            "agent_id": request.agent_id,
            "posture_status": "noncompliant",
            "risk_level": "high",
            "model_version_status": "approved",
            "configuration_integrity": "intact",
            "tool_inventory_status": "expected",
            "attestation_status": "compromised",
            "credential_status": "healthy",
            "behavior_status": "anomalous",
            "evidence_freshness": "current",
            "recommended_treatment": "deny",
            "reason_code": "runtime_compromised",
            "posture_version": "1",
        }
    }
    posture = evaluate_posture(request, posture_map, management)
    assert posture.recommended_treatment == "deny"
    assert posture.reason_code == "runtime_compromised"


def test_posture_cannot_expand_missing_authority():
    # Good posture on execution_not_delegated still DENY
    result = evaluate_scenario(load_bundle(), "execution_not_delegated")
    assert result.decision == "deny"
    assert result.posture_summary.status == "compliant"
