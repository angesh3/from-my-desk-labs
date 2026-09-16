"""Preset catalog loader for Lab 005."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import (
    AuthorizationOutcome,
    ExecutionJudgment,
    GenerateReceiptRequest,
    HumanInvolvement,
    IntegrityStatus,
    PresetDetail,
    PresetMeta,
)


class Lab005ConfigError(ValueError):
    """Raised when Lab 005 configuration cannot be loaded safely."""


def _enum(cls, value: str):
    try:
        return cls(value)
    except ValueError as exc:
        raise Lab005ConfigError(f"Invalid {cls.__name__} value: {value}") from exc


def _request_from_dict(raw: dict, preset_id: Optional[str] = None) -> GenerateReceiptRequest:
    return GenerateReceiptRequest(
        request_id=str(raw["request_id"]),
        correlation_id=str(raw["correlation_id"]),
        agent_identity=str(raw["agent_identity"]),
        principal_identity=str(raw["principal_identity"]),
        target_resource=str(raw["target_resource"]),
        requested_action=str(raw["requested_action"]),
        delegated_capability=str(raw["delegated_capability"]),
        authority_source=str(raw.get("authority_source") or "cq-delegation-register"),
        policy_id=str(raw.get("policy_id") or "cq-soc-response-policy"),
        policy_version=str(raw.get("policy_version") or "lab005-receipt-v1"),
        authorization_outcome=_enum(AuthorizationOutcome, raw["authorization_outcome"]),
        execution_judgment=_enum(ExecutionJudgment, raw["execution_judgment"]),
        evidence_references=list(raw.get("evidence_references") or []),
        evidence_summary=str(raw.get("evidence_summary") or ""),
        human_involvement=_enum(
            HumanInvolvement, raw.get("human_involvement") or "none"
        ),
        approval_reference=str(raw.get("approval_reference") or ""),
        original_request=str(raw.get("original_request") or ""),
        clarification_note=str(raw.get("clarification_note") or ""),
        simulated_tool=str(raw.get("simulated_tool") or ""),
        simulated_tool_action=str(raw.get("simulated_tool_action") or ""),
        observed_outcome=str(raw.get("observed_outcome") or ""),
        reason_codes=list(raw.get("reason_codes") or []),
        explanation=str(raw.get("explanation") or ""),
        previous_receipt_hash=str(raw.get("previous_receipt_hash") or ""),
        created_at=raw.get("created_at"),
        receipt_id=raw.get("receipt_id"),
        force_tamper_field=raw.get("force_tamper_field"),
        force_tamper_value=raw.get("force_tamper_value"),
        force_broken_chain=bool(raw.get("force_broken_chain", False)),
        preset_id=preset_id,
    )


class Lab005Bundle:
    def __init__(self, presets: Dict[str, PresetDetail], policy_version: str) -> None:
        self.presets = presets
        self.policy_version = policy_version

    def preset_meta(self) -> List[PresetMeta]:
        return [
            PresetMeta(
                id=item.id,
                title=item.title,
                short_description=item.short_description,
                expected_execution_judgment=item.expected_execution_judgment,
                expected_integrity=item.expected_integrity,
                category=item.category,
            )
            for item in self.presets.values()
        ]


def load_bundle(data_dir: Path, policy_dir: Path) -> Lab005Bundle:
    presets_path = data_dir / "presets.yaml"
    policy_path = policy_dir / "receipt-policy.yaml"
    if not presets_path.is_file():
        raise Lab005ConfigError("Lab 005 presets.yaml is missing.")
    if not policy_path.is_file():
        raise Lab005ConfigError("Lab 005 receipt-policy.yaml is missing.")
    try:
        presets_raw = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        policy_raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab005ConfigError("Lab 005 YAML is invalid.") from exc
    if not isinstance(presets_raw, dict) or "presets" not in presets_raw:
        raise Lab005ConfigError("presets.yaml must contain a presets list.")
    version = str((policy_raw or {}).get("policy_version") or "lab005-receipt-v1")
    presets: Dict[str, PresetDetail] = {}
    for item in presets_raw["presets"]:
        if not isinstance(item, dict):
            raise Lab005ConfigError("Each preset must be a mapping.")
        preset_id = str(item["id"])
        request = _request_from_dict(dict(item["request"]), preset_id=preset_id)
        follow_up = None
        if item.get("follow_up_request"):
            follow_up = _request_from_dict(
                dict(item["follow_up_request"]), preset_id=preset_id
            )
        prior_seed = None
        if item.get("prior_receipt_seed"):
            prior_seed = _request_from_dict(
                dict(item["prior_receipt_seed"]), preset_id=preset_id
            )
        presets[preset_id] = PresetDetail(
            id=preset_id,
            title=str(item["title"]),
            short_description=str(item["short_description"]),
            expected_execution_judgment=_enum(
                ExecutionJudgment, item["expected_execution_judgment"]
            ),
            expected_integrity=_enum(IntegrityStatus, item["expected_integrity"]),
            category=str(item.get("category") or "general"),
            request=request,
            follow_up_request=follow_up,
            prior_receipt_seed=prior_seed,
        )
    if len(presets) < 5:
        raise Lab005ConfigError("Lab 005 requires at least five presets.")
    return Lab005Bundle(presets=presets, policy_version=version)
