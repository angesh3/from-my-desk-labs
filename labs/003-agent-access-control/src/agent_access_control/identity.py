"""Identity evaluator for Lab 003."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import AccessRequest, EvaluationFragment, IdentityResult


def evaluate_identity(
    request: AccessRequest,
    agents: Dict[str, Dict[str, Any]],
    now: Optional[datetime] = None,
) -> tuple[IdentityResult, EvaluationFragment]:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    agent = agents.get(request.agent_id)
    if agent is None:
        if request.restricted_operation and request.requested_action == "register":
            result = IdentityResult(
                identity_status="unknown",
                agent_status="unknown",
                principal_binding="invalid",
                assurance_level=request.assurance_level,
                evaluated_at=evaluated_at,
                reason_code=None,
            )
            fragment = EvaluationFragment(
                stage="identity",
                outcome="restricted",
                summary="Identity is unknown; restricted registration path applies.",
                details={"identity_status": "unknown"},
            )
            return result, fragment
        result = IdentityResult(
            identity_status="unknown",
            agent_status="unknown",
            principal_binding="invalid",
            assurance_level=request.assurance_level,
            evaluated_at=evaluated_at,
            reason_code="agent_unknown",
        )
        fragment = EvaluationFragment(
            stage="identity",
            outcome="failed",
            summary="The requesting agent identity is unknown.",
            details={"identity_status": "unknown"},
        )
        return result, fragment

    status = str(agent.get("status", "active"))
    principal = str(agent.get("principal_id", ""))
    assurance = str(agent.get("assurance_level", "standard"))

    if status == "revoked":
        result = IdentityResult(
            identity_status="invalid",
            agent_status="revoked",
            principal_binding="valid" if principal == request.principal_id else "invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="identity_invalid",
        )
        fragment = EvaluationFragment(
            stage="identity",
            outcome="failed",
            decision_signal="deny",
            reason_code="identity_invalid",
            hard_authority_failure=True,
            summary="Agent credentials are revoked.",
            details={"agent_status": status},
        )
        return result, fragment

    if status == "suspended":
        result = IdentityResult(
            identity_status="invalid",
            agent_status="suspended",
            principal_binding="valid" if principal == request.principal_id else "invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="identity_invalid",
        )
        fragment = EvaluationFragment(
            stage="identity",
            outcome="failed",
            decision_signal="deny",
            reason_code="identity_invalid",
            hard_authority_failure=True,
            summary="Agent is suspended.",
            details={"agent_status": status},
        )
        return result, fragment

    if principal != request.principal_id:
        result = IdentityResult(
            identity_status="invalid",
            agent_status="active",
            principal_binding="invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="principal_mismatch",
        )
        fragment = EvaluationFragment(
            stage="identity",
            outcome="failed",
            decision_signal="deny",
            reason_code="principal_mismatch",
            hard_authority_failure=True,
            summary="Agent is not bound to the stated principal.",
            details={"principal_binding": "invalid"},
        )
        return result, fragment

    result = IdentityResult(
        identity_status="valid",
        agent_status="active",
        principal_binding="valid",
        assurance_level=assurance,
        evaluated_at=evaluated_at,
        reason_code=None,
    )
    fragment = EvaluationFragment(
        stage="identity",
        outcome="satisfied",
        summary="Agent identity is valid and active.",
        details={"identity_status": "valid", "agent_status": status},
    )
    return result, fragment
