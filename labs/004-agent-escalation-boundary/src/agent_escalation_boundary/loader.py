"""Preset catalog and policy loader for Lab 004."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import (
    AuthorizationOutcome,
    EvidenceConfidence,
    EvaluateRequest,
    ExecutionOutcome,
    GoalClarity,
    HumanAvailability,
    PolicyCoverage,
    PotentialImpact,
    PresetDetail,
    PresetMeta,
    Reversibility,
    TimeSensitivity,
)


class Lab004ConfigError(ValueError):
    """Raised when Lab 004 configuration cannot be loaded safely."""


def _enum(cls, value: str):
    try:
        return cls(value)
    except ValueError as exc:
        raise Lab004ConfigError(f"Invalid {cls.__name__} value: {value}") from exc


def _request_from_dict(raw: dict) -> EvaluateRequest:
    return EvaluateRequest(
        goal_clarity=_enum(GoalClarity, raw["goal_clarity"]),
        evidence_confidence=_enum(EvidenceConfidence, raw["evidence_confidence"]),
        potential_impact=_enum(PotentialImpact, raw["potential_impact"]),
        reversibility=_enum(Reversibility, raw["reversibility"]),
        policy_coverage=_enum(PolicyCoverage, raw["policy_coverage"]),
        time_sensitivity=_enum(TimeSensitivity, raw["time_sensitivity"]),
        human_availability=_enum(HumanAvailability, raw["human_availability"]),
        authorization_outcome=_enum(AuthorizationOutcome, raw["authorization_outcome"]),
        agent_id=str(raw["agent_id"]),
        principal_id=str(raw["principal_id"]),
        requested_action=str(raw["requested_action"]),
        target_account=str(raw["target_account"]),
        delegated_capability=str(raw["delegated_capability"]),
        business_context=str(raw.get("business_context") or ""),
        confirmation_satisfied=bool(raw.get("confirmation_satisfied", False)),
        stronger_auth_completed=bool(raw.get("stronger_auth_completed", False)),
        preset_id=str(raw["id"]) if raw.get("id") else None,
    )


class Lab004Bundle:
    def __init__(self, presets: Dict[str, PresetDetail], policy_version: str) -> None:
        self.presets = presets
        self.policy_version = policy_version

    def preset_meta(self) -> List[PresetMeta]:
        return [
            PresetMeta(
                id=item.id,
                title=item.title,
                short_description=item.short_description,
                expected_execution_outcome=item.expected_execution_outcome,
                category=item.category,
            )
            for item in self.presets.values()
        ]


def load_bundle(data_dir: Path, policy_dir: Path) -> Lab004Bundle:
    presets_path = data_dir / "presets.yaml"
    policy_path = policy_dir / "escalation-policy.yaml"
    if not presets_path.is_file():
        raise Lab004ConfigError("Lab 004 presets.yaml is missing.")
    if not policy_path.is_file():
        raise Lab004ConfigError("Lab 004 escalation-policy.yaml is missing.")
    try:
        presets_raw = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        policy_raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab004ConfigError("Lab 004 YAML is invalid.") from exc
    if not isinstance(presets_raw, dict) or "presets" not in presets_raw:
        raise Lab004ConfigError("presets.yaml must contain a presets list.")
    version = str((policy_raw or {}).get("policy_version") or "lab004-escalation-v1")
    presets: Dict[str, PresetDetail] = {}
    for item in presets_raw["presets"]:
        if not isinstance(item, dict):
            raise Lab004ConfigError("Each preset must be a mapping.")
        preset_id = str(item["id"])
        request_data = dict(item["request"])
        request = _request_from_dict(request_data)
        request = request.model_copy(update={"preset_id": preset_id})
        presets[preset_id] = PresetDetail(
            id=preset_id,
            title=str(item["title"]),
            short_description=str(item["short_description"]),
            expected_execution_outcome=_enum(
                ExecutionOutcome, item["expected_execution_outcome"]
            ),
            category=str(item.get("category") or "general"),
            request=request,
        )
    if len(presets) < 5:
        raise Lab004ConfigError("Lab 004 requires at least five presets.")
    return Lab004Bundle(presets=presets, policy_version=version)
