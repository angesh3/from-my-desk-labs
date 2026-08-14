from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from know_your_agent.loader import load_bundle
from know_your_agent.models import EvaluateRequest
from know_your_agent.policy_engine import compute_notional, evaluate


@pytest.fixture
def bundle():
    return load_bundle(Path(__file__).resolve().parents[1] / "policies")


def make_request(
    quantity=100,
    limit_price="40.00",
    ticker="BRICK",
    agent_id="kya-agent-001",
    principal_id="principal-demo-001",
    account_id="paper-desk-alpha",
    action="propose_paper_order",
    confirmed=False,
    mfa=False,
    side="buy",
):
    return EvaluateRequest.model_validate(
        {
            "principal_id": principal_id,
            "agent_id": agent_id,
            "action": action,
            "order": {
                "ticker": ticker,
                "side": side,
                "quantity": quantity,
                "limit_price": limit_price,
                "account_id": account_id,
            },
            "authorization_context": {
                "customer_confirmed": confirmed,
                "mfa_verified": mfa,
            },
        }
    )


def test_notional_uses_decimal():
    assert compute_notional(1, Decimal("0.10")) == Decimal("0.10")
    assert compute_notional(3, Decimal("1.10")) == Decimal("3.30")


@pytest.mark.parametrize(
    "price,confirmed,mfa,decision,code",
    [
        ("4000.00", False, False, "allow", "ok"),
        ("5000.00", False, False, "allow", "ok"),
        ("5000.01", False, False, "confirm", "confirmation_required"),
        ("8000.00", False, False, "confirm", "confirmation_required"),
        ("8000.00", True, False, "allow", "ok"),
        ("10000.00", False, False, "confirm", "confirmation_required"),
        ("10000.00", True, False, "allow", "ok"),
        ("10000.01", False, False, "step_up", "step_up_required"),
        ("12000.00", False, False, "step_up", "step_up_required"),
        ("12000.00", True, False, "step_up", "step_up_required"),
        ("12000.00", False, True, "step_up", "step_up_required"),
        ("12000.00", True, True, "allow", "ok"),
        ("15000.00", False, False, "step_up", "step_up_required"),
        ("15000.00", True, True, "allow", "ok"),
        ("15000.01", False, False, "deny", "amount_exceeds_limit"),
        ("18000.00", False, False, "deny", "amount_exceeds_limit"),
    ],
)
def test_amount_bands(bundle, price, confirmed, mfa, decision, code):
    result = evaluate(
        make_request(quantity=1, limit_price=price, confirmed=confirmed, mfa=mfa),
        bundle,
    )
    assert result.decision == decision
    assert result.reason_code == code
    assert result.notional == str(Decimal(price).quantize(Decimal("0.01")))
    assert result.audit_id.startswith("aud-")
    assert result.execution == "not_performed"
