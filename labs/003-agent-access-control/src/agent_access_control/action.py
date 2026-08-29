"""Requested action evaluator."""

from __future__ import annotations

from typing import Any, Dict, Set

from .models import AccessRequest, EvaluationFragment


def evaluate_action(
    request: AccessRequest,
    agents: Dict[str, Dict[str, Any]],
    policy: Dict[str, Any],
) -> EvaluationFragment:
    protected_actions: Set[str] = set(policy.get("protected_actions") or [])
    sensitive_actions: Set[str] = set(policy.get("sensitive_actions") or [])
    agent = agents.get(request.agent_id)

    if agent is None and request.requested_action in protected_actions:
        return EvaluationFragment(
            stage="action",
            outcome="failed",
            decision_signal="deny",
            reason_code="unknown_agent_protected_action",
            hard_authority_failure=True,
            summary=(
                "Unknown agents cannot invoke protected action '{0}' at Cedar Quill Markets."
            ).format(request.requested_action),
            details={
                "requested_action": request.requested_action,
                "protection": "protected",
            },
        )

    if request.restricted_operation and request.requested_action == "register":
        return EvaluationFragment(
            stage="action",
            outcome="restricted",
            decision_signal="allow",
            reason_code="restricted_registration_permitted",
            summary="Restricted registration action is permitted on the registration path only.",
            details={"requested_action": request.requested_action, "restricted_operation": True},
        )

    if request.requested_action in sensitive_actions:
        return EvaluationFragment(
            stage="action",
            outcome="warning",
            decision_signal="confirm",
            reason_code="human_consent_required",
            summary=(
                "Action '{0}' requires explicit human consent at Cedar Quill Markets."
            ).format(request.requested_action),
            details={"requested_action": request.requested_action, "sensitivity": "high"},
        )

    return EvaluationFragment(
        stage="action",
        outcome="satisfied",
        summary="Requested action '{0}' is within the evaluated action catalog.".format(
            request.requested_action
        ),
        details={"requested_action": request.requested_action},
    )
