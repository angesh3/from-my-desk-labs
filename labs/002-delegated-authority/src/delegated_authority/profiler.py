"""Agent Profiling Engine (APE). Profiling never manufactures authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    ActionRequest,
    AgentProfile,
    DeclaredAttributes,
    ObservedAttributes,
    VerifiedAttributes,
)
from .management import AgentManagementPlane


def evaluate_profile(
    request: ActionRequest,
    profiles: Dict[str, Dict[str, Any]],
    management: AgentManagementPlane,
    now: Optional[datetime] = None,
) -> AgentProfile:
    evaluated_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    raw = profiles.get(request.agent_id)
    if raw is None:
        return AgentProfile(
            agent_id=request.agent_id,
            classification="Unknown",
            declared_attributes=DeclaredAttributes(
                agent_type="unknown",
                model="unknown",
                tools=[],
                declared_capabilities=[],
                owner="unknown",
            ),
            observed_attributes=ObservedAttributes(
                typical_data_access=[],
                typical_tool_usage=[],
                typical_action_types=[],
                typical_operating_period="unknown",
                observed_execution_behavior="unknown",
            ),
            verified_attributes=VerifiedAttributes(
                signed_manifest=False,
                approved_software_version="unknown",
                attested_runtime=False,
                registered_environment="unknown",
                verified_tool_inventory=[],
            ),
            expected_capabilities=[],
            expected_tools=[],
            management_status=management.management_status(request.agent_id),
            confidence="low",
            profile_mismatch=True,
            profile_status="unknown",
            profile_version="0",
            evaluated_at=evaluated_at,
        )

    declared = DeclaredAttributes.model_validate(raw["declared"])
    observed = ObservedAttributes.model_validate(raw["observed"])
    verified = VerifiedAttributes.model_validate(raw["verified"])
    expected_caps = list(raw.get("expected_capabilities") or declared.declared_capabilities)
    expected_tools = list(raw.get("expected_tools") or verified.verified_tool_inventory)
    classification = str(raw.get("classification", declared.agent_type))
    confidence = str(raw.get("confidence", "medium"))
    mismatch = bool(raw.get("profile_mismatch", False))
    status = str(raw.get("profile_status", "known"))

    # Observed execution behavior while classified as research → mismatch signal
    if (
        classification.lower().startswith("research")
        and request.requested_capability in {"execute", "execution", "propose_paper_order"}
        and "execute" not in expected_caps
    ):
        mismatch = True

    if status == "conflicting":
        mismatch = True

    return AgentProfile(
        agent_id=request.agent_id,
        classification=classification,
        declared_attributes=declared,
        observed_attributes=observed,
        verified_attributes=verified,
        expected_capabilities=expected_caps,
        expected_tools=expected_tools,
        management_status=management.management_status(request.agent_id),
        confidence=confidence,  # type: ignore[arg-type]
        profile_mismatch=mismatch,
        profile_status=status,  # type: ignore[arg-type]
        profile_version=str(raw.get("profile_version", "1")),
        evaluated_at=evaluated_at,
    )


def profile_cannot_grant_authority(
    profile: AgentProfile, delegated_capabilities: List[str], requested: str
) -> bool:
    """True when delegated authority does not include the request.

    An Execution Agent profile never manufactures missing capability.
    """
    _ = profile  # profile may look like an executor; it still cannot grant authority
    return requested not in set(delegated_capabilities)
