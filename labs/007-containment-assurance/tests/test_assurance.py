"""Unit and API tests for Lab 007 containment assurance."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from containment_assurance.gateway import (
    get_lab007_bundle,
    reset_lab007_bundle,
    router,
)
from containment_assurance.loader import load_bundle
from containment_assurance.models import (
    AssuranceCheck,
    AssuranceStatus,
    AttemptedEnforcement,
    EvaluateRequest,
    EvidenceFreshness,
    EvidenceSource,
    REQUIRED_CHECK_IDS,
)
from containment_assurance.policy import evaluate
from containment_assurance.service import evaluate_preset, list_presets

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples"
POLICY = ROOT / "policies"

EXPECTED = {
    "complete_containment": AssuranceStatus.confirmed,
    "runtime_stopped_token_active": AssuranceStatus.partial,
    "delegate_still_running": AssuranceStatus.failed,
    "queued_action_survives": AssuranceStatus.partial,
    "alternate_network_path_open": AssuranceStatus.partial,
    "restart_resumes_work": AssuranceStatus.failed,
    "insufficient_telemetry": AssuranceStatus.unverified,
    "containment_regression": AssuranceStatus.failed,
}


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setenv("LAB007_DATA_DIR", str(DATA))
    monkeypatch.setenv("LAB007_POLICY_DIR", str(POLICY))
    reset_lab007_bundle()
    yield
    reset_lab007_bundle()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    get_lab007_bundle()
    return TestClient(app)


def _good_checks(**overrides):
    checks = []
    expected_map = {
        "primary_runtime_stopped": "stopped",
        "active_sessions_revoked": "revoked",
        "delegated_credentials_revoked": "revoked",
        "tool_access_disabled": "disabled",
        "queued_actions_cancelled": "cancelled",
        "scheduled_work_cancelled": "cancelled",
        "child_agents_stopped": "stopped",
        "network_egress_blocked": "blocked",
        "alternate_network_paths_checked": "blocked",
        "persistent_state_quarantined": "quarantined",
        "restart_recovery_disabled": "disabled",
        "telemetry_coverage_complete": "complete",
        "evidence_freshness_acceptable": "fresh",
        "evidence_source_independence": "independent",
        "post_containment_activity_absent": "absent",
    }
    for cid in REQUIRED_CHECK_IDS:
        o = overrides.get(cid, {})
        checks.append(
            AssuranceCheck(
                check_id=cid,
                expected_state=expected_map[cid],
                observed_state=o.get("observed_state", expected_map[cid]),
                evidence_reference=o.get("evidence_reference", f"evid-{cid}"),
                evidence_freshness=o.get(
                    "evidence_freshness", EvidenceFreshness.fresh
                ),
                evidence_source=o.get(
                    "evidence_source", EvidenceSource.independent_control_plane
                ),
            )
        )
    return checks


def _base(**overrides) -> EvaluateRequest:
    payload = {
        "request_id": "req-test-007",
        "correlation_id": "corr-test-007",
        "agent_id": "cq-soc-response-agent-01",
        "principal_id": "cq-ir-commander-ava",
        "attempted_enforcement": AttemptedEnforcement.terminate,
        "evaluated_at": "2026-10-10T18:00:00Z",
        "evidence_window_minutes": 15,
        "checks": _good_checks(),
    }
    payload.update(overrides)
    return EvaluateRequest(**payload)


def test_complete_containment_confirmed():
    result = evaluate(_base())
    assert result.assurance_status == AssuranceStatus.confirmed
    assert result.containment_effective is True
    assert result.residual_paths == []
    assert result.execution == "not_performed"


def test_token_residual_partial():
    result = evaluate(
        _base(
            checks=_good_checks(
                delegated_credentials_revoked={"observed_state": "cached_valid"}
            )
        )
    )
    assert result.assurance_status == AssuranceStatus.partial
    assert any("credential" in p.lower() for p in result.residual_paths)


def test_delegate_continued_failed():
    result = evaluate(
        _base(
            checks=_good_checks(
                child_agents_stopped={"observed_state": "running"},
                post_containment_activity_absent={"observed_state": "detected"},
            ),
            post_containment_activity=["child still running"],
        )
    )
    assert result.assurance_status == AssuranceStatus.failed


def test_queued_action_partial_not_failed():
    """Executable queue without observed continuation is PARTIAL by design."""
    result = evaluate(
        _base(
            checks=_good_checks(
                queued_actions_cancelled={"observed_state": "executable"}
            )
        )
    )
    assert result.assurance_status == AssuranceStatus.partial
    assert any("queue" in p.lower() for p in result.residual_paths)


def test_insufficient_telemetry_unverified():
    checks = [
        AssuranceCheck(
            check_id=cid,
            expected_state="required",
            observed_state="unknown",
            evidence_reference=None,
            evidence_freshness=EvidenceFreshness.unknown,
            evidence_source=EvidenceSource.none,
        )
        for cid in REQUIRED_CHECK_IDS
    ]
    result = evaluate(_base(checks=checks, agent_self_report_stopped=True))
    assert result.assurance_status == AssuranceStatus.unverified
    assert result.missing_evidence


def test_continued_overrides_missing_telemetry():
    checks = [
        AssuranceCheck(
            check_id=cid,
            expected_state="required",
            observed_state="unknown",
            evidence_reference=None,
            evidence_freshness=EvidenceFreshness.unknown,
            evidence_source=EvidenceSource.none,
        )
        for cid in REQUIRED_CHECK_IDS
    ]
    result = evaluate(
        _base(checks=checks, post_containment_activity=["still working"])
    )
    assert result.assurance_status == AssuranceStatus.failed


def test_containment_regression_failed():
    result = evaluate(
        _base(
            containment_regression_detected=True,
            post_containment_activity=["boundary restored"],
            checks=_good_checks(
                primary_runtime_stopped={"observed_state": "running"},
                delegated_credentials_revoked={"observed_state": "valid"},
            ),
        )
    )
    assert result.assurance_status == AssuranceStatus.failed
    assert result.containment_effective is False


def test_agent_self_report_not_sufficient():
    checks = _good_checks()
    for c in checks:
        if c.check_id == "primary_runtime_stopped":
            c.evidence_source = EvidenceSource.agent_self_report
    result = evaluate(_base(checks=checks, agent_self_report_stopped=True))
    assert result.assurance_status != AssuranceStatus.confirmed


def test_precedence_failed_over_partial():
    result = evaluate(
        _base(
            checks=_good_checks(
                delegated_credentials_revoked={"observed_state": "cached_valid"},
                child_agents_stopped={"observed_state": "running"},
            ),
            post_containment_activity=["delegate active"],
        )
    )
    assert result.assurance_status == AssuranceStatus.failed


def test_presets_match_documented_outcomes():
    bundle = load_bundle(DATA, POLICY)
    metas = list_presets(bundle)
    ids = [m.id for m in metas]
    assert len(ids) == len(set(ids))
    assert set(EXPECTED) <= set(ids)
    for preset_id, status in EXPECTED.items():
        result = evaluate_preset(bundle, preset_id)
        assert result.assurance_status == status, preset_id
        assert result.execution == "not_performed", preset_id
        assert result.attempted_enforcement in {
            AttemptedEnforcement.restrict,
            AttemptedEnforcement.isolate,
            AttemptedEnforcement.terminate,
        }


def test_api_presets_and_evaluate(client):
    presets = client.get("/api/labs/007/presets")
    assert presets.status_code == 200
    assert len(presets.json()) >= 8
    detail = client.get("/api/labs/007/presets/complete_containment")
    assert detail.status_code == 200
    response = client.post("/api/labs/007/evaluate", json=detail.json()["request"])
    assert response.status_code == 200
    body = response.json()
    assert body["assurance_status"] == "CONFIRMED"
    assert body["execution"] == "not_performed"


def test_api_evaluate_preset_all(client):
    for preset_id in EXPECTED:
        response = client.post(f"/api/labs/007/evaluate-preset/{preset_id}")
        assert response.status_code == 200, preset_id
        body = response.json()
        assert body["execution"] == "not_performed"
        assert body["assurance_status"] == EXPECTED[preset_id].value


def test_api_invalid_enum(client):
    payload = _base().model_dump(mode="json")
    payload["attempted_enforcement"] = "STOP_HARD"
    response = client.post("/api/labs/007/evaluate", json=payload)
    assert response.status_code == 422


def test_api_malformed_checks(client):
    payload = _base().model_dump(mode="json")
    payload["checks"] = []
    response = client.post("/api/labs/007/evaluate", json=payload)
    assert response.status_code == 422


def test_api_duplicate_check_ids(client):
    payload = _base().model_dump(mode="json")
    payload["checks"] = payload["checks"] + [payload["checks"][0]]
    response = client.post("/api/labs/007/evaluate", json=payload)
    assert response.status_code == 422


def test_api_unknown_preset(client):
    response = client.get("/api/labs/007/presets/does_not_exist")
    assert response.status_code == 404
    assert response.json()["detail"]["execution"] == "not_performed"
