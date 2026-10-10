"""Typed models for Lab 007 containment assurance."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AttemptedEnforcement(str, Enum):
    restrict = "RESTRICT"
    isolate = "ISOLATE"
    terminate = "TERMINATE"


class AssuranceStatus(str, Enum):
    confirmed = "CONFIRMED"
    partial = "PARTIAL"
    unverified = "UNVERIFIED"
    failed = "FAILED"


class CheckOutcome(str, Enum):
    pass_ = "pass"
    fail = "fail"
    missing = "missing"


class EvidenceFreshness(str, Enum):
    fresh = "fresh"
    stale = "stale"
    unknown = "unknown"


class EvidenceSource(str, Enum):
    independent_control_plane = "independent_control_plane"
    agent_self_report = "agent_self_report"
    partial_telemetry = "partial_telemetry"
    none = "none"


REQUIRED_CHECK_IDS = (
    "primary_runtime_stopped",
    "active_sessions_revoked",
    "delegated_credentials_revoked",
    "tool_access_disabled",
    "queued_actions_cancelled",
    "scheduled_work_cancelled",
    "child_agents_stopped",
    "network_egress_blocked",
    "alternate_network_paths_checked",
    "persistent_state_quarantined",
    "restart_recovery_disabled",
    "telemetry_coverage_complete",
    "evidence_freshness_acceptable",
    "evidence_source_independence",
    "post_containment_activity_absent",
)

MAX_ID = 120
MAX_TEXT = 500
MAX_LIST = 30
MAX_CHECKS = 30


class AssuranceCheck(BaseModel):
    check_id: str = Field(min_length=1, max_length=MAX_ID)
    expected_state: str = Field(min_length=1, max_length=MAX_TEXT)
    observed_state: str = Field(min_length=1, max_length=MAX_TEXT)
    evidence_reference: Optional[str] = Field(default=None, max_length=MAX_ID)
    evidence_freshness: EvidenceFreshness = EvidenceFreshness.unknown
    evidence_source: EvidenceSource = EvidenceSource.none
    reason: Optional[str] = Field(default=None, max_length=MAX_TEXT)


class EvaluateRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=MAX_ID)
    correlation_id: str = Field(min_length=1, max_length=MAX_ID)
    agent_id: str = Field(min_length=1, max_length=MAX_ID)
    principal_id: str = Field(min_length=1, max_length=MAX_ID)
    attempted_enforcement: AttemptedEnforcement
    evaluated_at: str = Field(min_length=1, max_length=MAX_ID)
    evidence_window_minutes: int = Field(default=15, ge=1, le=1440)
    checks: List[AssuranceCheck] = Field(min_length=1, max_length=MAX_CHECKS)
    post_containment_activity: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    containment_regression_detected: bool = False
    agent_self_report_stopped: bool = False
    preset_id: Optional[str] = Field(default=None, max_length=MAX_ID)

    @field_validator("post_containment_activity")
    @classmethod
    def _trim_activity(cls, values: List[str]) -> List[str]:
        cleaned: List[str] = []
        for item in values:
            text = str(item).strip()[:MAX_TEXT]
            if text:
                cleaned.append(text)
            if len(cleaned) >= MAX_LIST:
                break
        return cleaned

    @field_validator("checks")
    @classmethod
    def _validate_checks(cls, values: List[AssuranceCheck]) -> List[AssuranceCheck]:
        if not values:
            raise ValueError("At least one assurance check is required.")
        ids = [item.check_id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate check_id values are not allowed.")
        return values


class EvaluatedCheck(BaseModel):
    check_id: str
    expected_state: str
    observed_state: str
    evidence_reference: Optional[str] = None
    evidence_freshness: EvidenceFreshness
    evidence_source: EvidenceSource
    check_result: CheckOutcome
    reason: str


class EvaluateResponse(BaseModel):
    evaluation_id: str
    preset_id: Optional[str] = None
    request_id: str
    correlation_id: str
    agent_id: str
    principal_id: str
    attempted_enforcement: AttemptedEnforcement
    assurance_status: AssuranceStatus
    containment_effective: bool
    evaluated_at: str
    evidence_window_minutes: int
    checks: List[EvaluatedCheck] = Field(default_factory=list)
    passed_checks: List[str] = Field(default_factory=list)
    failed_checks: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    residual_paths: List[str] = Field(default_factory=list)
    post_containment_activity: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    explanation: str
    summary: str
    execution: Literal["not_performed"] = "not_performed"
    policy_version: str = "lab007-assurance-v1"


class PresetMeta(BaseModel):
    id: str
    title: str
    short_description: str
    expected_assurance_status: AssuranceStatus
    category: str


class PresetDetail(PresetMeta):
    request: EvaluateRequest
