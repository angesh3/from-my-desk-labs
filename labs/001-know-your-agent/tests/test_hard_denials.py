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
        ({"agent_id": "unknown-bot"}, "unknown_agent"),
        ({"agent_id": "kya-agent-dormant"}, "inactive_agent"),
        ({"agent_id": "kya-agent-revoked"}, "authority_revoked"),
        ({"agent_id": "kya-agent-expired"}, "authority_expired"),
        ({"principal_id": "principal-other-009"}, "principal_mismatch"),
        ({"agent_id": "kya-agent-observer"}, "capability_denied"),
        ({"account_id": "paper-desk-beta"}, "account_not_assigned"),
        ({"ticker": "ZZXX"}, "ticker_not_allowed"),
        ({"ticker": "MAPLE"}, "ticker_restricted"),
    ],
)
def test_hard_denials(bundle, kwargs, code):
    result = evaluate(make_request(**kwargs), bundle)
    assert result.decision == "deny"
    assert result.reason_code == code
    assert result.required_action is None
