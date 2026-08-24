"""Agent Posture and Security Engine (APSE). Posture never expands authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import ActionRequest, PostureEvidence
from .management import AgentManagementPlane


def evaluate_posture(
    request: ActionRequest,
    posture_records: Dict[str, Dict[str, Any]],
    management: AgentManagementPlane,
    now: Optional[datetime] = None,
) -> PostureEvidence:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    raw = posture_records.get(request.agent_id)
    if raw is None:
        return PostureEvidence(
            agent_id=request.agent_id,
            posture_status="unknown",
            risk_level="high",
            model_version_status="unknown",
            configuration_integrity="unknown",
            tool_inventory_status="unknown",
            attestation_status="unknown",
            credential_status="unknown",
            behavior_status="unknown",
            evidence_freshness="missing",
            recommended_treatment="restricted_fallback",
            posture_version="0",
            evaluated_at=evaluated_at,
            reason_code="agent_unknown",
        )

    status = str(raw.get("posture_status", "compliant"))
    freshness = str(raw.get("evidence_freshness", "current"))
    tool_status = str(raw.get("tool_inventory_status", "expected"))
    model_status = str(raw.get("model_version_status", "approved"))
    attestation = str(raw.get("attestation_status", "ok"))
    risk = str(raw.get("risk_level", "low"))
    treatment = str(raw.get("recommended_treatment", "continue"))
    reason = raw.get("reason_code")

    if attestation in {"compromised", "failed"}:
        status = "noncompliant"
        treatment = "deny"
        reason = reason or "runtime_compromised"
        risk = "high"
    elif tool_status in {"changed", "unexpected", "unauthorized"}:
        status = "noncompliant"
        treatment = "deny"
        reason = reason or "tool_inventory_changed"
        risk = "high"
    elif freshness == "stale":
        status = "stale"
        treatment = "step_up"
        reason = reason or "posture_evidence_stale"
        risk = risk if risk != "low" else "medium"
    elif model_status in {"noncompliant", "outdated"}:
        status = "noncompliant"
        treatment = "step_up"
        reason = reason or "model_version_noncompliant"
        risk = risk if risk != "low" else "medium"
    elif not management.is_registered(request.agent_id):
        status = "unknown"
        treatment = "restricted_fallback"
        reason = reason or "agent_unknown"

    return PostureEvidence(
        agent_id=request.agent_id,
        posture_status=status,  # type: ignore[arg-type]
        risk_level=risk,  # type: ignore[arg-type]
        model_version_status=model_status,
        configuration_integrity=str(raw.get("configuration_integrity", "intact")),
        tool_inventory_status=tool_status,
        attestation_status=attestation,
        credential_status=str(raw.get("credential_status", "healthy")),
        behavior_status=str(raw.get("behavior_status", "normal")),
        evidence_freshness=freshness,  # type: ignore[arg-type]
        recommended_treatment=treatment,  # type: ignore[arg-type]
        posture_version=str(raw.get("posture_version", "1")),
        evaluated_at=evaluated_at,
        reason_code=reason,
    )
