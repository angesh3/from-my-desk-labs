from typing import Any, Dict

from models import EvaluateRequest, EvaluateResponse


def _deny(reason_code: str, message: str, checks, notional=None, policy_bundle=None):
    return EvaluateResponse(
        decision="deny",
        reason_code=reason_code,
        message=message,
        notional=notional,
        policy_bundle=policy_bundle,
        checks=checks,
    )


def evaluate(
    request: EvaluateRequest,
    registry: Dict[str, Any],
    desk_policy: Dict[str, Any],
) -> EvaluateResponse:
    checks = []
    policy_bundle = desk_policy.get("bundle_id")
    agents = {agent["id"]: agent for agent in registry.get("agents", [])}
    agent = agents.get(request.agent_id)

    if agent is None:
        return _deny(
            "unknown_agent",
            "Agent '{0}' is not in the registry.".format(request.agent_id),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("agent_registered")

    if agent.get("status") != "active":
        return _deny(
            "inactive_agent",
            "Agent '{0}' is registered but not active.".format(request.agent_id),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("agent_active")

    capabilities = agent.get("capabilities", [])
    if request.action not in capabilities:
        return _deny(
            "capability_denied",
            "Agent '{0}' is not allowed to '{1}'.".format(
                request.agent_id, request.action
            ),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("capability_allowed")

    if request.order.account_id not in agent.get("accounts", []):
        return _deny(
            "account_not_assigned",
            "Account '{0}' is not assigned to agent '{1}'.".format(
                request.order.account_id, request.agent_id
            ),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("account_assigned")

    ticker = request.order.ticker.upper()
    allow_list = [item.upper() for item in desk_policy.get("allowed_tickers", [])]
    restricted = [item.upper() for item in desk_policy.get("restricted_tickers", [])]

    if ticker not in allow_list:
        return _deny(
            "ticker_not_allowed",
            "Ticker '{0}' is not on the Cedar Quill Desk allow-list.".format(ticker),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("ticker_allowed")

    if ticker in restricted:
        return _deny(
            "ticker_restricted",
            "Ticker '{0}' is restricted by the current desk policy.".format(ticker),
            checks,
            policy_bundle=policy_bundle,
        )
    checks.append("ticker_not_restricted")

    notional = round(request.order.quantity * request.order.limit_price, 2)
    max_notional = float(desk_policy.get("max_notional_per_order", 0))
    if notional > max_notional:
        return _deny(
            "notional_exceeds_cap",
            "Notional {0} exceeds the desk cap of {1}.".format(notional, max_notional),
            checks,
            notional=notional,
            policy_bundle=policy_bundle,
        )
    checks.append("notional_within_cap")

    return EvaluateResponse(
        decision="allow",
        reason_code="ok",
        message="Proposed paper order is within identity and desk policy.",
        notional=notional,
        policy_bundle=policy_bundle,
        checks=checks,
    )
