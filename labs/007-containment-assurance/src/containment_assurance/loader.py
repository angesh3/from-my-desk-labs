"""Preset catalog loader for Lab 007."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import (
    AssuranceCheck,
    AssuranceStatus,
    AttemptedEnforcement,
    EvaluateRequest,
    EvidenceFreshness,
    EvidenceSource,
    PresetDetail,
    PresetMeta,
)


class Lab007ConfigError(ValueError):
    """Raised when Lab 007 configuration cannot be loaded safely."""


def _enum(cls, value):
    if value is None:
        return None
    try:
        return cls(value)
    except ValueError as exc:
        raise Lab007ConfigError(f"Invalid {cls.__name__} value: {value}") from exc


def _check_from_dict(raw: dict) -> AssuranceCheck:
    return AssuranceCheck(
        check_id=str(raw["check_id"]),
        expected_state=str(raw["expected_state"]),
        observed_state=str(raw["observed_state"]),
        evidence_reference=raw.get("evidence_reference"),
        evidence_freshness=_enum(
            EvidenceFreshness, raw.get("evidence_freshness") or "unknown"
        ),
        evidence_source=_enum(
            EvidenceSource, raw.get("evidence_source") or "none"
        ),
        reason=raw.get("reason"),
    )


def _request_from_dict(raw: dict, preset_id: Optional[str] = None) -> EvaluateRequest:
    checks_raw = raw.get("checks") or []
    if not isinstance(checks_raw, list) or not checks_raw:
        raise Lab007ConfigError("Each preset request must include checks.")
    return EvaluateRequest(
        request_id=str(raw["request_id"]),
        correlation_id=str(raw["correlation_id"]),
        agent_id=str(raw["agent_id"]),
        principal_id=str(raw["principal_id"]),
        attempted_enforcement=_enum(
            AttemptedEnforcement, raw["attempted_enforcement"]
        ),
        evaluated_at=str(raw.get("evaluated_at") or "2026-10-10T18:00:00Z"),
        evidence_window_minutes=int(raw.get("evidence_window_minutes") or 15),
        checks=[_check_from_dict(item) for item in checks_raw],
        post_containment_activity=list(raw.get("post_containment_activity") or []),
        containment_regression_detected=bool(
            raw.get("containment_regression_detected", False)
        ),
        agent_self_report_stopped=bool(raw.get("agent_self_report_stopped", False)),
        preset_id=preset_id,
    )


class Lab007Bundle:
    def __init__(self, presets: Dict[str, PresetDetail], policy_version: str) -> None:
        self.presets = presets
        self.policy_version = policy_version

    def preset_meta(self) -> List[PresetMeta]:
        return [
            PresetMeta(
                id=item.id,
                title=item.title,
                short_description=item.short_description,
                expected_assurance_status=item.expected_assurance_status,
                category=item.category,
            )
            for item in self.presets.values()
        ]


def load_bundle(data_dir: Path, policy_dir: Path) -> Lab007Bundle:
    presets_path = data_dir / "presets.yaml"
    policy_path = policy_dir / "assurance-policy.yaml"
    if not presets_path.is_file():
        raise Lab007ConfigError("Lab 007 presets.yaml is missing.")
    if not policy_path.is_file():
        raise Lab007ConfigError("Lab 007 assurance-policy.yaml is missing.")
    try:
        presets_raw = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        policy_raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab007ConfigError("Lab 007 YAML is invalid.") from exc
    if not isinstance(presets_raw, dict) or "presets" not in presets_raw:
        raise Lab007ConfigError("presets.yaml must contain a presets list.")
    version = str((policy_raw or {}).get("policy_version") or "lab007-assurance-v1")
    presets: Dict[str, PresetDetail] = {}
    for item in presets_raw["presets"]:
        if not isinstance(item, dict):
            raise Lab007ConfigError("Each preset must be a mapping.")
        preset_id = str(item["id"])
        presets[preset_id] = PresetDetail(
            id=preset_id,
            title=str(item["title"]),
            short_description=str(item["short_description"]),
            expected_assurance_status=_enum(
                AssuranceStatus, item["expected_assurance_status"]
            ),
            category=str(item.get("category") or "general"),
            request=_request_from_dict(dict(item["request"]), preset_id=preset_id),
        )
    if len(presets) < 8:
        raise Lab007ConfigError("Lab 007 requires at least eight presets.")
    return Lab007Bundle(presets=presets, policy_version=version)
