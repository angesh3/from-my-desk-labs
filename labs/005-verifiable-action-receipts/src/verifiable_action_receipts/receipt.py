"""Receipt generation rules for Lab 005."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from .hashing import calculate_receipt_hash, verify_receipt
from .models import (
    ActionReceipt,
    AuthorizationOutcome,
    ExecutionJudgment,
    ExecutionStatus,
    GenerateReceiptRequest,
    GenerateResponse,
    HumanInvolvement,
    IntegrityStatus,
    VerificationResult,
)

POLICY_VERSION = "lab005-receipt-v1"
SCHEMA_VERSION = "receipt.v1"


class ReceiptRuleError(ValueError):
    """Raised when a receipt cannot be generated under Lab 005 rules."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _resolve_execution_status(request: GenerateReceiptRequest) -> ExecutionStatus:
    """Decide whether a fictional tool action may be recorded as simulated."""
    if request.execution_judgment in {ExecutionJudgment.escalate, ExecutionJudgment.stop}:
        return ExecutionStatus.not_performed
    if request.authorization_outcome == AuthorizationOutcome.deny:
        return ExecutionStatus.not_performed
    if request.execution_judgment == ExecutionJudgment.clarify:
        return ExecutionStatus.not_performed
    if request.authorization_outcome == AuthorizationOutcome.confirm:
        if not (request.approval_reference or "").strip():
            raise ReceiptRuleError(
                "CONFIRM requires a fictional approval_reference before simulated execution."
            )
        if request.human_involvement not in {
            HumanInvolvement.approval,
            HumanInvolvement.modification,
        }:
            raise ReceiptRuleError(
                "CONFIRM with simulated execution requires human approval involvement."
            )
    if request.execution_judgment == ExecutionJudgment.proceed:
        if request.authorization_outcome in {
            AuthorizationOutcome.allow,
            AuthorizationOutcome.confirm,
            AuthorizationOutcome.step_up,
        }:
            if not (request.simulated_tool or "").strip():
                raise ReceiptRuleError(
                    "PROCEED with simulated execution requires a fictional tool name."
                )
            return ExecutionStatus.simulated
    return ExecutionStatus.not_performed


def generate_receipt(
    request: GenerateReceiptRequest,
    *,
    previous_receipt: Optional[ActionReceipt] = None,
) -> ActionReceipt:
    """Build a sealed action receipt from a validated request."""
    execution_status = _resolve_execution_status(request)
    previous_hash = (request.previous_receipt_hash or "").strip()
    if previous_receipt is not None and not previous_hash:
        previous_hash = previous_receipt.receipt_hash

    observed = (request.observed_outcome or "").strip()
    if execution_status == ExecutionStatus.not_performed and not observed:
        if request.execution_judgment == ExecutionJudgment.escalate:
            observed = "No tool action performed; case escalated for human decision."
        elif request.execution_judgment == ExecutionJudgment.clarify:
            observed = "No tool action performed; clarification requested."
        elif request.execution_judgment == ExecutionJudgment.stop:
            observed = "No tool action performed; agent stopped."
        elif request.authorization_outcome == AuthorizationOutcome.deny:
            observed = "No tool action performed; authorization denied."
        else:
            observed = "No tool action performed."

    explanation = (request.explanation or "").strip()
    if not explanation:
        explanation = (
            f"Authorization={request.authorization_outcome.value}; "
            f"execution_judgment={request.execution_judgment.value}; "
            f"execution_status={execution_status.value}."
        )

    receipt = ActionReceipt(
        schema_version=SCHEMA_VERSION,
        receipt_id=(request.receipt_id or _new_id("rcpt")),
        previous_receipt_hash=previous_hash,
        created_at=(request.created_at or _utc_now()),
        request_id=request.request_id.strip(),
        correlation_id=request.correlation_id.strip(),
        agent_identity=request.agent_identity.strip(),
        principal_identity=request.principal_identity.strip(),
        target_resource=request.target_resource.strip(),
        requested_action=request.requested_action.strip(),
        delegated_capability=request.delegated_capability.strip(),
        authority_source=request.authority_source.strip(),
        policy_id=request.policy_id.strip(),
        policy_version=(request.policy_version or POLICY_VERSION).strip(),
        authorization_outcome=request.authorization_outcome,
        execution_judgment=request.execution_judgment,
        evidence_references=list(request.evidence_references),
        evidence_summary=(request.evidence_summary or "").strip(),
        human_involvement=request.human_involvement,
        approval_reference=(request.approval_reference or "").strip(),
        original_request=(request.original_request or "").strip(),
        clarification_note=(request.clarification_note or "").strip(),
        simulated_tool=(request.simulated_tool or "").strip(),
        simulated_tool_action=(request.simulated_tool_action or "").strip(),
        execution_status=execution_status,
        observed_outcome=observed,
        reason_codes=list(request.reason_codes),
        explanation=explanation,
        receipt_hash="",
        integrity_status=IntegrityStatus.verified,
    )
    receipt.receipt_hash = calculate_receipt_hash(receipt)
    receipt.integrity_status = IntegrityStatus.verified
    return receipt


def _apply_tamper(receipt: ActionReceipt, field: str, value: str) -> ActionReceipt:
    data = receipt.model_dump(mode="json")
    if field not in data or field in {"receipt_hash", "integrity_status", "schema_version"}:
        raise ReceiptRuleError(f"Cannot tamper with field '{field}'.")
    data[field] = value
    tampered = ActionReceipt.model_validate(data)
    # Keep the original sealed hash so verification detects the change.
    tampered.receipt_hash = receipt.receipt_hash
    tampered.integrity_status = IntegrityStatus.tampered
    return tampered


def evaluate_request(
    request: GenerateReceiptRequest,
    *,
    previous_receipt: Optional[ActionReceipt] = None,
    follow_up_request: Optional[GenerateReceiptRequest] = None,
) -> GenerateResponse:
    """Generate one or more receipts and return verification results."""
    prior: Optional[ActionReceipt] = previous_receipt
    prior_verification: Optional[VerificationResult] = None

    if request.force_broken_chain:
        if prior is None:
            seed = request.model_copy(
                update={
                    "force_broken_chain": False,
                    "force_tamper_field": None,
                    "force_tamper_value": None,
                    "requested_action": "preserve_evidence",
                    "execution_judgment": ExecutionJudgment.proceed,
                    "authorization_outcome": AuthorizationOutcome.allow,
                    "simulated_tool": "cq-evidence-vault",
                    "simulated_tool_action": "preserve_case_bundle",
                    "observed_outcome": "Evidence bundle preserved (fictional).",
                    "receipt_id": _new_id("prior"),
                    "request_id": _new_id("req-prior"),
                }
            )
            prior = generate_receipt(seed)
        # Point at a hash that does not match the prior receipt.
        request = request.model_copy(
            update={
                "previous_receipt_hash": "0" * 64,
                "force_broken_chain": False,
            }
        )

    receipt = generate_receipt(request, previous_receipt=prior)

    if request.force_tamper_field and request.force_tamper_value is not None:
        receipt = _apply_tamper(
            receipt, request.force_tamper_field, request.force_tamper_value
        )

    verification = verify_receipt(receipt, previous_receipt=prior)
    receipt.integrity_status = verification.integrity_status

    if prior is not None:
        prior_verification = verify_receipt(prior)

    follow_up_receipt: Optional[ActionReceipt] = None
    follow_up_verification: Optional[VerificationResult] = None
    if follow_up_request is not None:
        linked = follow_up_request.model_copy(
            update={"previous_receipt_hash": receipt.receipt_hash}
        )
        # Clarification receipts use not_performed; follow-up may proceed.
        follow_up_receipt = generate_receipt(linked, previous_receipt=receipt)
        follow_up_verification = verify_receipt(
            follow_up_receipt, previous_receipt=receipt
        )
        follow_up_receipt.integrity_status = follow_up_verification.integrity_status

    explanation = receipt.explanation
    if verification.integrity_status != IntegrityStatus.verified:
        explanation = verification.explanation
    elif follow_up_receipt is not None:
        explanation = (
            "Clarification was recorded first without tool execution. "
            "A follow-up receipt then records the clarified authorized path."
        )

    return GenerateResponse(
        receipt=receipt,
        verification=verification,
        prior_receipt=prior,
        prior_verification=prior_verification,
        follow_up_receipt=follow_up_receipt,
        follow_up_verification=follow_up_verification,
        explanation=explanation,
        execution="not_performed",
        policy_version=POLICY_VERSION,
        preset_id=request.preset_id,
    )


def evaluate_preset_bundle(
    request: GenerateReceiptRequest,
    *,
    follow_up_request: Optional[GenerateReceiptRequest] = None,
    prior_receipt_seed: Optional[GenerateReceiptRequest] = None,
) -> GenerateResponse:
    prior = None
    if prior_receipt_seed is not None:
        prior = generate_receipt(prior_receipt_seed)
    return evaluate_request(
        request,
        previous_receipt=prior,
        follow_up_request=follow_up_request,
    )
