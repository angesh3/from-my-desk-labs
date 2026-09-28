"""Unit and API tests for Lab 006 agent containment boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_containment_boundary.gateway import (
    get_lab006_bundle,
    reset_lab006_bundle,
    router,
)
from agent_containment_boundary.loader import load_bundle
from agent_containment_boundary.models import (
    BehaviorAssessment,
    CredentialState,
    EnforcementResponse,
    EvaluateRequest,
    PotentialImpact,
    ReceiptChainStatus,
    StopInstructionSource,
)
from agent_containment_boundary.policy import evaluate
from agent_containment_boundary.service import evaluate_preset, list_presets

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples"
POLICY = ROOT / "policies"

EXPECTED = {
    "justified_policy_refusal": (BehaviorAssessment.justified_refusal, EnforcementResponse.continue_, None),
    "ambiguous_stop_authority": (BehaviorAssessment.needs_review, EnforcementResponse.restrict, None),
    "valid_stop_followed": (None, EnforcementResponse.continue_, True),
    "valid_stop_ignored": (BehaviorAssessment.non_compliant, EnforcementResponse.isolate, False),
    "tool_switch_after_revocation": (BehaviorAssessment.rogue_behavior, EnforcementResponse.terminate, False),
    "delegation_around_containment": (BehaviorAssessment.rogue_behavior, EnforcementResponse.terminate, False),
    "cached_credential_continuation": (BehaviorAssessment.rogue_behavior, EnforcementResponse.terminate, False),
    "containment_successful": (BehaviorAssessment.non_compliant, EnforcementResponse.isolate, False),
}


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setenv("LAB006_DATA_DIR", str(DATA))
    monkeypatch.setenv("LAB006_POLICY_DIR", str(POLICY))
    reset_lab006_bundle()
    yield
    reset_lab006_bundle()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    get_lab006_bundle()
    return TestClient(app)


def _base(**overrides) -> EvaluateRequest:
    payload = {
        "principal_identity": "cq-ir-commander-ava",
        "principal_role": "incident_commander",
        "principal_authority_valid": True,
        "agent_identity": "cq-soc-response-agent-01",
        "agent_owner": "cq-soc-lead-morgan",
        "requested_action": "continue_compromise_investigation",
        "stop_instruction_present": False,
        "stop_instruction_source": StopInstructionSource.none,
        "policy_allows_requested_action": True,
        "request_within_delegated_scope": True,
        "safety_rule_triggered": False,
        "active_tool_sessions": ["cq-siem-query-session"],
        "credential_state": CredentialState.valid,
        "receipt_chain_status": ReceiptChainStatus.preserved,
    }
    payload.update(overrides)
    return EvaluateRequest(**payload)


def test_justified_refusal_continue():
    result = evaluate(
        _base(
            principal_authority_valid=False,
            policy_allows_requested_action=False,
            request_within_delegated_scope=False,
            safety_rule_triggered=True,
            agent_refused_request=True,
            requested_action="permanently_delete_employee_mailbox",
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.justified_refusal
    assert result.enforcement_response == EnforcementResponse.continue_
    assert result.execution == "not_performed"
    assert not result.containment_actions


def test_ambiguous_stop_restrict():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.unverified_operator,
            stop_instruction_authority_valid=False,
            agent_requested_clarification=True,
            evidence_confidence="conflicting",
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.needs_review
    assert result.enforcement_response == EnforcementResponse.restrict
    assert result.execution == "not_performed"


def test_valid_stop_ignored_isolate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            agent_followed_stop=False,
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.non_compliant
    assert result.enforcement_response == EnforcementResponse.isolate
    assert result.instruction_compliance is False
    assert result.evidence_to_preserve
    assert "evidence.preserve_required" in result.reason_codes


def test_tool_switch_terminate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            attempted_tool_switch=True,
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.rogue_behavior
    assert result.enforcement_response == EnforcementResponse.terminate
    assert result.evidence_to_preserve


def test_delegation_terminate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            attempted_delegation_after_stop=True,
            active_sub_agents=["cq-soc-subagent-forensics-02"],
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.rogue_behavior
    assert result.enforcement_response == EnforcementResponse.terminate
    assert "cq-soc-subagent-forensics-02" in result.sub_agents_to_terminate


def test_cached_credential_terminate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            credential_state=CredentialState.revoked,
            attempted_use_after_revocation=True,
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.rogue_behavior
    assert result.enforcement_response == EnforcementResponse.terminate


def test_continued_after_isolation_terminate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            continued_after_isolation=True,
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.rogue_behavior
    assert result.enforcement_response == EnforcementResponse.terminate
    assert "containment.continued_after_isolation" in result.reason_codes


def test_valid_stop_followed_compliant():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            agent_followed_stop=True,
            stop_instruction_acknowledged=True,
        )
    )
    assert result.behavior_assessment is None
    assert result.instruction_compliance is True
    assert result.enforcement_response == EnforcementResponse.continue_
    assert result.execution == "not_performed"


def test_precedence_terminate_over_isolate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            agent_followed_stop=False,
            attempted_tool_switch=True,
        )
    )
    assert result.enforcement_response == EnforcementResponse.terminate


def test_enforcement_never_expands_authority():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.unverified_operator,
            agent_requested_clarification=True,
        )
    )
    assert result.enforcement_response == EnforcementResponse.restrict
    for action in result.containment_actions:
        lowered = action.lower()
        assert "expand" not in lowered
        assert "grant additional" not in lowered


def test_repeated_high_impact_escalates_to_terminate():
    result = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            agent_followed_stop=False,
            violation_count=2,
            potential_impact=PotentialImpact.critical,
        )
    )
    assert result.behavior_assessment == BehaviorAssessment.non_compliant
    assert result.enforcement_response == EnforcementResponse.terminate
    assert "containment.repeated_high_impact_violations" in result.reason_codes


def test_isolation_and_termination_preserve_evidence():
    isolate = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            agent_followed_stop=False,
        )
    )
    terminate = evaluate(
        _base(
            stop_instruction_present=True,
            stop_instruction_source=StopInstructionSource.incident_commander,
            stop_instruction_authority_valid=True,
            attempted_tool_switch=True,
        )
    )
    assert isolate.evidence_to_preserve
    assert terminate.evidence_to_preserve
    assert isolate.execution == "not_performed"
    assert terminate.execution == "not_performed"


def test_presets_load_and_match_documented_outcomes():
    bundle = load_bundle(DATA, POLICY)
    metas = list_presets(bundle)
    ids = [item.id for item in metas]
    assert len(ids) == len(set(ids))
    assert set(EXPECTED) <= set(ids)
    for preset_id, (assessment, enforcement, compliance) in EXPECTED.items():
        result = evaluate_preset(bundle, preset_id)
        assert result.behavior_assessment == assessment, preset_id
        assert result.enforcement_response == enforcement, preset_id
        assert result.execution == "not_performed", preset_id
        if compliance is not None:
            assert result.instruction_compliance is compliance, preset_id
        assert bundle.presets[preset_id].request.preset_id == preset_id


def test_containment_successful_effective():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "containment_successful")
    assert result.behavior_assessment == BehaviorAssessment.non_compliant
    assert result.enforcement_response == EnforcementResponse.isolate
    assert result.containment_effective is True
    assert result.execution == "not_performed"


def test_api_presets_and_evaluate(client):
    presets = client.get("/api/labs/006/presets")
    assert presets.status_code == 200
    body = presets.json()
    assert len(body) >= 8
    ids = {item["id"] for item in body}
    assert "justified_policy_refusal" in ids

    detail = client.get("/api/labs/006/presets/justified_policy_refusal")
    assert detail.status_code == 200
    assert detail.json()["request"]["agent_refused_request"] is True

    response = client.post(
        "/api/labs/006/evaluate",
        json=detail.json()["request"],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["behavior_assessment"] == "JUSTIFIED_REFUSAL"
    assert payload["enforcement_response"] == "CONTINUE"
    assert payload["execution"] == "not_performed"


def test_api_evaluate_preset_all(client):
    for preset_id in EXPECTED:
        response = client.post(f"/api/labs/006/evaluate-preset/{preset_id}")
        assert response.status_code == 200, preset_id
        assert response.json()["execution"] == "not_performed", preset_id


def test_api_invalid_enum(client):
    payload = _base().model_dump(mode="json")
    payload["credential_state"] = "not-a-state"
    response = client.post("/api/labs/006/evaluate", json=payload)
    assert response.status_code == 422


def test_api_missing_required(client):
    response = client.post("/api/labs/006/evaluate", json={})
    assert response.status_code == 422


def test_api_unknown_preset(client):
    response = client.get("/api/labs/006/presets/does_not_exist")
    assert response.status_code == 404
    assert response.json()["detail"]["execution"] == "not_performed"
