"""Lab 003 evaluation API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from .loader import Lab003Bundle, Lab003ConfigError, load_bundle
from .models import EvaluationResult, ScenarioEvaluateRequest, ScenarioMeta
from .service import evaluate_scenario, list_scenarios

router = APIRouter()
_bundle: Optional[Lab003Bundle] = None


def data_dir() -> Path:
    override = os.environ.get("LAB003_DATA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "examples"


def policy_dir() -> Path:
    override = os.environ.get("LAB003_POLICY_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "policies"


def get_lab003_bundle() -> Lab003Bundle:
    global _bundle
    if _bundle is None:
        _bundle = load_bundle(data_dir(), policy_dir())
    return _bundle


def reset_lab003_bundle() -> None:
    global _bundle
    _bundle = None


@router.get("/api/labs/003/scenarios", response_model=List[ScenarioMeta])
def scenarios() -> List[ScenarioMeta]:
    try:
        return list_scenarios(get_lab003_bundle())
    except Lab003ConfigError as exc:
        raise HTTPException(
            status_code=500, detail="Lab 003 configuration unavailable."
        ) from exc


@router.post("/api/labs/003/evaluate", response_model=EvaluationResult)
def evaluate(payload: ScenarioEvaluateRequest) -> EvaluationResult:
    bundle = get_lab003_bundle()
    if payload.scenario_id not in bundle.scenarios:
        raise HTTPException(
            status_code=404,
            detail={
                "reason_code": "invalid_request",
                "reason": "Unknown scenario.",
                "execution": "not_performed",
            },
        )
    try:
        return evaluate_scenario(bundle, payload.scenario_id)
    except Lab003ConfigError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "policy_unavailable",
                "reason": "Lab 003 policy data is unavailable.",
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
