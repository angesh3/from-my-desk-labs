"""Lab 004 decision and API tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_escalation_boundary.gateway import get_lab004_bundle, reset_lab004_bundle, router
from agent_escalation_boundary.loader import load_bundle
from agent_escalation_boundary.models import (
    AuthorizationOutcome,
    EvidenceConfidence,
    EvaluateRequest,
    ExecutionOutcome,
    GoalClarity,
    HumanAvailability,
    PolicyCoverage,
    PotentialImpact,
    Reversibility,
    TimeSensitivity,
)
from agent_escalation_boundary.policy import evaluate
from agent_escalation_boundary.service import evaluate_preset, list_presets

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples"
POLICY = ROOT / "policies"


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setenv("LAB004_DATA_DIR", str(DATA))
    monkeypatch.setenv("LAB004_POLICY_DIR", str(POLICY))
    reset_lab004_bundle()
    yield
    reset_lab004_bundle()


def _base(**overrides) -> EvaluateRequest:
    payload = {
        "goal_clarity": GoalClarity.clear,
        "evidence_confidence": EvidenceConfidence.high,
        "potential_impact": PotentialImpact.moderate,
        "reversibility": Reversibility.easily_reversible,
        "policy_coverage": PolicyCoverage.explicitly_covered,
        "time_sensitivity": TimeSensitivity.moderate,
        "human_availability": HumanAvailability.available_shortly,
        "authorization_outcome": AuthorizationOutcome.allow,
        "agent_id": "cq-soc-response-agent-01",
        "principal_id": "cq-soc-lead-morgan",
        "requested_action": "revoke_suspicious_session",
        "target_account": "alex.rivera@cedarquill.example",
        "delegated_capability": "revoke_sessions",
        "business_context": "Fictional Cedar Quill Markets investigation.",
    }
    payload.update(overrides)
    return EvaluateRequest(**payload)


def test_case_a_proceed():
    result = evaluate(_base())
    assert result.execution_outcome == ExecutionOutcome.proceed
    assert result.execution == "not_performed"


def test_case_b_clarify_ambiguous():
    result = evaluate(_base(goal_clarity=GoalClarity.ambiguous))
    assert result.execution_outcome == ExecutionOutcome.clarify


def test_case_c_escalate_conflicting_critical():
    result = evaluate(
        _base(
            evidence_confidence=EvidenceConfidence.conflicting,
            potential_impact=PotentialImpact.critical,
            reversibility=Reversibility.difficult_to_reverse,
            policy_coverage=PolicyCoverage.partially_covered,
            requested_action="temporarily_suspend_access",
            delegated_capability="temporarily_suspend_access",
        )
    )
    assert result.execution_outcome == ExecutionOutcome.escalate


def test_case_d_deny_stops():
    result = evaluate(_base(authorization_outcome=AuthorizationOutcome.deny))
    assert result.execution_outcome == ExecutionOutcome.stop


def test_case_e_prohibited_stops():
    result = evaluate(_base(policy_coverage=PolicyCoverage.prohibited))
    assert result.execution_outcome == ExecutionOutcome.stop


def test_case_f_step_up_without_auth_escalates():
    result = evaluate(
        _base(
            authorization_outcome=AuthorizationOutcome.step_up,
            stronger_auth_completed=False,
        )
    )
    assert result.execution_outcome == ExecutionOutcome.escalate


def test_case_g_immediate_threat_bounded():
    result = evaluate(
        _base(
            evidence_confidence=EvidenceConfidence.conflicting,
            potential_impact=PotentialImpact.high,
            time_sensitivity=TimeSensitivity.immediate_threat,
            human_availability=HumanAvailability.delayed,
        )
    )
    assert result.execution_outcome == ExecutionOutcome.escalate
    assert result.bounded_protective_action.available is True
    assert result.bounded_protective_action.expands_authority is False
    assert any("session" in a.lower() for a in result.bounded_protective_action.actions)


def test_capability_mismatch_stops():
    result = evaluate(
        _base(
            requested_action="permanently_delete_account",
            delegated_capability="revoke_sessions",
            policy_coverage=PolicyCoverage.explicitly_covered,
        )
    )
    assert result.execution_outcome == ExecutionOutcome.stop


def test_precedence_stop_over_escalate():
    result = evaluate(
        _base(
            authorization_outcome=AuthorizationOutcome.deny,
            evidence_confidence=EvidenceConfidence.conflicting,
            potential_impact=PotentialImpact.critical,
        )
    )
    assert result.execution_outcome == ExecutionOutcome.stop


def test_invalid_identity_stops():
    result = evaluate(_base(agent_id="unknown"))
    assert result.execution_outcome == ExecutionOutcome.stop


def test_all_presets_match_expected():
    bundle = load_bundle(DATA, POLICY)
    for meta in list_presets(bundle):
        result = evaluate_preset(bundle, meta.id)
        assert result.execution_outcome == meta.expected_execution_outcome
        assert result.execution == "not_performed"
        assert result.decision_id
        assert result.triggered_rules
        assert result.recommended_next_step


def test_explanation_fields_present():
    result = evaluate(_base())
    assert result.authorization_outcome == AuthorizationOutcome.allow
    assert result.evidence_assessment
    assert result.why_paused_or_proceeded
    assert result.impact_of_acting
    assert result.impact_of_waiting
    assert result.authority_chain_summary
    assert result.policy_version


def test_api_presets_and_evaluate():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    presets = client.get("/api/labs/004/presets")
    assert presets.status_code == 200
    assert len(presets.json()) >= 5
    detail = client.get("/api/labs/004/presets/clear_session_revoke")
    assert detail.status_code == 200
    body = detail.json()["request"]
    evaluated = client.post("/api/labs/004/evaluate", json=body)
    assert evaluated.status_code == 200
    assert evaluated.json()["execution_outcome"] == "proceed"
    assert evaluated.json()["execution"] == "not_performed"
    named = client.post("/api/labs/004/evaluate-preset/immediate_threat_bounded")
    assert named.status_code == 200
    assert named.json()["execution_outcome"] == "escalate"
    assert named.json()["bounded_protective_action"]["available"] is True


def test_api_unknown_preset_404():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/labs/004/presets/does-not-exist")
    assert response.status_code == 404


def test_api_invalid_enum_422():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    payload = _base().model_dump()
    payload["goal_clarity"] = "not-a-value"
    response = client.post("/api/labs/004/evaluate", json=payload)
    assert response.status_code == 422
