"""Preset catalog loader for Lab 006."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import (
    BehaviorAssessment,
    CredentialState,
    EnforcementResponse,
    EvaluateRequest,
    EvidenceConfidence,
    ExecutionLeaseState,
    PotentialImpact,
    PresetDetail,
    PresetMeta,
    ReceiptChainStatus,
    Reversibility,
    StopInstructionSource,
    TimeSensitivity,
)


class Lab006ConfigError(ValueError):
    """Raised when Lab 006 configuration cannot be loaded safely."""


def _enum(cls, value):
    if value is None:
        return None
    try:
        return cls(value)
    except ValueError as exc:
        raise Lab006ConfigError(f"Invalid {cls.__name__} value: {value}") from exc


def _request_from_dict(raw: dict, preset_id: Optional[str] = None) -> EvaluateRequest:
    return EvaluateRequest(
        principal_identity=str(raw["principal_identity"]),
        principal_role=str(raw["principal_role"]),
        principal_authority_valid=bool(raw["principal_authority_valid"]),
        agent_identity=str(raw["agent_identity"]),
        agent_owner=str(raw["agent_owner"]),
        requested_action=str(raw["requested_action"]),
        stop_instruction_present=bool(raw.get("stop_instruction_present", False)),
        stop_instruction_source=_enum(
            StopInstructionSource, raw.get("stop_instruction_source") or "none"
        ),
        stop_instruction_authority_valid=bool(
            raw.get("stop_instruction_authority_valid", False)
        ),
        stop_instruction_acknowledged=bool(
            raw.get("stop_instruction_acknowledged", False)
        ),
        policy_id=str(raw.get("policy_id") or "cq-containment-policy"),
        policy_version=str(raw.get("policy_version") or "lab006-containment-v1"),
        policy_allows_requested_action=bool(
            raw.get("policy_allows_requested_action", True)
        ),
        request_within_delegated_scope=bool(
            raw.get("request_within_delegated_scope", True)
        ),
        safety_rule_triggered=bool(raw.get("safety_rule_triggered", False)),
        evidence_confidence=_enum(
            EvidenceConfidence, raw.get("evidence_confidence") or "medium"
        ),
        potential_impact=_enum(
            PotentialImpact, raw.get("potential_impact") or "moderate"
        ),
        reversibility=_enum(
            Reversibility, raw.get("reversibility") or "partially_reversible"
        ),
        time_sensitivity=_enum(
            TimeSensitivity, raw.get("time_sensitivity") or "moderate"
        ),
        active_tool_sessions=list(raw.get("active_tool_sessions") or []),
        active_sub_agents=list(raw.get("active_sub_agents") or []),
        credential_state=_enum(
            CredentialState, raw.get("credential_state") or "valid"
        ),
        execution_lease_state=_enum(
            ExecutionLeaseState, raw.get("execution_lease_state") or "active"
        ),
        attempted_tool_switch=bool(raw.get("attempted_tool_switch", False)),
        attempted_delegation_after_stop=bool(
            raw.get("attempted_delegation_after_stop", False)
        ),
        attempted_use_after_revocation=bool(
            raw.get("attempted_use_after_revocation", False)
        ),
        continued_after_isolation=bool(raw.get("continued_after_isolation", False)),
        violation_count=int(raw.get("violation_count") or 0),
        receipt_chain_status=_enum(
            ReceiptChainStatus, raw.get("receipt_chain_status") or "preserved"
        ),
        agent_refused_request=bool(raw.get("agent_refused_request", False)),
        agent_requested_clarification=bool(
            raw.get("agent_requested_clarification", False)
        ),
        agent_followed_stop=bool(raw.get("agent_followed_stop", False)),
        containment_already_applied=bool(
            raw.get("containment_already_applied", False)
        ),
        preset_id=preset_id,
    )


class Lab006Bundle:
    def __init__(self, presets: Dict[str, PresetDetail], policy_version: str) -> None:
        self.presets = presets
        self.policy_version = policy_version

    def preset_meta(self) -> List[PresetMeta]:
        return [
            PresetMeta(
                id=item.id,
                title=item.title,
                short_description=item.short_description,
                expected_behavior_assessment=item.expected_behavior_assessment,
                expected_enforcement_response=item.expected_enforcement_response,
                category=item.category,
            )
            for item in self.presets.values()
        ]


def load_bundle(data_dir: Path, policy_dir: Path) -> Lab006Bundle:
    presets_path = data_dir / "presets.yaml"
    policy_path = policy_dir / "containment-policy.yaml"
    if not presets_path.is_file():
        raise Lab006ConfigError("Lab 006 presets.yaml is missing.")
    if not policy_path.is_file():
        raise Lab006ConfigError("Lab 006 containment-policy.yaml is missing.")
    try:
        presets_raw = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        policy_raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab006ConfigError("Lab 006 YAML is invalid.") from exc
    if not isinstance(presets_raw, dict) or "presets" not in presets_raw:
        raise Lab006ConfigError("presets.yaml must contain a presets list.")
    version = str((policy_raw or {}).get("policy_version") or "lab006-containment-v1")
    presets: Dict[str, PresetDetail] = {}
    for item in presets_raw["presets"]:
        if not isinstance(item, dict):
            raise Lab006ConfigError("Each preset must be a mapping.")
        preset_id = str(item["id"])
        expected_behavior = item.get("expected_behavior_assessment")
        presets[preset_id] = PresetDetail(
            id=preset_id,
            title=str(item["title"]),
            short_description=str(item["short_description"]),
            expected_behavior_assessment=_enum(BehaviorAssessment, expected_behavior)
            if expected_behavior
            else None,
            expected_enforcement_response=_enum(
                EnforcementResponse, item["expected_enforcement_response"]
            ),
            category=str(item.get("category") or "general"),
            request=_request_from_dict(dict(item["request"]), preset_id=preset_id),
        )
    if len(presets) < 8:
        raise Lab006ConfigError("Lab 006 requires at least eight presets.")
    return Lab006Bundle(presets=presets, policy_version=version)
