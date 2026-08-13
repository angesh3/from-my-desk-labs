import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_POLICY_DIR = Path(__file__).resolve().parent.parent / "policies"


def policy_dir() -> Path:
    override = os.environ.get("POLICY_DIR")
    if override:
        return Path(override)
    return DEFAULT_POLICY_DIR


def load_yaml(name: str) -> Dict[str, Any]:
    path = policy_dir() / name
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Policy file {0} must contain a mapping".format(name))
    return data


def load_registry() -> Dict[str, Any]:
    return load_yaml("agent-registry.yaml")


def load_desk_policy() -> Dict[str, Any]:
    return load_yaml("desk-policy.yaml")
