"""Agent Posture and Security Engine (APSE). Posture never expands authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .management import AgentManagementPlane
from .models import AccessRequest, EvaluationFragment, PostureEvidence


def evaluate_posture(
    request: AccessRequest,
    posture_records: Dict[str, Dict[str, Any]],
    management: AgentManagementPlane,
    now: Optional[datetime] = None,
) -> tuple[PostureEvidence, EvaluationFragment]:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    raw = posture_records.get(request.agent_id)
    if raw is None:
        posture = PostureEvidence(
            agent_id=request.agent_id,
            posture_status="unknown",
            risk_level="high",
            model_version_status="unknown",
            tool_inventory_status="unknown",
            attestation_status="unknown",
            evidence_freshness="missing",
            recommended_treatment="restricted_recovery",
            posture_version="0",
            evaluated_at=evaluated_at,
            reason_code="agent_unknown",
        )
        fragment = EvaluationFragment(
            stage="posture",
            outcome="warning",
            summary="APSE has no posture evidence for this agent.",
            details={"posture_status": "unknown", "evidence_freshness": "missing"},
        )
        return posture, fragment

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
        reason = reason or "tool_inventory_changed"
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
        treatment = "restricted_recovery"
        reason = reason or "agent_unknown"

    posture = PostureEvidence(
        agent_id=request.agent_id,
        posture_status=status,  # type: ignore[arg-type]
        risk_level=risk,  # type: ignore[arg-type]
        model_version_status=model_status,
        tool_inventory_status=tool_status,
        attestation_status=attestation,
        evidence_freshness=freshness,  # type: ignore[arg-type]
        recommended_treatment=treatment,  # type: ignore[arg-type]
        posture_version=str(raw.get("posture_version", "1")),
        evaluated_at=evaluated_at,
        reason_code=reason,
    )

    if reason == "tool_inventory_changed":
        fragment = EvaluationFragment(
            stage="posture",
            outcome="failed",
            decision_signal="deny",
            reason_code="tool_inventory_changed",
            hard_authority_failure=True,
            summary="APSE detected an undeclared or changed tool inventory.",
            details={"tool_inventory_status": tool_status},
        )
    elif reason == "posture_evidence_stale":
        fragment = EvaluationFragment(
            stage="posture",
            outcome="warning",
            decision_signal="step_up",
            reason_code="posture_evidence_stale",
            summary="Runtime attestation evidence is stale.",
            details={"evidence_freshness": freshness, "attestation_status": attestation},
        )
    elif reason == "model_version_noncompliant":
        fragment = EvaluationFragment(
            stage="posture",
            outcome="warning",
            decision_signal="step_up",
            reason_code="model_version_noncompliant",
            summary="Model or runtime version is not approved by Cedar Quill Markets.",
            details={"model_version_status": model_status},
        )
    else:
        fragment = EvaluationFragment(
            stage="posture",
            outcome="satisfied",
            summary="APSE posture {0}; evidence {1}.".format(status, freshness),
            details={
                "posture_status": status,
                "evidence_freshness": freshness,
                "risk_level": risk,
            },
        )
    return posture, fragment
