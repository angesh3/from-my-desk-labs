"""Operating context evaluator."""

from __future__ import annotations

from typing import Any, Dict

from .models import AccessRequest, EvaluationFragment


def evaluate_context(
    request: AccessRequest,
    policy: Dict[str, Any],
) -> EvaluationFragment:
    material_contexts = set(policy.get("material_context_changes") or ["material_change"])
    if request.context in material_contexts:
        return EvaluationFragment(
            stage="context",
            outcome="warning",
            decision_signal="step_up",
            reason_code="context_change_requires_step_up",
            summary="Material context change requires elevated assurance before proceeding.",
            details={"context": request.context},
        )
    if request.context == "unusual":
        return EvaluationFragment(
            stage="context",
            outcome="warning",
            decision_signal="confirm",
            reason_code="human_consent_required",
            summary="Unusual operating context requires human confirmation.",
            details={"context": request.context},
        )
    return EvaluationFragment(
        stage="context",
        outcome="satisfied",
        summary="Operating context is within normal Cedar Quill Markets parameters.",
        details={"context": request.context},
    )
