"""Four-way educational policy engine. Hard denials always win."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from .audit import new_audit_id
from .loader import AgentRecord, DeskPolicy, PolicyBundle
from .models import EvaluateRequest, EvaluateResponse, PolicyCheck, RequiredAction

MONEY = Decimal("0.01")


def compute_notional(quantity: int, limit_price: Decimal) -> Decimal:
    return (Decimal(quantity) * limit_price).quantize(MONEY)


def format_money(amount: Decimal) -> str:
    return str(amount.quantize(MONEY))


def _result(
    decision: str,
    reason_code: str,
    reason: str,
    policy_id: str,
    checks: List[PolicyCheck],
    notional: Optional[Decimal] = None,
    required_action: RequiredAction = None,
) -> EvaluateResponse:
    return EvaluateResponse(
        decision=decision,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        required_action=required_action,
        policy_id=policy_id,
        audit_id=new_audit_id(),
        notional=format_money(notional) if notional is not None else None,
        checks=checks,
        execution="not_performed",
    )


def _fail(
    checks: List[PolicyCheck],
    name: str,
    explanation: str,
    reason_code: str,
    reason: str,
    policy_id: str,
    notional: Optional[Decimal] = None,
) -> EvaluateResponse:
    checks.append(PolicyCheck(name=name, result="fail", explanation=explanation))
    return _result("deny", reason_code, reason, policy_id, checks, notional)


def evaluate(
    request: EvaluateRequest,
    bundle: PolicyBundle,
    now: Optional[datetime] = None,
) -> EvaluateResponse:
    """Evaluate identity, authority, then amount. Flags never override DENY."""
    policy = bundle.policy
    checks: List[PolicyCheck] = []
    notional = compute_notional(request.order.quantity, request.order.limit_price)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    moment = moment.astimezone(timezone.utc)

    agent = bundle.agents.get(request.agent_id)
    if agent is None:
        return _fail(
            checks,
            "agent_exists",
            "No registered agent matches this identifier.",
            "unknown_agent",
            "The agent is not in the fictional identity registry.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="agent_exists",
            result="pass",
            explanation="Agent {0} is present in the registry.".format(agent.agent_id),
        )
    )

    hard = _hard_authorization(request, agent, policy, checks, moment, notional)
    if hard is not None:
        return hard

    return _amount_decision(request, policy, checks, notional)


def _hard_authorization(
    request: EvaluateRequest,
    agent: AgentRecord,
    policy: DeskPolicy,
    checks: List[PolicyCheck],
    moment: datetime,
    notional: Decimal,
) -> Optional[EvaluateResponse]:
    if agent.status != "active":
        return _fail(
            checks,
            "agent_status",
            "Agent status is '{0}', not active.".format(agent.status),
            "inactive_agent",
            "The agent is registered but is not active.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="agent_status",
            result="pass",
            explanation="Agent is active.",
        )
    )

    if moment < agent.valid_from or moment > agent.valid_until:
        return _fail(
            checks,
            "authority_not_expired",
            "Delegated authority is outside its validity window.",
            "authority_expired",
            "The agent's delegated authority is not in force at this time.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="authority_not_expired",
            result="pass",
            explanation="Delegated authority is within its validity window.",
        )
    )

    if agent.revoked:
        return _fail(
            checks,
            "authority_not_revoked",
            "Delegated authority has been revoked.",
            "authority_revoked",
            "The principal has revoked this agent's authority.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="authority_not_revoked",
            result="pass",
            explanation="Delegated authority has not been revoked.",
        )
    )

    if request.principal_id != agent.principal_id:
        return _fail(
            checks,
            "principal_match",
            "Request principal does not match the delegating principal.",
            "principal_mismatch",
            "The request is not from the principal that delegated authority.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="principal_match",
            result="pass",
            explanation="Request principal matches the delegating principal.",
        )
    )

    if request.action not in agent.capabilities:
        return _fail(
            checks,
            "capability_allowed",
            "Action '{0}' is not in the agent's capabilities.".format(request.action),
            "capability_denied",
            "This agent is not permitted to perform the requested action.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="capability_allowed",
            result="pass",
            explanation="Requested action is an allowed capability.",
        )
    )

    if request.order.account_id not in agent.accounts:
        return _fail(
            checks,
            "account_assigned",
            "Account '{0}' is not assigned to this agent.".format(request.order.account_id),
            "account_not_assigned",
            "The requested paper account is not assigned to this agent.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="account_assigned",
            result="pass",
            explanation="The requested paper account is assigned to this agent.",
        )
    )

    ticker = request.order.ticker
    if ticker not in policy.allowed_tickers:
        return _fail(
            checks,
            "ticker_allowed",
            "Ticker '{0}' is not on the fictional allow-list.".format(ticker),
            "ticker_not_allowed",
            "The requested ticker is outside the agent's resource scope.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="ticker_allowed",
            result="pass",
            explanation="Ticker {0} is on the fictional allow-list.".format(ticker),
        )
    )

    if ticker in policy.restricted_tickers:
        return _fail(
            checks,
            "ticker_not_restricted",
            "Ticker '{0}' is restricted by desk policy.".format(ticker),
            "ticker_restricted",
            "The requested ticker is restricted and cannot be used.",
            policy.policy_id,
            notional,
        )
    checks.append(
        PolicyCheck(
            name="ticker_not_restricted",
            result="pass",
            explanation="Ticker {0} is not restricted.".format(ticker),
        )
    )
    return None


def _amount_decision(
    request: EvaluateRequest,
    policy: DeskPolicy,
    checks: List[PolicyCheck],
    notional: Decimal,
) -> EvaluateResponse:
    confirmed = request.authorization_context.customer_confirmed
    mfa = request.authorization_context.mfa_verified

    if notional <= policy.allow_max:
        checks.append(
            PolicyCheck(
                name="notional_band",
                result="pass",
                explanation="Notional {0} is at or under the ALLOW threshold of {1}.".format(
                    format_money(notional), format_money(policy.allow_max)
                ),
            )
        )
        return _result(
            "allow",
            "ok",
            "Hard authorization passed and the amount is within the ALLOW band. No order is executed.",
            policy.policy_id,
            checks,
            notional,
        )

    if notional <= policy.confirm_max:
        checks.append(
            PolicyCheck(
                name="notional_band",
                result="pass",
                explanation="Notional {0} is in the CONFIRM band (above {1} through {2}).".format(
                    format_money(notional),
                    format_money(policy.allow_max),
                    format_money(policy.confirm_max),
                ),
            )
        )
        if confirmed:
            checks.append(
                PolicyCheck(
                    name="confirmation_satisfied",
                    result="pass",
                    explanation="Customer confirmation is present for this amount band.",
                )
            )
            return _result(
                "allow",
                "ok",
                "Hard authorization passed and customer confirmation is present. No order is executed.",
                policy.policy_id,
                checks,
                notional,
            )
        checks.append(
            PolicyCheck(
                name="confirmation_satisfied",
                result="fail",
                explanation="Customer confirmation is required for this amount band.",
            )
        )
        return _result(
            "confirm",
            "confirmation_required",
            "The amount requires explicit customer confirmation before it may proceed. No order is executed.",
            policy.policy_id,
            checks,
            notional,
            required_action="customer_confirmation",
        )

    if notional <= policy.step_up_max:
        checks.append(
            PolicyCheck(
                name="notional_band",
                result="pass",
                explanation="Notional {0} is in the STEP_UP band (above {1} through {2}).".format(
                    format_money(notional),
                    format_money(policy.confirm_max),
                    format_money(policy.step_up_max),
                ),
            )
        )
        if confirmed and mfa:
            checks.append(
                PolicyCheck(
                    name="step_up_satisfied",
                    result="pass",
                    explanation="Customer confirmation and MFA are both present.",
                )
            )
            return _result(
                "allow",
                "ok",
                "Hard authorization passed with confirmation and MFA. No order is executed.",
                policy.policy_id,
                checks,
                notional,
            )
        checks.append(
            PolicyCheck(
                name="step_up_satisfied",
                result="fail",
                explanation="This amount requires both customer confirmation and MFA.",
            )
        )
        required: RequiredAction
        if not mfa:
            required = "mfa_verification"
        else:
            required = "customer_confirmation"
        return _result(
            "step_up",
            "step_up_required",
            "The amount requires stronger authentication (MFA) in addition to confirmation. No order is executed.",
            policy.policy_id,
            checks,
            notional,
            required_action=required,
        )

    checks.append(
        PolicyCheck(
            name="notional_band",
            result="fail",
            explanation="Notional {0} exceeds the absolute maximum of {1}.".format(
                format_money(notional), format_money(policy.step_up_max)
            ),
        )
    )
    return _result(
        "deny",
        "amount_exceeds_limit",
        "The amount is above the absolute fictional maximum. Confirmation and MFA cannot override this limit.",
        policy.policy_id,
        checks,
        notional,
    )
