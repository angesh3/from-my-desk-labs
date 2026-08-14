"""Load and validate fictional registry and policy YAML."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import as_decimal


class PolicyConfigError(ValueError):
    """Raised when policy or registry files cannot be used safely."""


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    display_name: str
    status: str
    principal_id: str
    capabilities: List[str]
    accounts: List[str]
    valid_from: datetime
    valid_until: datetime
    revoked: bool
    policy_id: str


@dataclass(frozen=True)
class DeskPolicy:
    policy_id: str
    organization: str
    allowed_tickers: List[str]
    restricted_tickers: List[str]
    allow_max: Decimal
    confirm_max: Decimal
    step_up_max: Decimal


@dataclass(frozen=True)
class PolicyBundle:
    registry_organization: str
    policy: DeskPolicy
    agents: Dict[str, AgentRecord]


def _read_mapping(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise PolicyConfigError("Required policy file is missing.")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise PolicyConfigError("Policy file is not valid YAML.") from exc
    if not isinstance(data, dict):
        raise PolicyConfigError("Policy file must contain a mapping.")
    return data


def _parse_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PolicyConfigError("Agent field '{0}' must be an ISO-8601 timestamp.".format(field))
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise PolicyConfigError("Agent field '{0}' is not a valid timestamp.".format(field)) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _require_str(data: Dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PolicyConfigError("Missing required string field '{0}'.".format(field))
    return value.strip()


def _require_list(data: Dict[str, Any], field: str) -> List[Any]:
    value = data.get(field)
    if not isinstance(value, list):
        raise PolicyConfigError("Field '{0}' must be a list.".format(field))
    return value


def parse_agent(raw: Any) -> AgentRecord:
    if not isinstance(raw, dict):
        raise PolicyConfigError("Each agent must be a mapping.")
    agent_id = _require_str(raw, "agent_id")
    status = _require_str(raw, "status")
    if status not in {"active", "inactive"}:
        raise PolicyConfigError("Agent '{0}' has an invalid status.".format(agent_id))
    capabilities = [str(item).strip() for item in _require_list(raw, "capabilities")]
    accounts = [str(item).strip() for item in _require_list(raw, "accounts")]
    return AgentRecord(
        agent_id=agent_id,
        display_name=_require_str(raw, "display_name"),
        status=status,
        principal_id=_require_str(raw, "principal_id"),
        capabilities=capabilities,
        accounts=accounts,
        valid_from=_parse_datetime(raw.get("valid_from"), "valid_from"),
        valid_until=_parse_datetime(raw.get("valid_until"), "valid_until"),
        revoked=bool(raw.get("revoked", False)),
        policy_id=_require_str(raw, "policy_id"),
    )


def parse_desk_policy(raw: Dict[str, Any]) -> DeskPolicy:
    policy_id = _require_str(raw, "policy_id")
    organization = _require_str(raw, "organization")
    allowed = [str(item).strip().upper() for item in _require_list(raw, "allowed_tickers")]
    restricted = [str(item).strip().upper() for item in _require_list(raw, "restricted_tickers")]
    if not allowed:
        raise PolicyConfigError("allowed_tickers must not be empty.")
    if len(set(allowed)) != len(allowed):
        raise PolicyConfigError("allowed_tickers contains duplicates.")
    thresholds = raw.get("thresholds")
    if not isinstance(thresholds, dict):
        raise PolicyConfigError("thresholds must be a mapping.")
    try:
        allow_max = as_decimal(thresholds.get("allow_max"))
        confirm_max = as_decimal(thresholds.get("confirm_max"))
        step_up_max = as_decimal(thresholds.get("step_up_max"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PolicyConfigError("Thresholds must be decimal amounts.") from exc
    if not (Decimal("0") < allow_max < confirm_max < step_up_max):
        raise PolicyConfigError(
            "Thresholds must satisfy 0 < allow_max < confirm_max < step_up_max."
        )
    return DeskPolicy(
        policy_id=policy_id,
        organization=organization,
        allowed_tickers=allowed,
        restricted_tickers=restricted,
        allow_max=allow_max,
        confirm_max=confirm_max,
        step_up_max=step_up_max,
    )


def load_bundle(policy_dir: Path) -> PolicyBundle:
    registry_raw = _read_mapping(policy_dir / "agent-registry.yaml")
    policy_raw = _read_mapping(policy_dir / "desk-policy.yaml")
    policy = parse_desk_policy(policy_raw)
    organization = _require_str(registry_raw, "organization")
    registry_policy_id = _require_str(registry_raw, "policy_id")
    if registry_policy_id != policy.policy_id:
        raise PolicyConfigError("Registry policy_id does not match desk policy_id.")
    agents_raw = _require_list(registry_raw, "agents")
    agents: Dict[str, AgentRecord] = {}
    for item in agents_raw:
        record = parse_agent(item)
        if record.agent_id in agents:
            raise PolicyConfigError("Duplicate agent_id '{0}'.".format(record.agent_id))
        if record.policy_id != policy.policy_id:
            raise PolicyConfigError(
                "Agent '{0}' policy_id does not match the desk policy.".format(record.agent_id)
            )
        if record.valid_from >= record.valid_until:
            raise PolicyConfigError(
                "Agent '{0}' valid_from must be earlier than valid_until.".format(record.agent_id)
            )
        agents[record.agent_id] = record
    if not agents:
        raise PolicyConfigError("Registry must contain at least one agent.")
    return PolicyBundle(
        registry_organization=organization,
        policy=policy,
        agents=agents,
    )


def sanitized_registry(bundle: PolicyBundle) -> Dict[str, Any]:
    return {
        "organization": bundle.policy.organization,
        "policy_id": bundle.policy.policy_id,
        "note": (
            "Sanitized demo view. Internal authority windows, revocation flags, "
            "and principal bindings are not published."
        ),
        "agents": [
            {
                "agent_id": agent.agent_id,
                "display_name": agent.display_name,
                "status": agent.status,
            }
            for agent in bundle.agents.values()
        ],
        "fictional_tickers": list(bundle.policy.allowed_tickers),
        "restricted_tickers": list(bundle.policy.restricted_tickers),
    }
