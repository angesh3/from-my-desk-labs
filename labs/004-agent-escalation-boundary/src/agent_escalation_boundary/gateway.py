"""Lab 004 evaluation API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from .loader import Lab004Bundle, Lab004ConfigError, load_bundle
from .models import EvaluateRequest, EvaluateResponse, PresetDetail, PresetMeta
from .service import evaluate_preset, evaluate_request, list_presets

router = APIRouter()
_bundle: Optional[Lab004Bundle] = None


def data_dir() -> Path:
    override = os.environ.get("LAB004_DATA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "examples"


def policy_dir() -> Path:
    override = os.environ.get("LAB004_POLICY_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "policies"


def get_lab004_bundle() -> Lab004Bundle:
    global _bundle
    if _bundle is None:
        _bundle = load_bundle(data_dir(), policy_dir())
    return _bundle


def reset_lab004_bundle() -> None:
    global _bundle
    _bundle = None


@router.get("/api/labs/004/presets", response_model=List[PresetMeta])
def presets() -> List[PresetMeta]:
    try:
        return list_presets(get_lab004_bundle())
    except Lab004ConfigError as exc:
        raise HTTPException(
            status_code=500, detail="Lab 004 configuration unavailable."
        ) from exc


@router.get("/api/labs/004/presets/{preset_id}", response_model=PresetDetail)
def preset_detail(preset_id: str) -> PresetDetail:
    bundle = get_lab004_bundle()
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


@router.post("/api/labs/004/evaluate", response_model=EvaluateResponse)
def evaluate(payload: EvaluateRequest) -> EvaluateResponse:
    try:
        return evaluate_request(payload)
    except Lab004ConfigError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "policy_unavailable",
                "reason": "Lab 004 policy data is unavailable.",
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


@router.post("/api/labs/004/evaluate-preset/{preset_id}", response_model=EvaluateResponse)
def evaluate_named_preset(preset_id: str) -> EvaluateResponse:
    bundle = get_lab004_bundle()
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
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "invalid_request",
                "reason": "The service could not complete this evaluation.",
                "execution": "not_performed",
            },
        ) from exc
