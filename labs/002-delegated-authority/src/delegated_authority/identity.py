"""Identity evaluator for Lab 002."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import ActionRequest, IdentityResult


def evaluate_identity(
    request: ActionRequest,
    agents: Dict[str, Dict[str, Any]],
    now: Optional[datetime] = None,
) -> IdentityResult:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    agent = agents.get(request.agent_id)
    if agent is None:
        return IdentityResult(
            identity_status="unknown",
            agent_status="unknown",
            principal_binding="invalid",
            assurance_level=request.assurance_level,
            evaluated_at=evaluated_at,
            reason_code="agent_unknown",
        )

    status = str(agent.get("status", "active"))
    principal = str(agent.get("principal_id", ""))
    assurance = str(agent.get("assurance_level", "standard"))

    if status == "revoked":
        return IdentityResult(
            identity_status="invalid",
            agent_status="revoked",
            principal_binding="valid" if principal == request.principal_id else "invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="identity_invalid",
        )
    if status == "suspended":
        return IdentityResult(
            identity_status="invalid",
            agent_status="suspended",
            principal_binding="valid" if principal == request.principal_id else "invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="identity_invalid",
        )
    if principal != request.principal_id:
        return IdentityResult(
            identity_status="invalid",
            agent_status="active",
            principal_binding="invalid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="principal_mismatch",
        )

    required = str(agent.get("required_assurance", "standard"))
    if _assurance_rank(assurance) < _assurance_rank(required):
        return IdentityResult(
            identity_status="valid",
            agent_status="active",
            principal_binding="valid",
            assurance_level=assurance,
            evaluated_at=evaluated_at,
            reason_code="posture_evidence_stale",
        )

    return IdentityResult(
        identity_status="valid",
        agent_status="active",
        principal_binding="valid",
        assurance_level=assurance,
        evaluated_at=evaluated_at,
        reason_code=None,
    )


def _assurance_rank(level: str) -> int:
    order = {"low": 0, "standard": 1, "elevated": 2, "high": 3}
    return order.get(level, 1)
