"""Typed models for Lab 008 agent threat model."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ThreatSurface(str, Enum):
    identity = "IDENTITY"
    authority = "AUTHORITY"
    instructions = "INSTRUCTIONS"
    memory_context = "MEMORY_CONTEXT"
    tools_execution = "TOOLS_EXECUTION"
    delegation = "DELEGATION"
    evidence_control = "EVIDENCE_CONTROL"


class Likelihood(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"


class Impact(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class RiskLevel(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"
    unknown = "UNKNOWN"


class ControlStatus(str, Enum):
    present = "PRESENT"
    missing = "MISSING"
    ineffective = "INEFFECTIVE"
    unknown = "UNKNOWN"


class ControlCoverage(str, Enum):
    complete = "COMPLETE"
    partial = "PARTIAL"
    none = "NONE"
    unverified = "UNVERIFIED"


class ControlCategory(str, Enum):
    preventive = "preventive"
    detective = "detective"
    containment = "containment"
    recovery = "recovery"


MAX_ID = 120
MAX_TEXT = 800
MAX_LIST = 30


class ControlItem(BaseModel):
    control_id: str = Field(min_length=1, max_length=MAX_ID)
    name: str = Field(min_length=1, max_length=MAX_TEXT)
    category: ControlCategory
    expected_behavior: str = Field(min_length=1, max_length=MAX_TEXT)
    evidence_reference: Optional[str] = Field(default=None, max_length=MAX_ID)
    status: ControlStatus = ControlStatus.unknown


class EvaluateRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=MAX_ID)
    title: str = Field(min_length=1, max_length=MAX_TEXT)
    description: str = Field(min_length=1, max_length=MAX_TEXT)
    agent_identity: str = Field(min_length=1, max_length=MAX_ID)
    principal_identity: str = Field(min_length=1, max_length=MAX_ID)
    environment: str = Field(min_length=1, max_length=MAX_TEXT)
    policy_version: str = Field(default="lab008-threat-model-v1", max_length=MAX_ID)

    asset_name: str = Field(min_length=1, max_length=MAX_TEXT)
    asset_type: str = Field(min_length=1, max_length=MAX_ID)
    asset_sensitivity: str = Field(min_length=1, max_length=MAX_ID)
    security_objective: str = Field(min_length=1, max_length=MAX_TEXT)

    threat_source: str = Field(min_length=1, max_length=MAX_TEXT)
    failure_mode: str = Field(min_length=1, max_length=MAX_TEXT)
    primary_surface: ThreatSurface
    secondary_surfaces: List[ThreatSurface] = Field(default_factory=list, max_length=MAX_LIST)
    trust_boundary: str = Field(min_length=1, max_length=MAX_TEXT)
    preconditions: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    threat_path: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    potential_impact: str = Field(min_length=1, max_length=MAX_TEXT)

    initial_likelihood: Likelihood
    initial_impact: Impact

    preventive_controls: List[ControlItem] = Field(default_factory=list, max_length=MAX_LIST)
    detective_controls: List[ControlItem] = Field(default_factory=list, max_length=MAX_LIST)
    containment_controls: List[ControlItem] = Field(default_factory=list, max_length=MAX_LIST)
    recovery_controls: List[ControlItem] = Field(default_factory=list, max_length=MAX_LIST)

    evidence_sources: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    evidence_summary: str = Field(default="", max_length=MAX_TEXT)
    evidence_gaps: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    observation_window: str = Field(default="15m", max_length=MAX_ID)
    agent_self_report_present: bool = False
    independent_evidence_sufficient: bool = True

    residual_likelihood: Optional[Likelihood] = None
    residual_impact: Optional[Impact] = None
    preset_id: Optional[str] = Field(default=None, max_length=MAX_ID)

    @field_validator("secondary_surfaces")
    @classmethod
    def _normalize_surfaces(cls, values: List) -> List[ThreatSurface]:
        cleaned: List[ThreatSurface] = []
        for item in values:
            if isinstance(item, ThreatSurface):
                cleaned.append(item)
            else:
                cleaned.append(ThreatSurface(str(item).strip()))
            if len(cleaned) >= MAX_LIST:
                break
        return cleaned

    @field_validator(
        "preconditions",
        "threat_path",
        "evidence_sources",
        "evidence_gaps",
    )
    @classmethod
    def _trim_str_list(cls, values: List) -> List[str]:
        cleaned: List[str] = []
        for item in values:
            text = str(item).strip()[:MAX_TEXT]
            if text:
                cleaned.append(text)
            if len(cleaned) >= MAX_LIST:
                break
        return cleaned


class EvaluateResponse(BaseModel):
    evaluation_id: str
    case_id: str
    preset_id: Optional[str] = None
    title: str
    primary_surface: ThreatSurface
    secondary_surfaces: List[ThreatSurface] = Field(default_factory=list)
    initial_likelihood: Likelihood
    initial_impact: Impact
    initial_risk: RiskLevel
    control_coverage: ControlCoverage
    residual_likelihood: Optional[Likelihood] = None
    residual_impact: Optional[Impact] = None
    residual_risk: RiskLevel
    residual_risk_explanation: str
    material_gaps: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    summary: str
    explanation: str
    preventive_controls: List[ControlItem] = Field(default_factory=list)
    detective_controls: List[ControlItem] = Field(default_factory=list)
    containment_controls: List[ControlItem] = Field(default_factory=list)
    recovery_controls: List[ControlItem] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    execution: Literal["not_performed"] = "not_performed"
    policy_version: str = "lab008-threat-model-v1"


class PresetMeta(BaseModel):
    id: str
    title: str
    short_description: str
    primary_surface: ThreatSurface
    expected_initial_risk: RiskLevel
    expected_control_coverage: ControlCoverage
    expected_residual_risk: RiskLevel
    category: str


class PresetDetail(PresetMeta):
    request: EvaluateRequest
