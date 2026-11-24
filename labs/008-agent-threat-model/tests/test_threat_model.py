"""Unit and API tests for Lab 008 agent threat model."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_threat_model.gateway import (
    get_lab008_bundle,
    reset_lab008_bundle,
    router,
)
from agent_threat_model.loader import load_bundle
from agent_threat_model.models import (
    ControlCategory,
    ControlCoverage,
    ControlItem,
    ControlStatus,
    CrossCuttingDimension,
    EvaluateRequest,
    Impact,
    Likelihood,
    RiskLevel,
    ThreatSurface,
)
from agent_threat_model.risk import classify_risk
from agent_threat_model.service import evaluate_preset, list_presets
from agent_threat_model.threat_case import evaluate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples"
POLICY = ROOT / "policies"

EXPECTED = {
    "retrieved_prompt_injection_blocked": {
        "primary": ThreatSurface.instructions,
        "secondary": [],
        "dimensions": [],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.complete,
        "residual": RiskLevel.low,
    },
    "excessive_delegated_authority": {
        "primary": ThreatSurface.authority,
        "secondary": [ThreatSurface.delegation],
        "dimensions": [],
        "initial": RiskLevel.critical,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "approval_replay_blocked": {
        "primary": ThreatSurface.authority,
        "secondary": [ThreatSurface.identity, ThreatSurface.evidence_control],
        "dimensions": [],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.complete,
        "residual": RiskLevel.low,
    },
    "poisoned_persistent_memory": {
        "primary": ThreatSurface.memory_context,
        "secondary": [ThreatSurface.instructions],
        "dimensions": [],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.none,
        "residual": RiskLevel.high,
    },
    "allowed_tool_data_exposure": {
        "primary": ThreatSurface.tools_execution,
        "secondary": [ThreatSurface.authority, ThreatSurface.memory_context],
        "dimensions": [],
        "initial": RiskLevel.critical,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "alternate_tool_after_denial": {
        "primary": ThreatSurface.tools_execution,
        "secondary": [ThreatSurface.authority, ThreatSurface.evidence_control],
        "dimensions": [],
        "initial": RiskLevel.critical,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "queued_action_after_authority_expiry": {
        "primary": ThreatSurface.authority,
        "secondary": [ThreatSurface.tools_execution, ThreatSurface.evidence_control],
        "dimensions": [],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.none,
        "residual": RiskLevel.high,
    },
    "insufficient_cross_system_telemetry": {
        "primary": ThreatSurface.evidence_control,
        "secondary": [],
        "dimensions": [],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.unverified,
        "residual": RiskLevel.unknown,
    },
    "usage_drift_after_approval": {
        "primary": ThreatSurface.instructions,
        "secondary": [],
        "dimensions": [CrossCuttingDimension.behavior_usage_drift],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "public_model_sensitive_context_exposure": {
        "primary": ThreatSurface.tools_execution,
        "secondary": [ThreatSurface.memory_context, ThreatSurface.evidence_control],
        "dimensions": [CrossCuttingDimension.external_model_exposure],
        "initial": RiskLevel.critical,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "learning_changes_future_behavior": {
        "primary": ThreatSurface.memory_context,
        "secondary": [ThreatSurface.instructions],
        "dimensions": [CrossCuttingDimension.learning_memory_drift],
        "initial": RiskLevel.high,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
    "agent_resource_and_network_expansion": {
        "primary": ThreatSurface.tools_execution,
        "secondary": [
            ThreatSurface.authority,
            ThreatSurface.delegation,
            ThreatSurface.evidence_control,
        ],
        "dimensions": [CrossCuttingDimension.network_resource_impact],
        "initial": RiskLevel.critical,
        "coverage": ControlCoverage.partial,
        "residual": RiskLevel.high,
    },
}

PRESET_IDS = list(EXPECTED.keys())


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setenv("LAB008_DATA_DIR", str(DATA))
    monkeypatch.setenv("LAB008_POLICY_DIR", str(POLICY))
    reset_lab008_bundle()
    yield
    reset_lab008_bundle()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    get_lab008_bundle()
    return TestClient(app)


def _ctrl(
    control_id: str,
    *,
    category: ControlCategory = ControlCategory.preventive,
    status: ControlStatus = ControlStatus.present,
) -> ControlItem:
    return ControlItem(
        control_id=control_id,
        name=control_id.replace("_", " ").title(),
        category=category,
        expected_behavior=f"Expected behavior for {control_id}",
        evidence_reference=f"evid-{control_id}",
        status=status,
    )


def _base(**overrides) -> EvaluateRequest:
    payload = {
        "case_id": "case-test-008",
        "title": "Test case",
        "description": "Fictional threat-case for unit tests.",
        "agent_identity": "cq-test-agent",
        "principal_identity": "cq-test-principal",
        "environment": "Cedar Quill Markets fictional lab",
        "policy_version": "lab008-threat-model-v1",
        "asset_name": "Test asset",
        "asset_type": "test",
        "asset_sensitivity": "high",
        "security_objective": "Protect the fictional asset",
        "threat_source": "Test threat source",
        "failure_mode": "Test failure mode",
        "primary_surface": ThreatSurface.instructions,
        "secondary_surfaces": [],
        "cross_cutting_dimensions": [],
        "trust_boundary": "Test trust boundary",
        "preconditions": ["precondition"],
        "threat_path": ["step-1"],
        "potential_impact": "Test impact",
        "initial_likelihood": Likelihood.medium,
        "initial_impact": Impact.high,
        "preventive_controls": [_ctrl("preventive_ok")],
        "detective_controls": [
            _ctrl("detective_ok", category=ControlCategory.detective)
        ],
        "containment_controls": [
            _ctrl("containment_ok", category=ControlCategory.containment)
        ],
        "recovery_controls": [
            _ctrl("recovery_ok", category=ControlCategory.recovery)
        ],
        "evidence_sources": ["runtime_log"],
        "evidence_summary": "Independent evidence available.",
        "evidence_gaps": [],
        "observation_window": "15m",
        "agent_self_report_present": False,
        "independent_evidence_sufficient": True,
    }
    payload.update(overrides)
    return EvaluateRequest(**payload)


@pytest.mark.parametrize("preset_id", PRESET_IDS)
def test_all_twelve_presets(preset_id):
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, preset_id)
    expected = EXPECTED[preset_id]
    assert result.primary_surface == expected["primary"]
    assert list(result.secondary_surfaces) == expected["secondary"]
    assert list(result.cross_cutting_dimensions) == expected["dimensions"]
    assert result.initial_risk == expected["initial"]
    assert result.control_coverage == expected["coverage"]
    assert result.residual_risk == expected["residual"]
    assert result.execution == "not_performed"
    assert "execution.not_performed" in result.reason_codes
    assert result.organizational_exposure is not None
    assert result.recommended_controls
    assert result.recommended_evidence


def test_risk_matrix_deterministic():
    assert classify_risk(Likelihood.low, Impact.critical) == RiskLevel.high
    assert classify_risk(Likelihood.high, Impact.high) == RiskLevel.critical
    assert classify_risk(Likelihood.medium, Impact.high) == RiskLevel.high


def test_execution_always_not_performed():
    result = evaluate(_base())
    assert result.execution == "not_performed"


def test_agent_self_report_not_independent():
    result = evaluate(
        _base(
            evidence_sources=["agent_self_report"],
            agent_self_report_present=True,
            independent_evidence_sufficient=True,
            preventive_controls=[_ctrl("p1")],
            detective_controls=[],
            containment_controls=[],
            recovery_controls=[],
        )
    )
    assert result.control_coverage == ControlCoverage.unverified
    assert result.residual_risk == RiskLevel.unknown
    assert "evidence.self_report_not_independent" in result.reason_codes


def test_missing_evidence_unverified():
    result = evaluate(
        _base(
            independent_evidence_sufficient=False,
            evidence_gaps=["Missing credential telemetry"],
            evidence_sources=["runtime_log_excerpt"],
        )
    )
    assert result.control_coverage == ControlCoverage.unverified
    assert result.residual_risk == RiskLevel.unknown
    assert "assessment.unverified" in result.reason_codes


def test_complete_coverage_not_zero_risk():
    result = evaluate(
        _base(
            residual_likelihood=Likelihood.low,
            residual_impact=Impact.medium,
        )
    )
    assert result.control_coverage == ControlCoverage.complete
    assert result.residual_risk == RiskLevel.low
    assert "does not mean zero risk" in result.residual_risk_explanation.lower()
    assert any("zero risk" in item.lower() for item in result.limitations)


def test_tool_auth_distinct_from_data_purpose():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "allowed_tool_data_exposure")
    assert result.primary_surface == ThreatSurface.tools_execution
    assert ThreatSurface.authority in result.secondary_surfaces
    assert any(
        "data_purpose" in g or "purpose" in g.lower() for g in result.material_gaps
    )
    assert result.control_coverage == ControlCoverage.partial


def test_delegated_authority_narrowing():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "excessive_delegated_authority")
    assert result.primary_surface == ThreatSurface.authority
    assert ThreatSurface.delegation in result.secondary_surfaces
    assert any("narrow" in a.lower() for a in result.recommended_actions)
    assert any("authority_narrowing" in g for g in result.material_gaps)


def test_approval_binding():
    bundle = load_bundle(DATA, POLICY)
    detail = bundle.presets["approval_replay_blocked"]
    names = [c.name.lower() for c in detail.request.preventive_controls]
    assert any("binding" in n for n in names)
    result = evaluate_preset(bundle, "approval_replay_blocked")
    assert result.control_coverage == ControlCoverage.complete


def test_execution_time_reevaluation_for_queued_work():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "queued_action_after_authority_expiry")
    assert result.control_coverage == ControlCoverage.none
    assert any("execution_time_reevaluation" in g for g in result.material_gaps)


def test_usage_drift_dimension():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "usage_drift_after_approval")
    assert CrossCuttingDimension.behavior_usage_drift in result.cross_cutting_dimensions
    assert "dimension.behavior_usage_drift" in result.reason_codes
    assert any("purpose" in c.lower() for c in result.recommended_controls)


def test_public_model_exposure_dimension():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "public_model_sensitive_context_exposure")
    assert (
        CrossCuttingDimension.external_model_exposure
        in result.cross_cutting_dimensions
    )
    assert result.organizational_exposure.public_model_transmission.value in {
        "HIGH",
        "CRITICAL",
    }


def test_learning_memory_drift_dimension():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "learning_changes_future_behavior")
    assert (
        CrossCuttingDimension.learning_memory_drift in result.cross_cutting_dimensions
    )
    assert any("learning" in c.lower() or "memory" in c.lower() for c in result.recommended_controls)


def test_network_resource_impact_dimension():
    bundle = load_bundle(DATA, POLICY)
    result = evaluate_preset(bundle, "agent_resource_and_network_expansion")
    assert (
        CrossCuttingDimension.network_resource_impact
        in result.cross_cutting_dimensions
    )
    assert result.organizational_exposure.credential_reach.value in {"HIGH", "CRITICAL"}
    assert result.organizational_exposure.compute_token_cost.value in {
        "HIGH",
        "CRITICAL",
    }


def test_list_presets_twelve():
    bundle = load_bundle(DATA, POLICY)
    metas = list_presets(bundle)
    assert len(metas) == 12
    assert {m.id for m in metas} == set(PRESET_IDS)


def test_api_presets_and_evaluate(client):
    listed = client.get("/api/labs/008/presets").json()
    assert len(listed) == 12
    for preset_id in PRESET_IDS:
        response = client.post(f"/api/labs/008/evaluate-preset/{preset_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["execution"] == "not_performed"
        assert body["control_coverage"] == EXPECTED[preset_id]["coverage"].value
        assert body["residual_risk"] == EXPECTED[preset_id]["residual"].value
        assert body["initial_risk"] == EXPECTED[preset_id]["initial"].value
        assert "cross_cutting_dimensions" in body
        assert "organizational_exposure" in body


def test_api_evaluate_custom(client):
    payload = _base(
        cross_cutting_dimensions=[CrossCuttingDimension.behavior_usage_drift]
    ).model_dump(mode="json")
    response = client.post("/api/labs/008/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["execution"] == "not_performed"
    assert body["cross_cutting_dimensions"] == ["BEHAVIOR_USAGE_DRIFT"]


def test_ui_labels_constants_in_static():
    lab_js = (ROOT / "static" / "lab.js").read_text(encoding="utf-8")
    assert "IDENTITY" in lab_js
    assert "Identity" in lab_js
    assert "BEHAVIOR_USAGE_DRIFT" in lab_js
    assert "Behavior and usage drift" in lab_js
    assert "EXTERNAL_MODEL_EXPOSURE" in lab_js
    assert "NETWORK_RESOURCE_IMPACT" in lab_js
    assert "organizational_exposure" in lab_js
    assert "not_performed" in lab_js


def test_architecture_and_data_flow_svgs_utf8():
    for name in (
        "agent-threat-model.svg",
        "agent-system-architecture.svg",
        "agent-data-flow.svg",
    ):
        path = ROOT / "static" / name
        data = path.read_bytes()
        data.decode("utf-8")
        assert b"<svg" in data
        assert b"<title" in data
        assert b"<desc" in data
