"""Preset catalog loader for Lab 008."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import (
    ControlCategory,
    ControlCoverage,
    ControlItem,
    ControlStatus,
    EvaluateRequest,
    Impact,
    Likelihood,
    PresetDetail,
    PresetMeta,
    RiskLevel,
    ThreatSurface,
)


class Lab008ConfigError(ValueError):
    """Raised when Lab 008 configuration cannot be loaded safely."""


def _enum(cls, value):
    if value is None:
        return None
    try:
        return cls(value)
    except ValueError as exc:
        raise Lab008ConfigError(f"Invalid {cls.__name__} value: {value}") from exc


def _control(raw: dict) -> ControlItem:
    return ControlItem(
        control_id=str(raw["control_id"]),
        name=str(raw["name"]),
        category=_enum(ControlCategory, raw["category"]),
        expected_behavior=str(raw["expected_behavior"]),
        evidence_reference=raw.get("evidence_reference"),
        status=_enum(ControlStatus, raw.get("status") or "UNKNOWN"),
    )


def _request_from_dict(raw: dict, preset_id: Optional[str] = None) -> EvaluateRequest:
    secondary = [
        _enum(ThreatSurface, item) for item in (raw.get("secondary_surfaces") or [])
    ]
    return EvaluateRequest(
        case_id=str(raw["case_id"]),
        title=str(raw["title"]),
        description=str(raw["description"]),
        agent_identity=str(raw["agent_identity"]),
        principal_identity=str(raw["principal_identity"]),
        environment=str(raw.get("environment") or "Cedar Quill Markets fictional lab"),
        policy_version=str(raw.get("policy_version") or "lab008-threat-model-v1"),
        asset_name=str(raw["asset_name"]),
        asset_type=str(raw["asset_type"]),
        asset_sensitivity=str(raw["asset_sensitivity"]),
        security_objective=str(raw["security_objective"]),
        threat_source=str(raw["threat_source"]),
        failure_mode=str(raw["failure_mode"]),
        primary_surface=_enum(ThreatSurface, raw["primary_surface"]),
        secondary_surfaces=secondary,
        trust_boundary=str(raw["trust_boundary"]),
        preconditions=list(raw.get("preconditions") or []),
        threat_path=list(raw.get("threat_path") or []),
        potential_impact=str(raw["potential_impact"]),
        initial_likelihood=_enum(Likelihood, raw["initial_likelihood"]),
        initial_impact=_enum(Impact, raw["initial_impact"]),
        preventive_controls=[
            _control(item) for item in (raw.get("preventive_controls") or [])
        ],
        detective_controls=[
            _control(item) for item in (raw.get("detective_controls") or [])
        ],
        containment_controls=[
            _control(item) for item in (raw.get("containment_controls") or [])
        ],
        recovery_controls=[
            _control(item) for item in (raw.get("recovery_controls") or [])
        ],
        evidence_sources=list(raw.get("evidence_sources") or []),
        evidence_summary=str(raw.get("evidence_summary") or ""),
        evidence_gaps=list(raw.get("evidence_gaps") or []),
        observation_window=str(raw.get("observation_window") or "15m"),
        agent_self_report_present=bool(raw.get("agent_self_report_present", False)),
        independent_evidence_sufficient=bool(
            raw.get("independent_evidence_sufficient", True)
        ),
        residual_likelihood=_enum(Likelihood, raw.get("residual_likelihood"))
        if raw.get("residual_likelihood")
        else None,
        residual_impact=_enum(Impact, raw.get("residual_impact"))
        if raw.get("residual_impact")
        else None,
        preset_id=preset_id,
    )


class Lab008Bundle:
    def __init__(self, presets: Dict[str, PresetDetail], policy_version: str) -> None:
        self.presets = presets
        self.policy_version = policy_version

    def preset_meta(self) -> List[PresetMeta]:
        return [
            PresetMeta(
                id=item.id,
                title=item.title,
                short_description=item.short_description,
                primary_surface=item.primary_surface,
                expected_initial_risk=item.expected_initial_risk,
                expected_control_coverage=item.expected_control_coverage,
                expected_residual_risk=item.expected_residual_risk,
                category=item.category,
            )
            for item in self.presets.values()
        ]


def load_bundle(data_dir: Path, policy_dir: Path) -> Lab008Bundle:
    presets_path = data_dir / "presets.yaml"
    policy_path = policy_dir / "threat-model-policy.yaml"
    if not presets_path.is_file():
        raise Lab008ConfigError("Lab 008 presets.yaml is missing.")
    if not policy_path.is_file():
        raise Lab008ConfigError("Lab 008 threat-model-policy.yaml is missing.")
    try:
        presets_raw = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        policy_raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Lab008ConfigError("Lab 008 YAML is invalid.") from exc
    if not isinstance(presets_raw, dict) or "presets" not in presets_raw:
        raise Lab008ConfigError("presets.yaml must contain a presets list.")
    version = str((policy_raw or {}).get("policy_version") or "lab008-threat-model-v1")
    presets: Dict[str, PresetDetail] = {}
    for item in presets_raw["presets"]:
        if not isinstance(item, dict):
            raise Lab008ConfigError("Each preset must be a mapping.")
        preset_id = str(item["id"])
        request = _request_from_dict(dict(item["request"]), preset_id=preset_id)
        presets[preset_id] = PresetDetail(
            id=preset_id,
            title=str(item["title"]),
            short_description=str(item["short_description"]),
            primary_surface=request.primary_surface,
            expected_initial_risk=_enum(RiskLevel, item["expected_initial_risk"]),
            expected_control_coverage=_enum(
                ControlCoverage, item["expected_control_coverage"]
            ),
            expected_residual_risk=_enum(RiskLevel, item["expected_residual_risk"]),
            category=str(item.get("category") or "general"),
            request=request,
        )
    if len(presets) < 8:
        raise Lab008ConfigError("Lab 008 requires at least eight presets.")
    return Lab008Bundle(presets=presets, policy_version=version)
