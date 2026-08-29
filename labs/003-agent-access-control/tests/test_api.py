"""Lab 003 API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

EXPECTED = {
    "managed_public_data_read": "allow",
    "sensitive_action_consent": "confirm",
    "stale_runtime_attestation": "step_up",
    "unapproved_model": "step_up",
    "undelegated_capability": "deny",
    "unknown_agent_protected_tool": "deny",
    "unknown_agent_registration": "allow",
    "undeclared_tool": "deny",
    "data_boundary_violation": "deny",
    "parent_delegation_expired": "deny",
    "parent_delegation_revoked": "deny",
    "purpose_conflict": "deny",
    "limit_requires_confirmation": "confirm",
    "material_context_change": "step_up",
}


def test_scenarios_endpoint():
    response = client.get("/api/labs/003/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 14
    assert {item["id"] for item in body} == set(EXPECTED)
    for item in body:
        assert "request" not in item
        assert set(item.keys()) >= {
            "id",
            "title",
            "short_description",
            "category",
            "expected_decision",
        }


def test_evaluate_all_scenarios():
    for scenario_id, decision in EXPECTED.items():
        response = client.post(
            "/api/labs/003/evaluate",
            json={"scenario_id": scenario_id},
        )
        assert response.status_code == 200, scenario_id
        body = response.json()
        assert body["decision"] == decision
        assert body["execution"] == "not_performed"
        assert body["audit_id"]
        assert "restricted" in body
        assert "events" in body
        assert len(body["events"]) >= 14
        assert "traceback" not in response.text.lower()


def test_unknown_scenario_safe_404():
    response = client.post(
        "/api/labs/003/evaluate",
        json={"scenario_id": "not_a_real_scenario"},
    )
    assert response.status_code == 404
    assert "traceback" not in response.text.lower()


def test_invalid_json_safe_422():
    response = client.post(
        "/api/labs/003/evaluate",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "traceback" not in response.text.lower()


def test_canonical_result_is_deterministic_for_guided_and_instant_modes():
    """Guided and Instant modes replay the same server event list; API must be stable."""
    for scenario_id in EXPECTED:
        first = client.post(
            "/api/labs/003/evaluate",
            json={"scenario_id": scenario_id},
        ).json()
        second = client.post(
            "/api/labs/003/evaluate",
            json={"scenario_id": scenario_id},
        ).json()
        assert first["decision"] == second["decision"]
        assert first["reason_code"] == second["reason_code"]
        assert first["audit_id"] != second["audit_id"]
        assert [event["event_type"] for event in first["events"]] == [
            event["event_type"] for event in second["events"]
        ]
        assert [event["status"] for event in first["events"]] == [
            event["status"] for event in second["events"]
        ]
