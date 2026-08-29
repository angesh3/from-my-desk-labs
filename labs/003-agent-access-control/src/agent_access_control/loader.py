"""Load Lab 003 educational policy and example data."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import ScenarioMeta


class Lab003ConfigError(ValueError):
    """Raised when Lab 003 data cannot be loaded safely."""


class Lab003Bundle:
    def __init__(
        self,
        *,
        agents: Dict[str, Dict[str, Any]],
        profiles: Dict[str, Dict[str, Any]],
        posture: Dict[str, Dict[str, Any]],
        delegations: Dict[str, Dict[str, Any]],
        scenarios: Dict[str, Dict[str, Any]],
        policies: Dict[str, Any],
        data_dir: Path,
    ) -> None:
        self.agents = agents
        self.profiles = profiles
        self.posture = posture
        self.delegations = delegations
        self.scenarios = scenarios
        self.policies = policies
        self.data_dir = data_dir

    def scenario_meta(self) -> List[ScenarioMeta]:
        items: List[ScenarioMeta] = []
        for scenario_id, raw in self.scenarios.items():
            items.append(
                ScenarioMeta(
                    id=scenario_id,
                    title=str(raw["title"]),
                    short_description=str(raw["short_description"]),
                    category=str(raw["category"]),
                    expected_decision=raw["expected_decision"],
                )
            )
        order = list(self.scenarios.keys())
        items.sort(key=lambda item: order.index(item.id))
        return items


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab003ConfigError("Invalid YAML: {0}".format(path.name)) from exc


def _index_by_id(items: Any, key: str = "id") -> Dict[str, Dict[str, Any]]:
    if not isinstance(items, list):
        raise Lab003ConfigError("Expected a list of mappings.")
    out: Dict[str, Dict[str, Any]] = {}
    for raw in items:
        if not isinstance(raw, dict) or key not in raw:
            raise Lab003ConfigError("Each item must include '{0}'.".format(key))
        item_id = str(raw[key])
        if item_id in out:
            raise Lab003ConfigError("Duplicate id '{0}'.".format(item_id))
        out[item_id] = raw
    return out


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples"


def default_policy_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "policies"


def load_bundle(
    data_dir: Optional[Path] = None,
    policy_dir: Optional[Path] = None,
) -> Lab003Bundle:
    data = Path(data_dir) if data_dir else default_data_dir()
    policies_path = Path(policy_dir) if policy_dir else default_policy_dir()
    required = (
        "agents.yaml",
        "profiles.yaml",
        "posture.yaml",
        "delegations.yaml",
        "scenarios.yaml",
    )
    for name in required:
        if not (data / name).is_file():
            raise Lab003ConfigError("Missing example file: {0}".format(name))
    if not (policies_path / "access-policy.yaml").is_file():
        raise Lab003ConfigError("Missing policy file: access-policy.yaml")

    agents = _index_by_id(_read_yaml(data / "agents.yaml")["agents"], "agent_id")
    profiles = _index_by_id(_read_yaml(data / "profiles.yaml")["profiles"], "agent_id")
    posture = _index_by_id(_read_yaml(data / "posture.yaml")["posture"], "agent_id")
    delegations = _index_by_id(
        _read_yaml(data / "delegations.yaml")["delegations"], "delegation_id"
    )
    scenarios_raw = _read_yaml(data / "scenarios.yaml")["scenarios"]
    if not isinstance(scenarios_raw, list):
        raise Lab003ConfigError("scenarios must be a list.")
    scenarios: Dict[str, Dict[str, Any]] = {}
    for raw in scenarios_raw:
        sid = str(raw["id"])
        scenarios[sid] = raw

    policies = {"access": _read_yaml(policies_path / "access-policy.yaml")}
    return Lab003Bundle(
        agents=agents,
        profiles=profiles,
        posture=posture,
        delegations=delegations,
        scenarios=scenarios,
        policies=policies,
        data_dir=data,
    )


def materialize_scenario(
    bundle: Lab003Bundle, scenario_id: str
) -> tuple[
    Dict[str, Any],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    """Return (scenario, agents, profiles, posture, delegations) with overlays applied."""
    if scenario_id not in bundle.scenarios:
        raise KeyError(scenario_id)
    scenario = copy.deepcopy(bundle.scenarios[scenario_id])
    agents = copy.deepcopy(bundle.agents)
    profiles = copy.deepcopy(bundle.profiles)
    posture = copy.deepcopy(bundle.posture)
    delegations = copy.deepcopy(bundle.delegations)

    overlays = scenario.get("overlays") or {}
    for agent_id, patch in (overlays.get("agents") or {}).items():
        if agent_id not in agents:
            agents[agent_id] = {"agent_id": agent_id}
        agents[agent_id].update(patch)
    for agent_id, patch in (overlays.get("profiles") or {}).items():
        if agent_id not in profiles:
            profiles[agent_id] = {"agent_id": agent_id}
        profiles[agent_id].update(patch)
    for agent_id, patch in (overlays.get("posture") or {}).items():
        if agent_id not in posture:
            posture[agent_id] = {"agent_id": agent_id}
        posture[agent_id].update(patch)
    for delegation_id, patch in (overlays.get("delegations") or {}).items():
        if delegation_id not in delegations:
            delegations[delegation_id] = {"delegation_id": delegation_id}
        delegations[delegation_id].update(patch)
    for delegation_id in overlays.get("remove_delegations") or []:
        delegations.pop(delegation_id, None)
    for agent_id in overlays.get("remove_agents") or []:
        agents.pop(agent_id, None)
        profiles.pop(agent_id, None)
        posture.pop(agent_id, None)

    return scenario, agents, profiles, posture, delegations
