"""Requested tool evaluator."""

from __future__ import annotations

from typing import Any, Dict, Set

from .management import AgentManagementPlane
from .models import AccessRequest, AgentProfile, EvaluationFragment


def evaluate_tool(
    request: AccessRequest,
    management: AgentManagementPlane,
    profile: AgentProfile,
    policy: Dict[str, Any],
) -> EvaluationFragment:
    protected_tools: Set[str] = set(policy.get("protected_tools") or [])
    approved = set(management.approved_tools(request.agent_id))
    expected = set(profile.expected_tools)

    if request.requested_tool in protected_tools and not management.is_registered(
        request.agent_id
    ):
        return EvaluationFragment(
            stage="tool",
            outcome="failed",
            decision_signal="deny",
            reason_code="unknown_agent_protected_action",
            hard_authority_failure=True,
            summary="Unknown agents cannot use protected tool '{0}'.".format(
                request.requested_tool
            ),
            details={"requested_tool": request.requested_tool, "protection": "protected"},
        )

    if request.restricted_operation:
        allowed = set(policy.get("restricted_registration_tools") or ["registration_portal"])
        if request.requested_tool in allowed:
            return EvaluationFragment(
                stage="tool",
                outcome="restricted",
                summary="Tool '{0}' is permitted on the restricted registration path.".format(
                    request.requested_tool
                ),
                details={"requested_tool": request.requested_tool},
            )

    declared_tools = approved or expected
    if declared_tools and request.requested_tool not in declared_tools:
        return EvaluationFragment(
            stage="tool",
            outcome="failed",
            decision_signal="deny",
            reason_code="tool_inventory_changed",
            hard_authority_failure=True,
            summary="Requested tool '{0}' is not in the approved inventory.".format(
                request.requested_tool
            ),
            details={
                "requested_tool": request.requested_tool,
                "approved_tools": sorted(declared_tools),
            },
        )

    return EvaluationFragment(
        stage="tool",
        outcome="satisfied",
        summary="Tool '{0}' matches the declared inventory.".format(request.requested_tool),
        details={"requested_tool": request.requested_tool},
    )
