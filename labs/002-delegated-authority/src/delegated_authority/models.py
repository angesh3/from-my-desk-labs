"""Typed models for Lab 002 delegated-authority evaluation."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Decision = Literal["allow", "confirm", "step_up", "deny"]
IdentityStatus = Literal["valid", "invalid", "unknown"]
AgentLifecycle = Literal["active", "suspended", "revoked", "unknown"]
PrincipalBinding = Literal["valid", "invalid"]
ChainStatus = Literal["valid", "broken", "expired", "revoked", "constraint_violation"]
ProfileStatus = Literal["known", "unknown", "conflicting"]
Confidence = Literal["high", "medium", "low"]
PostureStatus = Literal["compliant", "noncompliant", "unknown", "stale"]
RiskLevel = Literal["low", "medium", "high"]
EvidenceFreshness = Literal["current", "stale", "missing"]
FallbackType = Literal[
    "none",
    "register_agent",
    "collect_profile",
    "refresh_posture",
    "request_human_review",
    "request_new_delegation",
    "request_narrower_action",
    "correct_delegation",
    "correct_delegation_period",
    "request_direct_delegation",
    "upgrade_version",
    "restore_approved_configuration",
    "investigate_tool_change",
]
ReasonCategory = Literal[
    "policy_satisfied",
    "business_confirmation",
    "assurance_required",
    "identity_failure",
    "delegation_failure",
    "profile_risk",
    "posture_risk",
    "lifecycle_failure",
    "system_failure",
]

REASON_CODES = frozenset(
    {
        "policy_satisfied",
        "confirmation_threshold",
        "unusual_context",
        "posture_evidence_stale",
        "identity_invalid",
        "agent_unknown",
        "principal_mismatch",
        "parent_expired",
        "parent_revoked",
        "capability_not_delegated",
        "child_capability_exceeds_parent",
        "child_resource_exceeds_parent",
        "child_limit_exceeds_parent",
        "child_expiry_exceeds_parent",
        "redelegation_prohibited",
        "delegation_depth_exceeded",
        "delegation_chain_broken",
        "profile_mismatch",
        "model_version_noncompliant",
        "tool_inventory_changed",
        "runtime_compromised",
        "policy_unavailable",
        "audit_unavailable",
        "invalid_request",
    }
)

DECISION_RANK = {"deny": 0, "step_up": 1, "confirm": 2, "allow": 3}


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


class ActionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: str = Field(..., min_length=1, max_length=64)
    principal_id: str = Field(..., min_length=1, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=64)
    requested_capability: str = Field(..., min_length=1, max_length=64)
    requested_resource: str = Field(..., min_length=1, max_length=64)
    requested_amount: Decimal
    request_time: str = Field(..., min_length=1, max_length=64)
    delegation_id: str = Field(..., min_length=1, max_length=64)
    context: str = Field(default="normal", max_length=64)
    assurance_level: str = Field(default="standard", max_length=32)

    @field_validator("requested_amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        amount = as_decimal(value)
        if amount < 0:
            raise ValueError("requested_amount must be non-negative.")
        return amount


class DelegationEnvelope(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    delegation_id: str
    parent_delegation_id: Optional[str] = None
    principal_id: str
    delegator_id: str
    delegate_id: str
    capabilities: List[str]
    resources: List[str]
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
    effective_limit: Optional[str] = None
    effective_expiry: Optional[str] = None
    redelegation_allowed: bool = False
    violated_constraint: Optional[str] = None
    chain_version: str = "1"
    reason_code: Optional[str] = None


class DeclaredAttributes(BaseModel):
    agent_type: str
    model: str
    tools: List[str]
    declared_capabilities: List[str]
    owner: str


class ObservedAttributes(BaseModel):
    typical_data_access: List[str]
    typical_tool_usage: List[str]
    typical_action_types: List[str]
    typical_operating_period: str
    observed_execution_behavior: str


class VerifiedAttributes(BaseModel):
    signed_manifest: bool
    approved_software_version: str
    attested_runtime: bool
    registered_environment: str
    verified_tool_inventory: List[str]


class AgentProfile(BaseModel):
    agent_id: str
    classification: str
    declared_attributes: DeclaredAttributes
    observed_attributes: ObservedAttributes
    verified_attributes: VerifiedAttributes
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
    configuration_integrity: str
    tool_inventory_status: str
    attestation_status: str
    credential_status: str
    behavior_status: str
    evidence_freshness: EvidenceFreshness
    recommended_treatment: Literal[
        "continue", "confirm", "step_up", "deny", "restricted_fallback"
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


class FallbackRecommendation(BaseModel):
    available: bool = False
    fallback_type: FallbackType = "none"
    explanation: str = ""
    permitted_operations: List[str] = Field(default_factory=list)
    prohibited_operations: List[str] = Field(default_factory=list)
    new_evaluation_required: bool = True


class JourneyStep(BaseModel):
    stage: str
    status: str
    summary: str


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
    fallback: FallbackRecommendation
    execution: Literal["not_performed"] = "not_performed"
    journey: List[JourneyStep] = Field(default_factory=list)
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


class AuditRecord(BaseModel):
    audit_id: str
    request_id: str
    timestamp: str
    principal_reference: str
    agent_reference: str
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
    fallback_offered: str
    execution: Literal["not_performed"] = "not_performed"
