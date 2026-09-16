"""Typed models for Lab 005 verifiable action receipts."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AuthorizationOutcome(str, Enum):
    allow = "allow"
    confirm = "confirm"
    step_up = "step_up"
    deny = "deny"


class ExecutionJudgment(str, Enum):
    proceed = "proceed"
    clarify = "clarify"
    escalate = "escalate"
    stop = "stop"


class IntegrityStatus(str, Enum):
    verified = "verified"
    tampered = "tampered"
    chain_broken = "chain_broken"


class ExecutionStatus(str, Enum):
    """Fictional tool execution status recorded on the receipt."""

    simulated = "simulated"
    not_performed = "not_performed"


class HumanInvolvement(str, Enum):
    none = "none"
    clarification = "clarification"
    approval = "approval"
    modification = "modification"
    rejection = "rejection"
    escalation = "escalation"


MAX_TEXT = 500
MAX_ID = 120
MAX_LIST_ITEMS = 12


class GenerateReceiptRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=MAX_ID)
    correlation_id: str = Field(min_length=1, max_length=MAX_ID)
    agent_identity: str = Field(min_length=1, max_length=MAX_ID)
    principal_identity: str = Field(min_length=1, max_length=MAX_ID)
    target_resource: str = Field(min_length=1, max_length=MAX_TEXT)
    requested_action: str = Field(min_length=1, max_length=MAX_TEXT)
    delegated_capability: str = Field(min_length=1, max_length=MAX_TEXT)
    authority_source: str = Field(default="cq-delegation-register", max_length=MAX_TEXT)
    policy_id: str = Field(default="cq-soc-response-policy", max_length=MAX_ID)
    policy_version: str = Field(default="lab005-receipt-v1", max_length=MAX_ID)
    authorization_outcome: AuthorizationOutcome
    execution_judgment: ExecutionJudgment
    evidence_references: List[str] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    evidence_summary: str = Field(default="", max_length=MAX_TEXT)
    human_involvement: HumanInvolvement = HumanInvolvement.none
    approval_reference: str = Field(default="", max_length=MAX_ID)
    original_request: str = Field(default="", max_length=MAX_TEXT)
    clarification_note: str = Field(default="", max_length=MAX_TEXT)
    simulated_tool: str = Field(default="", max_length=MAX_TEXT)
    simulated_tool_action: str = Field(default="", max_length=MAX_TEXT)
    observed_outcome: str = Field(default="", max_length=MAX_TEXT)
    reason_codes: List[str] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    explanation: str = Field(default="", max_length=2000)
    previous_receipt_hash: str = Field(default="", max_length=128)
    created_at: Optional[str] = Field(default=None, max_length=64)
    receipt_id: Optional[str] = Field(default=None, max_length=MAX_ID)
    force_tamper_field: Optional[str] = Field(default=None, max_length=64)
    force_tamper_value: Optional[str] = Field(default=None, max_length=MAX_TEXT)
    force_broken_chain: bool = False
    preset_id: Optional[str] = Field(default=None, max_length=MAX_ID)

    @field_validator("evidence_references", "reason_codes")
    @classmethod
    def _trim_list_items(cls, values: List[str]) -> List[str]:
        cleaned: List[str] = []
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            cleaned.append(text[:MAX_TEXT])
            if len(cleaned) >= MAX_LIST_ITEMS:
                break
        return cleaned


class ActionReceipt(BaseModel):
    schema_version: str = "receipt.v1"
    receipt_id: str
    previous_receipt_hash: str = ""
    created_at: str
    request_id: str
    correlation_id: str
    agent_identity: str
    principal_identity: str
    target_resource: str
    requested_action: str
    delegated_capability: str
    authority_source: str
    policy_id: str
    policy_version: str
    authorization_outcome: AuthorizationOutcome
    execution_judgment: ExecutionJudgment
    evidence_references: List[str] = Field(default_factory=list)
    evidence_summary: str = ""
    human_involvement: HumanInvolvement = HumanInvolvement.none
    approval_reference: str = ""
    original_request: str = ""
    clarification_note: str = ""
    simulated_tool: str = ""
    simulated_tool_action: str = ""
    execution_status: ExecutionStatus
    observed_outcome: str = ""
    reason_codes: List[str] = Field(default_factory=list)
    explanation: str = ""
    receipt_hash: str = ""
    integrity_status: IntegrityStatus = IntegrityStatus.verified


class VerificationResult(BaseModel):
    integrity_status: IntegrityStatus
    content_match: bool
    chain_match: bool
    expected_hash: str
    stored_hash: str
    failures: List[str] = Field(default_factory=list)
    explanation: str


class PresetMeta(BaseModel):
    id: str
    title: str
    short_description: str
    expected_execution_judgment: ExecutionJudgment
    expected_integrity: IntegrityStatus
    category: str


class PresetDetail(PresetMeta):
    request: GenerateReceiptRequest
    follow_up_request: Optional[GenerateReceiptRequest] = None
    prior_receipt_seed: Optional[GenerateReceiptRequest] = None


class GenerateResponse(BaseModel):
    receipt: ActionReceipt
    verification: VerificationResult
    prior_receipt: Optional[ActionReceipt] = None
    prior_verification: Optional[VerificationResult] = None
    follow_up_receipt: Optional[ActionReceipt] = None
    follow_up_verification: Optional[VerificationResult] = None
    explanation: str
    execution: Literal["not_performed"] = "not_performed"
    policy_version: str
    preset_id: Optional[str] = None


class VerifyRequest(BaseModel):
    receipt: ActionReceipt
    previous_receipt: Optional[ActionReceipt] = None
