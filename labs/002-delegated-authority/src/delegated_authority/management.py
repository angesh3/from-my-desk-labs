"""Agent Management Plane — educational registration and inventory data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class AgentManagementPlane:
    """In-process educational data layer (not a separate deployable service)."""

    def __init__(self, agents: Dict[str, Dict[str, Any]]) -> None:
        self._agents = agents

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def is_registered(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def management_status(self, agent_id: str) -> str:
        agent = self._agents.get(agent_id)
        if agent is None:
            return "unregistered"
        return str(agent.get("management_status", "managed"))

    def approved_tools(self, agent_id: str) -> List[str]:
        agent = self._agents.get(agent_id) or {}
        tools = agent.get("approved_tools") or []
        return list(tools)

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
                    "management_status": raw.get("management_status", "managed"),
                    "classification": raw.get("classification", "unknown"),
                }
            )
        return out
