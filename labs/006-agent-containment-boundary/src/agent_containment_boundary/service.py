"""Service helpers for Lab 006."""

from __future__ import annotations

from typing import List

from .loader import Lab006Bundle
from .models import EvaluateRequest, EvaluateResponse, PresetMeta
from .policy import evaluate


def list_presets(bundle: Lab006Bundle) -> List[PresetMeta]:
    return bundle.preset_meta()


def evaluate_request(request: EvaluateRequest) -> EvaluateResponse:
    return evaluate(request)


def evaluate_preset(bundle: Lab006Bundle, preset_id: str) -> EvaluateResponse:
    preset = bundle.presets[preset_id]
    payload = preset.request.model_copy(update={"preset_id": preset_id})
    return evaluate(payload)
