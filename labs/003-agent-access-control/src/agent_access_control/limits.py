"""Transaction and exposure limit evaluator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from .models import AccessRequest, DelegationResult, EvaluationFragment, as_decimal


def evaluate_limits(
    request: AccessRequest,
    delegation: DelegationResult | None,
    policy: Dict[str, Any],
) -> EvaluationFragment:
    if request.restricted_operation:
        return EvaluationFragment(
            stage="limits",
            outcome="restricted",
            summary="Restricted registration path has zero operational exposure.",
            details={"requested_amount": str(request.requested_amount), "exposure": "0.00"},
        )

    confirm_threshold = as_decimal(policy.get("confirm_threshold", "5000.00"))
    amount = request.requested_amount

    if delegation and delegation.effective_limit:
        effective_limit = as_decimal(delegation.effective_limit)
        if amount > effective_limit:
            return EvaluationFragment(
                stage="limits",
                outcome="failed",
                decision_signal="deny",
                reason_code="capability_not_delegated",
                hard_authority_failure=True,
                summary="Requested amount exceeds effective delegated limit.",
                details={
                    "requested_amount": str(amount),
                    "effective_limit": str(effective_limit),
                },
            )

    if amount > confirm_threshold:
        return EvaluationFragment(
            stage="limits",
            outcome="warning",
            decision_signal="confirm",
            reason_code="limit_requires_confirmation",
            summary=(
                "Amount {0} exceeds the autonomous confirmation threshold {1}."
            ).format(amount, confirm_threshold),
            details={
                "requested_amount": str(amount),
                "confirm_threshold": str(confirm_threshold),
            },
        )

    return EvaluationFragment(
        stage="limits",
        outcome="satisfied",
        summary="Requested amount is within autonomous limits.",
        details={"requested_amount": str(amount)},
    )
