from fastapi.testclient import TestClient

from from_my_desk.main import app


client = TestClient(app)


def payload(**overrides):
    body = {
        "principal_id": "principal-demo-001",
        "agent_id": "kya-agent-001",
        "action": "propose_paper_order",
        "order": {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": 100,
            "limit_price": "40.00",
            "account_id": "paper-desk-alpha",
        },
        "authorization_context": {"customer_confirmed": False, "mfa_verified": False},
    }
    body.update(overrides)
    if "order" in overrides:
        order = {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": 100,
            "limit_price": "40.00",
            "account_id": "paper-desk-alpha",
        }
        order.update(overrides["order"])
        body["order"] = order
    return body


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_sanitized_registry_hides_authority_fields():
    response = client.get("/registry")
    assert response.status_code == 200
    data = response.json()
    blob = str(data)
    assert "valid_until" not in blob
    assert "principal_id" not in blob
    assert "revoked:" not in blob
    assert "'revoked'" not in blob
    assert data["policy_id"] == "cedar-quill-desk-v2"


def test_evaluate_allow_and_all_decisions():
    allow = client.post("/api/evaluate", json=payload())
    assert allow.status_code == 200
    assert allow.json()["decision"] == "allow"
    assert allow.json()["audit_id"]
    assert allow.json()["notional"] == "4000.00"

    confirm = client.post(
        "/evaluate",
        json=payload(order={"quantity": 200, "limit_price": "40.00"}),
    )
    assert confirm.json()["decision"] == "confirm"
    assert confirm.json()["required_action"] == "customer_confirmation"

    step = client.post(
        "/api/evaluate",
        json=payload(order={"quantity": 300, "limit_price": "40.00"}),
    )
    assert step.json()["decision"] == "step_up"

    deny = client.post(
        "/api/evaluate",
        json=payload(order={"quantity": 450, "limit_price": "40.00"}),
    )
    assert deny.json()["decision"] == "deny"
    assert deny.json()["reason_code"] == "amount_exceeds_limit"


def test_invalid_bodies():
    missing = client.post("/api/evaluate", json={"agent_id": "x"})
    assert missing.status_code == 422
    assert missing.json()["reason_code"] == "invalid_request"
    assert "traceback" not in str(missing.json()).lower()

    bad_side = client.post(
        "/api/evaluate",
        json=payload(order={"side": "hold"}),
    )
    assert bad_side.status_code == 422

    bad_qty = client.post(
        "/api/evaluate",
        json=payload(order={"quantity": 0}),
    )
    assert bad_qty.status_code == 422

    bad_price = client.post(
        "/api/evaluate",
        json=payload(order={"limit_price": "0"}),
    )
    assert bad_price.status_code == 422


def test_decimal_boundary_via_api():
    response = client.post(
        "/api/evaluate",
        json=payload(order={"quantity": 1, "limit_price": "5000.00"}),
    )
    assert response.json()["decision"] == "allow"
    over = client.post(
        "/api/evaluate",
        json=payload(order={"quantity": 1, "limit_price": "5000.01"}),
    )
    assert over.json()["decision"] == "confirm"
