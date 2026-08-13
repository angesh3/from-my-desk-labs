import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from models import EvaluateRequest
from policy_engine import evaluate
from loader import load_desk_policy, load_registry


@pytest.fixture
def registry():
    return load_registry()


@pytest.fixture
def desk_policy():
    return load_desk_policy()


def _request(**overrides):
    payload = {
        "agent_id": "kya-agent-001",
        "action": "propose_paper_order",
        "order": {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": 10,
            "limit_price": 42.5,
            "account_id": "paper-desk-alpha",
        },
    }
    payload.update(overrides)
    if "order" in overrides:
        order = {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": 10,
            "limit_price": 42.5,
            "account_id": "paper-desk-alpha",
        }
        order.update(overrides["order"])
        payload["order"] = order
    return EvaluateRequest.model_validate(payload)


def test_allows_registered_agent_within_policy(registry, desk_policy):
    result = evaluate(_request(), registry, desk_policy)
    assert result.decision == "allow"
    assert result.reason_code == "ok"
    assert result.notional == 425.0


def test_denies_unknown_agent(registry, desk_policy):
    result = evaluate(_request(agent_id="unknown-bot"), registry, desk_policy)
    assert result.decision == "deny"
    assert result.reason_code == "unknown_agent"


def test_denies_inactive_agent(registry, desk_policy):
    result = evaluate(_request(agent_id="kya-agent-dormant"), registry, desk_policy)
    assert result.decision == "deny"
    assert result.reason_code == "inactive_agent"


def test_denies_restricted_ticker(registry, desk_policy):
    result = evaluate(_request(order={"ticker": "MAPLE"}), registry, desk_policy)
    assert result.decision == "deny"
    assert result.reason_code == "ticker_restricted"


def test_denies_notional_over_cap(registry, desk_policy):
    result = evaluate(
        _request(order={"ticker": "WILLO", "quantity": 1000, "limit_price": 40.0}),
        registry,
        desk_policy,
    )
    assert result.decision == "deny"
    assert result.reason_code == "notional_exceeds_cap"


def test_denies_unassigned_account(registry, desk_policy):
    result = evaluate(
        _request(order={"account_id": "paper-desk-beta"}),
        registry,
        desk_policy,
    )
    assert result.decision == "deny"
    assert result.reason_code == "account_not_assigned"
