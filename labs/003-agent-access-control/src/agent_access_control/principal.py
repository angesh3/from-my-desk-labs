"""Principal binding evaluator for Lab 003."""

from __future__ import annotations

from typing import Any, Dict

from .models import AccessRequest, EvaluationFragment, IdentityResult


def evaluate_principal(
    request: AccessRequest,
    identity: IdentityResult,
    agents: Dict[str, Dict[str, Any]],
) -> EvaluationFragment:
    agent = agents.get(request.agent_id)
    if identity.reason_code == "principal_mismatch":
        return EvaluationFragment(
            stage="principal",
            outcome="failed",
            decision_signal="deny",
            reason_code="principal_mismatch",
            hard_authority_failure=True,
            summary="Principal binding failed for Cedar Quill Markets desk {0}.".format(
                request.principal_id
            ),
            details={"principal_id": request.principal_id, "binding": "invalid"},
        )
    if agent is None and request.restricted_operation:
        return EvaluationFragment(
            stage="principal",
            outcome="restricted",
            summary=(
                "Principal asserted for restricted registration; "
                "operational binding deferred until registration completes."
            ),
            details={"principal_id": request.principal_id, "binding": "pending"},
        )
    return EvaluationFragment(
        stage="principal",
        outcome="satisfied",
        summary="Principal binding is valid for desk {0}.".format(request.principal_id),
        details={"principal_id": request.principal_id, "binding": "valid"},
    )
