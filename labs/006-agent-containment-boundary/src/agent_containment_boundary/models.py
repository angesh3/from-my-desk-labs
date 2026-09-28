"""Typed models for Lab 006 agent containment boundary."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class BehaviorAssessment(str, Enum):
    justified_refusal = "JUSTIFIED_REFUSAL"
    needs_review = "NEEDS_REVIEW"
    non_compliant = "NON_COMPLIANT"
    rogue_behavior = "ROGUE_BEHAVIOR"


class EnforcementResponse(str, Enum):
    continue_ = "CONTINUE"
    restrict = "RESTRICT"
    isolate = "ISOLATE"
    terminate = "TERMINATE"


class EvidenceConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    conflicting = "conflicting"


class PotentialImpact(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class Reversibility(str, Enum):
    easily_reversible = "easily_reversible"
    partially_reversible = "partially_reversible"
    difficult_to_reverse = "difficult_to_reverse"
    irreversible = "irreversible"


class TimeSensitivity(str, Enum):
    low = "low"
    moderate = "moderate"
    urgent = "urgent"
    immediate_threat = "immediate_threat"


class CredentialState(str, Enum):
    valid = "valid"
    suspended = "suspended"
    revoked = "revoked"
    expired = "expired"


class ExecutionLeaseState(str, Enum):
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    expired = "expired"


class ReceiptChainStatus(str, Enum):
    preserved = "preserved"
    incomplete = "incomplete"
    broken = "broken"


class StopInstructionSource(str, Enum):
    none = "none"
    incident_commander = "incident_commander"
    unverified_operator = "unverified_operator"
    automated_alert = "automated_alert"
    peer_agent = "peer_agent"


MAX_TEXT = 500
MAX_ID = 120
MAX_LIST = 20


class EvaluateRequest(BaseModel):
    principal_identity: str = Field(min_length=1, max_length=MAX_ID)
    principal_role: str = Field(min_length=1, max_length=MAX_ID)
    principal_authority_valid: bool
    agent_identity: str = Field(min_length=1, max_length=MAX_ID)
    agent_owner: str = Field(min_length=1, max_length=MAX_ID)
    requested_action: str = Field(min_length=1, max_length=MAX_TEXT)
    stop_instruction_present: bool = False
    stop_instruction_source: StopInstructionSource = StopInstructionSource.none
    stop_instruction_authority_valid: bool = False
    stop_instruction_acknowledged: bool = False
    policy_id: str = Field(default="cq-containment-policy", max_length=MAX_ID)
    policy_version: str = Field(default="lab006-containment-v1", max_length=MAX_ID)
    policy_allows_requested_action: bool = True
    request_within_delegated_scope: bool = True
    safety_rule_triggered: bool = False
    evidence_confidence: EvidenceConfidence = EvidenceConfidence.medium
    potential_impact: PotentialImpact = PotentialImpact.moderate
    reversibility: Reversibility = Reversibility.partially_reversible
    time_sensitivity: TimeSensitivity = TimeSensitivity.moderate
    active_tool_sessions: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    active_sub_agents: List[str] = Field(default_factory=list, max_length=MAX_LIST)
    credential_state: CredentialState = CredentialState.valid
    execution_lease_state: ExecutionLeaseState = ExecutionLeaseState.active
    attempted_tool_switch: bool = False
    attempted_delegation_after_stop: bool = False
    attempted_use_after_revocation: bool = False
    continued_after_isolation: bool = False
    violation_count: int = Field(default=0, ge=0, le=50)
    receipt_chain_status: ReceiptChainStatus = ReceiptChainStatus.preserved
    agent_refused_request: bool = False
    agent_requested_clarification: bool = False
    agent_followed_stop: bool = False
    containment_already_applied: bool = False
    preset_id: Optional[str] = Field(default=None, max_length=MAX_ID)

    @field_validator("active_tool_sessions", "active_sub_agents")
    @classmethod
    def _trim_list(cls, values: List[str]) -> List[str]:
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
    behavior_assessment: Optional[BehaviorAssessment] = None
    instruction_compliance: Optional[bool] = None
    enforcement_response: EnforcementResponse
    reason_codes: List[str] = Field(default_factory=list)
    summary: str
    human_explanation: str
    authority_findings: List[str] = Field(default_factory=list)
    policy_findings: List[str] = Field(default_factory=list)
    behavior_findings: List[str] = Field(default_factory=list)
    containment_actions: List[str] = Field(default_factory=list)
    credentials_to_suspend: List[str] = Field(default_factory=list)
    tool_sessions_to_suspend: List[str] = Field(default_factory=list)
    sub_agents_to_terminate: List[str] = Field(default_factory=list)
    execution_lease_action: str = "none"
    evidence_to_preserve: List[str] = Field(default_factory=list)
    recovery_requirements: List[str] = Field(default_factory=list)
    containment_effective: bool = False
    receipt_chain_status: ReceiptChainStatus = ReceiptChainStatus.preserved
    execution: Literal["not_performed"] = "not_performed"
    policy_version: str = "lab006-containment-v1"
    preset_id: Optional[str] = None


class PresetMeta(BaseModel):
    id: str
    title: str
    short_description: str
    expected_behavior_assessment: Optional[BehaviorAssessment] = None
    expected_enforcement_response: EnforcementResponse
    category: str


class PresetDetail(PresetMeta):
    request: EvaluateRequest
