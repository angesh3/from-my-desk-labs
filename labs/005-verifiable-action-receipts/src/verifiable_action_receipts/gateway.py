"""Lab 005 receipt API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from .loader import Lab005Bundle, Lab005ConfigError, load_bundle
from .models import (
    GenerateReceiptRequest,
    GenerateResponse,
    PresetDetail,
    PresetMeta,
    VerificationResult,
    VerifyRequest,
)
from .receipt import ReceiptRuleError
from .service import evaluate_preset, generate_from_request, list_presets, verify_request

router = APIRouter()
_bundle: Optional[Lab005Bundle] = None


def data_dir() -> Path:
    override = os.environ.get("LAB005_DATA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "examples"


def policy_dir() -> Path:
    override = os.environ.get("LAB005_POLICY_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "policies"


def get_lab005_bundle() -> Lab005Bundle:
    global _bundle
    if _bundle is None:
        _bundle = load_bundle(data_dir(), policy_dir())
    return _bundle


def reset_lab005_bundle() -> None:
    global _bundle
    _bundle = None


@router.get("/api/labs/005/presets", response_model=List[PresetMeta])
def presets() -> List[PresetMeta]:
    try:
        return list_presets(get_lab005_bundle())
    except Lab005ConfigError as exc:
        raise HTTPException(
            status_code=500, detail="Lab 005 configuration unavailable."
        ) from exc


@router.get("/api/labs/005/presets/{preset_id}", response_model=PresetDetail)
def preset_detail(preset_id: str) -> PresetDetail:
    bundle = get_lab005_bundle()
    if preset_id not in bundle.presets:
        raise HTTPException(
            status_code=404,
            detail={
                "reason_code": "invalid_request",
                "reason": "Unknown preset.",
                "execution": "not_performed",
            },
        )
    return bundle.presets[preset_id]


@router.post("/api/labs/005/generate", response_model=GenerateResponse)
def generate(payload: GenerateReceiptRequest) -> GenerateResponse:
    try:
        return generate_from_request(payload)
    except ReceiptRuleError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "reason_code": "invalid_request",
                "reason": str(exc),
                "execution": "not_performed",
            },
        ) from exc
    except Lab005ConfigError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "policy_unavailable",
                "reason": "Lab 005 policy data is unavailable.",
                "execution": "not_performed",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "invalid_request",
                "reason": "The service could not complete this evaluation.",
                "execution": "not_performed",
            },
        ) from exc


@router.post("/api/labs/005/verify", response_model=VerificationResult)
def verify(payload: VerifyRequest) -> VerificationResult:
    try:
        return verify_request(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "invalid_request",
                "reason": "The service could not verify this receipt.",
                "execution": "not_performed",
            },
        ) from exc


@router.post("/api/labs/005/evaluate-preset/{preset_id}", response_model=GenerateResponse)
def evaluate_named_preset(preset_id: str) -> GenerateResponse:
    bundle = get_lab005_bundle()
    if preset_id not in bundle.presets:
        raise HTTPException(
            status_code=404,
            detail={
                "reason_code": "invalid_request",
                "reason": "Unknown preset.",
                "execution": "not_performed",
            },
        )
    try:
        return evaluate_preset(bundle, preset_id)
    except ReceiptRuleError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "reason_code": "invalid_request",
                "reason": str(exc),
                "execution": "not_performed",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "invalid_request",
                "reason": "The service could not complete this evaluation.",
                "execution": "not_performed",
            },
        ) from exc
