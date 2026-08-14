from pathlib import Path

import pytest

from know_your_agent.loader import load_bundle
from know_your_agent.policy_engine import evaluate
from test_policy_engine import make_request


@pytest.fixture
def bundle():
    return load_bundle(Path(__file__).resolve().parents[1] / "policies")


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"ticker": "MAPLE"}, "ticker_restricted"),
        ({"agent_id": "kya-agent-revoked"}, "authority_revoked"),
        ({"principal_id": "principal-other-009"}, "principal_mismatch"),
        ({"quantity": 1, "limit_price": "18000.00"}, "amount_exceeds_limit"),
    ],
)
def test_flags_cannot_override_hard_deny(bundle, kwargs, code):
    result = evaluate(make_request(confirmed=True, mfa=True, **kwargs), bundle)
    assert result.decision == "deny"
    assert result.reason_code == code
    assert result.required_action is None
