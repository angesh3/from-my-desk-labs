"""Typed models for Lab 003 agent access control evaluation."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Decision = Literal["allow", "confirm", "step_up", "deny"]
IdentityStatus = Literal["valid", "invalid", "unknown"]
AgentLifecycle = Literal["active", "suspended", "revoked", "unknown"]
RegistrationState = Literal["registered", "unknown", "unmanaged"]
PrincipalBinding = Literal["valid", "invalid"]
ChainStatus = Literal["valid", "broken", "expired", "revoked", "constraint_violation"]
ProfileStatus = Literal["known", "unknown", "conflicting"]
Confidence = Literal["high", "medium", "low"]
PostureStatus = Literal["compliant", "noncompliant", "unknown", "stale"]
RiskLevel = Literal["low", "medium", "high"]
EvidenceFreshness = Literal["current", "stale", "missing"]
RestrictedType = Literal[
    "none",
    "register_agent",
    "collect_profile",
    "refresh_posture",
    "request_human_review",
    "request_new_delegation",
    "upgrade_version",
    "investigate_tool_change",
    "request_consent",
    "context_review",
]
ReasonCategory = Literal[
    "policy_satisfied",
    "business_confirmation",
    "assurance_required",
    "identity_failure",
    "delegation_failure",
    "profile_risk",
    "posture_risk",
    "resource_failure",
    "purpose_failure",
    "lifecycle_failure",
    "restricted_recovery",
    "system_failure",
]

REASON_CODES = frozenset(
    {
        "within_current_authority",
        "human_consent_required",
        "posture_evidence_stale",
        "model_version_noncompliant",
        "capability_not_delegated",
        "unknown_agent_protected_action",
        "restricted_registration_permitted",
        "tool_inventory_changed",
        "data_classification_exceeds_authority",
        "parent_delegation_expired",
        "parent_delegation_revoked",
        "purpose_not_permitted",
        "limit_requires_confirmation",
        "context_change_requires_step_up",
        "identity_invalid",
        "principal_mismatch",
        "agent_unknown",
        "delegation_chain_broken",
        "profile_mismatch",
        "invalid_request",
        "policy_unavailable",
        "audit_unavailable",
    }
)

DECISION_RANK = {"deny": 0, "step_up": 1, "confirm": 2, "allow": 3}

HARD_DENY_CODES = frozenset(
    {
        "capability_not_delegated",
        "unknown_agent_protected_action",
        "tool_inventory_changed",
        "data_classification_exceeds_authority",
        "parent_delegation_expired",
        "parent_delegation_revoked",
        "purpose_not_permitted",
        "identity_invalid",
        "principal_mismatch",
        "agent_unknown",
        "delegation_chain_broken",
    }
)


def as_decimal(value: object) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Amount must be a decimal number.") from exc
    if not amount.is_finite():
        raise ValueError("Amount must be a finite decimal number.")
    return amount


def worse_decision(left: Decision, right: Decision) -> Decision:
    """Return the more restrictive decision (DENY > STEP_UP > CONFIRM > ALLOW)."""
    if DECISION_RANK[left] <= DECISION_RANK[right]:
        return left
    return right


class AccessRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: str = Field(..., min_length=1, max_length=64)
    principal_id: str = Field(..., min_length=1, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=64)
    requested_action: str = Field(..., min_length=1, max_length=64)
    requested_tool: str = Field(..., min_length=1, max_length=64)
    requested_resource: str = Field(..., min_length=1, max_length=64)
    data_classification: str = Field(..., min_length=1, max_length=32)
    requested_amount: Decimal
    stated_purpose: str = Field(..., min_length=1, max_length=128)
    request_time: str = Field(..., min_length=1, max_length=64)
    delegation_id: str = Field(..., min_length=1, max_length=64)
    context: str = Field(default="normal", max_length=64)
    assurance_level: str = Field(default="standard", max_length=32)
    restricted_operation: bool = False

    @field_validator("requested_amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        amount = as_decimal(value)
        if amount < 0:
            raise ValueError("requested_amount must be non-negative.")
        return amount


class EvaluationFragment(BaseModel):
    """Partial evaluation outcome from a single evaluator stage."""

    stage: str
    outcome: Literal["satisfied", "failed", "warning", "skipped", "restricted"]
    decision_signal: Optional[Decision] = None
    reason_code: Optional[str] = None
    hard_authority_failure: bool = False
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationEvent(BaseModel):
    event_type: str
    status: Literal["completed", "skipped"]
    timestamp: str
    summary: str
    skip_reason: Optional[str] = None
    fragment: Optional[EvaluationFragment] = None


class DelegationEnvelope(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    delegation_id: str
    parent_delegation_id: Optional[str] = None
    principal_id: str
    delegator_id: str
    delegate_id: str
    capabilities: List[str]
    resources: List[str]
    permitted_purposes: List[str]
    maximum_data_classification: str
    maximum_amount: Decimal
    valid_from: str
    valid_until: str
    may_redelegate: bool
    remaining_depth: int = Field(..., ge=0)
    required_assurance: str = "standard"
    status: Literal["active", "expired", "revoked"] = "active"
    version: str = "1"

    @field_validator("maximum_amount", mode="before")
    @classmethod
    def parse_limit(cls, value: object) -> Decimal:
        return as_decimal(value)


class IdentityResult(BaseModel):
    identity_status: IdentityStatus
    agent_status: AgentLifecycle
    principal_binding: PrincipalBinding
    assurance_level: str
    evaluated_at: str
    reason_code: Optional[str] = None


class DelegationResult(BaseModel):
    chain_status: ChainStatus
    chain_path: List[str]
    effective_capabilities: List[str]
    effective_resources: List[str]
    effective_purposes: List[str]
    effective_data_classification: Optional[str] = None
    effective_limit: Optional[str] = None
    effective_expiry: Optional[str] = None
    redelegation_allowed: bool = False
    violated_constraint: Optional[str] = None
    chain_version: str = "1"
    reason_code: Optional[str] = None


class AgentProfile(BaseModel):
    agent_id: str
    classification: str
    expected_capabilities: List[str]
    expected_tools: List[str]
    management_status: str
    confidence: Confidence
    profile_mismatch: bool = False
    profile_status: ProfileStatus = "known"
    profile_version: str = "1"
    evaluated_at: str = ""


class PostureEvidence(BaseModel):
    agent_id: str
    posture_status: PostureStatus
    risk_level: RiskLevel
    model_version_status: str
    tool_inventory_status: str
    attestation_status: str
    evidence_freshness: EvidenceFreshness
    recommended_treatment: Literal[
        "continue", "confirm", "step_up", "deny", "restricted_recovery"
    ] = "continue"
    posture_version: str = "1"
    evaluated_at: str = ""
    reason_code: Optional[str] = None


class ProfileSummary(BaseModel):
    classification: str
    confidence: Confidence
    profile_mismatch: bool
    profile_status: ProfileStatus = "known"


class PostureSummary(BaseModel):
    status: PostureStatus
    evidence_freshness: EvidenceFreshness
    risk_level: RiskLevel = "low"


class RestrictedRecommendation(BaseModel):
    available: bool = False
    restricted_type: RestrictedType = "none"
    explanation: str = ""
    permitted_operations: List[str] = Field(default_factory=list)
    prohibited_operations: List[str] = Field(default_factory=list)
    new_evaluation_required: bool = True


class AuditRecord(BaseModel):
    audit_id: str
    request_id: str
    timestamp: str
    principal_reference: str
    agent_reference: str
    registration_state: str
    delegation_chain_reference: str
    delegation_chain_version: str
    ape_profile_status: str
    ape_profile_version: str
    apse_posture_status: str
    apse_posture_version: str
    evidence_freshness: str
    policy_version: str
    decision: Decision
    reason_code: str
    restricted_path_offered: str
    execution: Literal["not_performed"] = "not_performed"


class EvaluationResult(BaseModel):
    decision: Decision
    reason_code: str
    reason_category: ReasonCategory
    explanation: str
    violated_constraint: Optional[str] = None
    delegation_path: List[str] = Field(default_factory=list)
    profile_summary: ProfileSummary
    posture_summary: PostureSummary
    audit_id: str
    evaluated_at: str
    decision_valid_until: Optional[str] = None
    restricted: RestrictedRecommendation
    execution: Literal["not_performed"] = "not_performed"
    events: List[EvaluationEvent] = Field(default_factory=list)
    request_fingerprint: Optional[str] = None
    chain_version: Optional[str] = None
    profile_version: Optional[str] = None
    posture_version: Optional[str] = None
    policy_version: Optional[str] = None
    scenario_id: Optional[str] = None


class ScenarioEvaluateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    scenario_id: str = Field(..., min_length=1, max_length=64)


class ScenarioMeta(BaseModel):
    id: str
    title: str
    short_description: str
    category: str
    expected_decision: Decision
