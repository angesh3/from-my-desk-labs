"""Lab 002 API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

EXPECTED = {
    "valid_narrow_delegation": "allow",
    "confirmation_required": "confirm",
    "stale_posture": "step_up",
    "unusual_context": "confirm",
    "execution_not_delegated": "deny",
    "child_capability_exceeds_parent": "deny",
    "child_limit_exceeds_parent": "deny",
    "child_expiry_exceeds_parent": "deny",
    "delegation_depth_exceeded": "deny",
    "parent_expired": "deny",
    "parent_revoked": "deny",
    "unknown_agent": "deny",
    "profile_mismatch": "step_up",
    "noncompliant_model_version": "step_up",
    "tool_inventory_changed": "deny",
}


def test_scenarios_endpoint():
    response = client.get("/api/labs/002/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 15
    assert {item["id"] for item in body} == set(EXPECTED)
    for item in body:
        assert "request" not in item
        assert set(item.keys()) >= {"id", "title", "short_description", "category", "expected_decision"}


def test_evaluate_all_scenarios():
    for scenario_id, decision in EXPECTED.items():
        response = client.post(
            "/api/labs/002/evaluate",
            json={"scenario_id": scenario_id},
        )
        assert response.status_code == 200, scenario_id
        body = response.json()
        assert body["decision"] == decision
        assert body["execution"] == "not_performed"
        assert body["audit_id"]
        assert "fallback" in body
        assert "traceback" not in response.text.lower()


def test_unknown_scenario_safe_404():
    response = client.post("/api/labs/002/evaluate", json={"scenario_id": "not_a_real_scenario"})
    assert response.status_code == 404
    assert "traceback" not in response.text.lower()


def test_invalid_json_safe_422():
    response = client.post(
        "/api/labs/002/evaluate",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "traceback" not in response.text.lower()
