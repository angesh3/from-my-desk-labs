"""Lab 001 evaluation API. No website templates live here."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from .loader import PolicyBundle, load_bundle, sanitized_registry
from .models import EvaluateRequest, EvaluateResponse
from .policy_engine import evaluate

router = APIRouter()
_bundle: Optional[PolicyBundle] = None


def policy_dir() -> Path:
    override = os.environ.get("POLICY_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "policies"


def get_bundle() -> PolicyBundle:
    global _bundle
    if _bundle is None:
        _bundle = load_bundle(policy_dir())
    return _bundle


def reset_bundle() -> None:
    global _bundle
    _bundle = None


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": os.environ.get("APP_VERSION", "0.3.0"),
        "service": "from-my-desk",
    }


@router.get("/registry")
def registry() -> Any:
    mode = os.environ.get("REGISTRY_PUBLIC", "sanitized").strip().lower()
    if mode in {"disabled", "private", "off"}:
        raise HTTPException(status_code=404, detail="Registry is not published.")
    return sanitized_registry(get_bundle())


def _evaluate(payload: EvaluateRequest) -> EvaluateResponse:
    return evaluate(payload, get_bundle())


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_legacy(payload: EvaluateRequest) -> EvaluateResponse:
    return _evaluate(payload)


@router.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_api(payload: EvaluateRequest) -> EvaluateResponse:
    return _evaluate(payload)
