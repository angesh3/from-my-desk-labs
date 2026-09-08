"""Request and response models for Lab 004 execution judgment."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AuthorizationOutcome(str, Enum):
    allow = "allow"
    confirm = "confirm"
    step_up = "step_up"
    deny = "deny"


class ExecutionOutcome(str, Enum):
    proceed = "proceed"
    clarify = "clarify"
    escalate = "escalate"
    stop = "stop"


class GoalClarity(str, Enum):
    clear = "clear"
    partially_clear = "partially_clear"
    ambiguous = "ambiguous"


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


class PolicyCoverage(str, Enum):
    explicitly_covered = "explicitly_covered"
    partially_covered = "partially_covered"
    not_covered = "not_covered"
    prohibited = "prohibited"


class TimeSensitivity(str, Enum):
    low = "low"
    moderate = "moderate"
    urgent = "urgent"
    immediate_threat = "immediate_threat"


class HumanAvailability(str, Enum):
    available_now = "available_now"
    available_shortly = "available_shortly"
    delayed = "delayed"
    unavailable = "unavailable"


class EvaluateRequest(BaseModel):
    goal_clarity: GoalClarity
    evidence_confidence: EvidenceConfidence
    potential_impact: PotentialImpact
    reversibility: Reversibility
    policy_coverage: PolicyCoverage
    time_sensitivity: TimeSensitivity
    human_availability: HumanAvailability
    authorization_outcome: AuthorizationOutcome
    agent_id: str = Field(min_length=1, max_length=120)
    principal_id: str = Field(min_length=1, max_length=120)
    requested_action: str = Field(min_length=1, max_length=200)
    target_account: str = Field(min_length=1, max_length=200)
    delegated_capability: str = Field(min_length=1, max_length=200)
    business_context: str = Field(default="", max_length=2000)
    confirmation_satisfied: bool = False
    stronger_auth_completed: bool = False
    preset_id: Optional[str] = Field(default=None, max_length=80)


class TriggeredRule(BaseModel):
    rule_id: str
    outcome: ExecutionOutcome
    summary: str


class BoundedAction(BaseModel):
    available: bool = False
    actions: List[str] = Field(default_factory=list)
    explanation: str = ""
    expands_authority: bool = False


class EvaluateResponse(BaseModel):
    authorization_outcome: AuthorizationOutcome
    execution_outcome: ExecutionOutcome
    decision_id: str
    evaluated_at: str
    explanation: str
    evidence_assessment: str
    triggered_rules: List[TriggeredRule]
    why_paused_or_proceeded: str
    missing_or_conflicting_evidence: List[str]
    impact_of_acting: str
    impact_of_waiting: str
    safe_actions_permitted: List[str]
    actions_requiring_approval: List[str]
    recommended_next_step: str
    escalation_destination: Optional[str] = None
    authority_chain_summary: str
    bounded_protective_action: BoundedAction
    execution: str = "not_performed"
    policy_version: str
    preset_id: Optional[str] = None


class PresetMeta(BaseModel):
    id: str
    title: str
    short_description: str
    expected_execution_outcome: ExecutionOutcome
    category: str


class PresetDetail(PresetMeta):
    request: EvaluateRequest
