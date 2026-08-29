"""Resource and data classification evaluator."""

from __future__ import annotations

from typing import Any, Dict

from .models import AccessRequest, DelegationResult, EvaluationFragment

_CLASS_RANK = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
}


def _rank(label: str) -> int:
    return _CLASS_RANK.get(label.lower(), 99)


def evaluate_resource(
    request: AccessRequest,
    delegation: DelegationResult | None,
    policy: Dict[str, Any],
) -> EvaluationFragment:
    if request.restricted_operation:
        public_resources = set(policy.get("public_registration_resources") or [])
        if request.requested_resource in public_resources:
            return EvaluationFragment(
                stage="resource",
                outcome="restricted",
                summary="Public registration resource is accessible on the restricted path.",
                details={
                    "requested_resource": request.requested_resource,
                    "data_classification": request.data_classification,
                },
            )

    effective_class = None
    if delegation and delegation.effective_data_classification:
        effective_class = delegation.effective_data_classification
    elif delegation and delegation.chain_status == "valid":
        effective_class = "public"

    if effective_class is not None and _rank(request.data_classification) > _rank(
        effective_class
    ):
        return EvaluationFragment(
            stage="resource",
            outcome="failed",
            decision_signal="deny",
            reason_code="data_classification_exceeds_authority",
            hard_authority_failure=True,
            summary=(
                "Data classification '{0}' exceeds delegated authority ({1})."
            ).format(request.data_classification, effective_class),
            details={
                "requested_resource": request.requested_resource,
                "data_classification": request.data_classification,
                "effective_data_classification": effective_class,
            },
        )

    return EvaluationFragment(
        stage="resource",
        outcome="satisfied",
        summary="Resource '{0}' is within the evaluated data boundary.".format(
            request.requested_resource
        ),
        details={
            "requested_resource": request.requested_resource,
            "data_classification": request.data_classification,
        },
    )
