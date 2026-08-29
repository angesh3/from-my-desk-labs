"""Agent Management Plane — registration, unknown, and unmanaged states."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import EvaluationFragment, RegistrationState


class AgentManagementPlane:
    """Educational management plane for Cedar Quill Markets agents."""

    def __init__(self, agents: Dict[str, Dict[str, Any]]) -> None:
        self._agents = agents

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def is_registered(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def registration_state(self, agent_id: str) -> RegistrationState:
        agent = self._agents.get(agent_id)
        if agent is None:
            return "unknown"
        status = str(agent.get("management_status", "registered"))
        if status in {"unmanaged", "unknown"}:
            return status  # type: ignore[return-value]
        return "registered"

    def management_status(self, agent_id: str) -> str:
        return self.registration_state(agent_id)

    def approved_tools(self, agent_id: str) -> List[str]:
        agent = self._agents.get(agent_id) or {}
        return list(agent.get("approved_tools") or [])

    def approved_model_version(self, agent_id: str) -> Optional[str]:
        agent = self._agents.get(agent_id) or {}
        return agent.get("approved_model_version")

    def inventory(self) -> List[Dict[str, Any]]:
        out = []
        for agent_id, raw in sorted(self._agents.items()):
            out.append(
                {
                    "agent_id": agent_id,
                    "display_name": raw.get("display_name", agent_id),
                    "status": raw.get("status", "active"),
                    "registration_state": self.registration_state(agent_id),
                    "classification": raw.get("classification", "unknown"),
                }
            )
        return out


def evaluate_registration(
    agent_id: str,
    management: AgentManagementPlane,
    request_restricted: bool,
) -> EvaluationFragment:
    state = management.registration_state(agent_id)
    if state == "unknown" and request_restricted:
        return EvaluationFragment(
            stage="registration",
            outcome="restricted",
            decision_signal="allow",
            reason_code="restricted_registration_permitted",
            summary=(
                "Unknown agent may use the restricted registration path only; "
                "no operational authority is granted."
            ),
            details={"registration_state": state, "restricted_operation": True},
        )
    if state == "unknown":
        return EvaluationFragment(
            stage="registration",
            outcome="failed",
            summary="Agent is not registered in the Cedar Quill Markets management plane.",
            details={"registration_state": state},
        )
    if state == "unmanaged":
        return EvaluationFragment(
            stage="registration",
            outcome="warning",
            decision_signal="step_up",
            reason_code="profile_mismatch",
            summary="Agent is known but unmanaged; additional review is required.",
            details={"registration_state": state},
        )
    return EvaluationFragment(
        stage="registration",
        outcome="satisfied",
        summary="Agent is registered and managed by Cedar Quill Markets.",
        details={"registration_state": state},
    )
