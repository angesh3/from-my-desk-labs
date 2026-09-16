"""Service helpers for Lab 005."""

from __future__ import annotations

from typing import List

from .hashing import (
    calculate_receipt_hash,
    canonicalize_receipt,
    verify_receipt,
)
from .loader import Lab005Bundle
from .models import (
    ActionReceipt,
    GenerateReceiptRequest,
    GenerateResponse,
    PresetMeta,
    VerificationResult,
    VerifyRequest,
)
from .receipt import evaluate_preset_bundle, evaluate_request, generate_receipt


def list_presets(bundle: Lab005Bundle) -> List[PresetMeta]:
    return bundle.preset_meta()


def generate_from_request(request: GenerateReceiptRequest) -> GenerateResponse:
    return evaluate_request(request)


def evaluate_preset(bundle: Lab005Bundle, preset_id: str) -> GenerateResponse:
    preset = bundle.presets[preset_id]
    payload = preset.request.model_copy(update={"preset_id": preset_id})
    follow_up = None
    if preset.follow_up_request is not None:
        follow_up = preset.follow_up_request.model_copy(update={"preset_id": preset_id})
    prior_seed = None
    if preset.prior_receipt_seed is not None:
        prior_seed = preset.prior_receipt_seed.model_copy(update={"preset_id": preset_id})
    return evaluate_preset_bundle(
        payload,
        follow_up_request=follow_up,
        prior_receipt_seed=prior_seed,
    )


def verify_request(payload: VerifyRequest) -> VerificationResult:
    return verify_receipt(payload.receipt, previous_receipt=payload.previous_receipt)


# Public names expected by the Lab brief.
__all__ = [
    "generate_receipt",
    "canonicalize_receipt",
    "calculate_receipt_hash",
    "verify_receipt",
    "evaluate_preset",
    "generate_from_request",
    "list_presets",
    "verify_request",
    "ActionReceipt",
    "GenerateReceiptRequest",
    "GenerateResponse",
]
