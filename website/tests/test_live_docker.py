"""Optional live checks against a running production container."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pytest

BASE = os.environ.get("FROM_MY_DESK_BASE_URL", "").rstrip("/")

pytestmark = pytest.mark.skipif(
    not BASE,
    reason="Set FROM_MY_DESK_BASE_URL to exercise a running Docker/production service.",
)


def _get(path: str):
    request = urllib.request.Request(BASE + path, method="GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.getcode(), response.headers, response.read()


def _post_json(path: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.getcode(), json.loads(response.read().decode("utf-8"))


def _eval_payload(quantity: int, limit_price: str, confirmed: bool = False, mfa: bool = False):
    return {
        "principal_id": "principal-demo-001",
        "agent_id": "kya-agent-001",
        "action": "propose_paper_order",
        "order": {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": quantity,
            "limit_price": limit_price,
            "account_id": "paper-desk-alpha",
        },
        "authorization_context": {
            "customer_confirmed": confirmed,
            "mfa_verified": mfa,
        },
    }


def test_live_pages_and_assets():
    for path, needle in (
        ("/", b"Perspectives shaped by experience"),
        ("/labs", b"Labs"),
        ("/labs/know-your-agent", b"Know Your Agent"),
    ):
        code, headers, body = _get(path)
        assert code == 200
        assert needle in body
        assert "text/html" in headers.get("Content-Type", "")

    code, headers, body = _get("/static/css/styles.css")
    assert code == 200
    assert "text/css" in headers.get("Content-Type", "")
    assert b"--navy:" in body

    code, headers, body = _get("/static/js/site.js")
    assert code == 200
    assert "javascript" in headers.get("Content-Type", "")

    code, headers, _ = _get("/static/brand/from-my-desk-logo.webp")
    assert code == 200
    assert "image/webp" in headers.get("Content-Type", "")

    code, headers, _ = _get("/static/brand/favicon.png")
    assert code == 200
    assert "image/png" in headers.get("Content-Type", "")

    code, headers, _ = _get("/static/labs/001/architecture.svg")
    assert code == 200
    assert "image/svg+xml" in headers.get("Content-Type", "")

    code, headers, _ = _get("/static/labs/001/know-your-agent-trust-workflow.gif")
    assert code == 200
    assert "image/gif" in headers.get("Content-Type", "")

    with pytest.raises(urllib.error.HTTPError) as exc:
        _get("/static/brand/from-my-desk-logo-source.png")
    assert exc.value.code == 404


def test_live_four_way_decisions_unchanged():
    cases = [
        (100, "40.00", False, False, "allow"),
        (200, "40.00", False, False, "confirm"),
        (300, "40.00", False, False, "step_up"),
        (450, "40.00", False, False, "deny"),
    ]
    for quantity, price, confirmed, mfa, expected in cases:
        code, body = _post_json(
            "/api/evaluate",
            _eval_payload(quantity, price, confirmed, mfa),
        )
        assert code == 200
        assert body["decision"] == expected
        assert body["execution"] == "not_performed"

    code, body = _post_json(
        "/api/evaluate",
        _eval_payload(200, "40.00", confirmed=True, mfa=False),
    )
    assert code == 200
    assert body["decision"] == "allow"
    assert body["execution"] == "not_performed"

    code, body = _post_json(
        "/api/evaluate",
        _eval_payload(300, "40.00", confirmed=True, mfa=True),
    )
    assert code == 200
    assert body["decision"] == "allow"
    assert body["execution"] == "not_performed"
