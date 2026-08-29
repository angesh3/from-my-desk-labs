"""Agent Profiling Engine (APE). Profiling never manufactures authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .management import AgentManagementPlane
from .models import AccessRequest, AgentProfile, EvaluationFragment


def evaluate_profile(
    request: AccessRequest,
    profiles: Dict[str, Dict[str, Any]],
    management: AgentManagementPlane,
    now: Optional[datetime] = None,
) -> tuple[AgentProfile, EvaluationFragment]:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    raw = profiles.get(request.agent_id)
    if raw is None:
        profile = AgentProfile(
            agent_id=request.agent_id,
            classification="Unknown",
            expected_capabilities=[],
            expected_tools=[],
            management_status=management.registration_state(request.agent_id),
            confidence="low",
            profile_mismatch=True,
            profile_status="unknown",
            profile_version="0",
            evaluated_at=evaluated_at,
        )
        fragment = EvaluationFragment(
            stage="profiler",
            outcome="warning" if request.restricted_operation else "failed",
            summary="No trusted APE profile exists for this agent.",
            details={
                "profile_status": profile.profile_status,
                "confidence": profile.confidence,
            },
        )
        return profile, fragment

    expected_caps = list(raw.get("expected_capabilities") or [])
    expected_tools = list(raw.get("expected_tools") or [])
    classification = str(raw.get("classification", "unknown"))
    confidence = str(raw.get("confidence", "medium"))
    mismatch = bool(raw.get("profile_mismatch", False))
    status = str(raw.get("profile_status", "known"))

    profile = AgentProfile(
        agent_id=request.agent_id,
        classification=classification,
        expected_capabilities=expected_caps,
        expected_tools=expected_tools,
        management_status=management.registration_state(request.agent_id),
        confidence=confidence,  # type: ignore[arg-type]
        profile_mismatch=mismatch,
        profile_status=status,  # type: ignore[arg-type]
        profile_version=str(raw.get("profile_version", "1")),
        evaluated_at=evaluated_at,
    )
    fragment = EvaluationFragment(
        stage="profiler",
        outcome="warning" if mismatch or status == "conflicting" else "satisfied",
        decision_signal="step_up" if mismatch else None,
        reason_code="profile_mismatch" if mismatch else None,
        summary="APE classification {0} (confidence {1}).".format(
            classification, confidence
        ),
        details={
            "profile_status": status,
            "profile_mismatch": mismatch,
            "expected_capabilities": expected_caps,
        },
    )
    return profile, fragment


def profile_cannot_grant_authority(
    profile: AgentProfile, delegated_capabilities: List[str], requested: str
) -> bool:
    """True when delegated authority does not include the request."""
    _ = profile
    return requested not in set(delegated_capabilities)
