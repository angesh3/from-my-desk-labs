"""Stated purpose evaluator."""

from __future__ import annotations

from typing import Any, Dict, List

from .models import AccessRequest, DelegationResult, EvaluationFragment


def evaluate_purpose(
    request: AccessRequest,
    delegation: DelegationResult | None,
) -> EvaluationFragment:
    if request.restricted_operation and request.requested_action == "register":
        return EvaluationFragment(
            stage="purpose",
            outcome="restricted",
            summary="Purpose limited to agent registration for Cedar Quill Markets onboarding.",
            details={"stated_purpose": request.stated_purpose, "scope": "registration_only"},
        )

    permitted: List[str] = []
    if delegation and delegation.effective_purposes:
        permitted = delegation.effective_purposes
    elif delegation and delegation.chain_status == "valid":
        permitted = ["market_research", "portfolio_analysis"]

    if permitted and request.stated_purpose not in permitted:
        return EvaluationFragment(
            stage="purpose",
            outcome="failed",
            decision_signal="deny",
            reason_code="purpose_not_permitted",
            hard_authority_failure=True,
            summary=(
                "Stated purpose '{0}' is not permitted by effective delegation."
            ).format(request.stated_purpose),
            details={
                "stated_purpose": request.stated_purpose,
                "permitted_purposes": permitted,
            },
        )

    return EvaluationFragment(
        stage="purpose",
        outcome="satisfied",
        summary="Stated purpose '{0}' is permitted.".format(request.stated_purpose),
        details={"stated_purpose": request.stated_purpose},
    )
