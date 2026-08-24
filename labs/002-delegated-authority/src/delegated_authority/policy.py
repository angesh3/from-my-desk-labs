"""Trust gateway / policy orchestrator for Lab 002."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from .models import (
    ActionRequest,
    AgentProfile,
    Decision,
    DECISION_RANK,
    DelegationResult,
    IdentityResult,
    PostureEvidence,
)


def reason_category_for(code: str) -> str:
    mapping = {
        "policy_satisfied": "policy_satisfied",
        "confirmation_threshold": "business_confirmation",
        "unusual_context": "business_confirmation",
        "posture_evidence_stale": "assurance_required",
        "identity_invalid": "identity_failure",
        "agent_unknown": "identity_failure",
        "principal_mismatch": "identity_failure",
        "parent_expired": "lifecycle_failure",
        "parent_revoked": "lifecycle_failure",
        "capability_not_delegated": "delegation_failure",
        "child_capability_exceeds_parent": "delegation_failure",
        "child_resource_exceeds_parent": "delegation_failure",
        "child_limit_exceeds_parent": "delegation_failure",
        "child_expiry_exceeds_parent": "delegation_failure",
        "redelegation_prohibited": "delegation_failure",
        "delegation_depth_exceeded": "delegation_failure",
        "delegation_chain_broken": "delegation_failure",
        "profile_mismatch": "profile_risk",
        "model_version_noncompliant": "posture_risk",
        "tool_inventory_changed": "posture_risk",
        "runtime_compromised": "posture_risk",
        "policy_unavailable": "system_failure",
        "audit_unavailable": "system_failure",
        "invalid_request": "system_failure",
    }
    return mapping.get(code, "system_failure")


def decide(
    request: ActionRequest,
    identity: IdentityResult,
    delegation: DelegationResult,
    profile: AgentProfile,
    posture: PostureEvidence,
    policy: Dict[str, Any],
) -> Tuple[Decision, str, Optional[str], str]:
    """
    Return (decision, reason_code, violated_constraint, explanation).
    Precedence: DENY > STEP_UP > CONFIRM > ALLOW.
    """
    candidates: list[Tuple[Decision, str, Optional[str], str]] = []

    # Identity
    if identity.identity_status == "unknown" or identity.reason_code == "agent_unknown":
        candidates.append(
            (
                "deny",
                "agent_unknown",
                "agent_unknown",
                "The requesting agent is unknown to the management plane.",
            )
        )
    elif identity.reason_code == "principal_mismatch":
        candidates.append(
            (
                "deny",
                "principal_mismatch",
                "principal_binding_invalid",
                "The agent is not bound to the stated principal.",
            )
        )
    elif identity.identity_status == "invalid" or identity.agent_status in {
        "revoked",
        "suspended",
    }:
        candidates.append(
            (
                "deny",
                identity.reason_code or "identity_invalid",
                "identity_invalid",
                "Identity evaluation failed for this agent.",
            )
        )

    # Delegation hard failures
    if delegation.reason_code:
        deny_codes = {
            "parent_expired",
            "parent_revoked",
            "capability_not_delegated",
            "child_capability_exceeds_parent",
            "child_resource_exceeds_parent",
            "child_limit_exceeds_parent",
            "child_expiry_exceeds_parent",
            "redelegation_prohibited",
            "delegation_depth_exceeded",
            "delegation_chain_broken",
        }
        if delegation.reason_code in deny_codes:
            explanations = {
                "capability_not_delegated": (
                    "The Research Agent was delegated research capability but "
                    "requested an action outside effective authority."
                ),
                "parent_revoked": "A parent delegation was revoked; downstream authority is invalid.",
                "parent_expired": "A parent delegation expired; downstream authority is invalid.",
                "child_capability_exceeds_parent": (
                    "Child capabilities exceed parent capabilities."
                ),
                "child_limit_exceeds_parent": (
                    "Child maximum amount exceeds parent maximum amount."
                ),
                "child_expiry_exceeds_parent": (
                    "Child expiry exceeds parent expiry."
                ),
                "delegation_depth_exceeded": "Delegation depth was exceeded.",
                "redelegation_prohibited": "Redelegation is not permitted by the parent envelope.",
                "delegation_chain_broken": "The delegation chain is incomplete or inconsistent.",
                "child_resource_exceeds_parent": (
                    "Child resources exceed parent resources."
                ),
            }
            candidates.append(
                (
                    "deny",
                    delegation.reason_code,
                    delegation.violated_constraint,
                    explanations.get(
                        delegation.reason_code,
                        "Delegation constraints were violated.",
                    ),
                )
            )

    # Profile — cannot manufacture authority; mismatch → STEP_UP unless already DENY
    if profile.profile_status == "unknown":
        candidates.append(
            (
                "deny",
                "agent_unknown",
                "profile_unknown",
                "No trusted profile exists for this agent.",
            )
        )
    elif profile.profile_mismatch or profile.profile_status == "conflicting":
        candidates.append(
            (
                "step_up",
                "profile_mismatch",
                "profile_mismatch",
                "APE detected a profile mismatch requiring human review.",
            )
        )

    # Critical invariant: executor-looking profile cannot grant missing capability
    if (
        request.requested_capability not in set(delegation.effective_capabilities)
        and delegation.chain_status == "valid"
    ):
        candidates.append(
            (
                "deny",
                "capability_not_delegated",
                "requested_capability_not_in_effective_capabilities",
                "Profiling cannot manufacture missing delegated authority.",
            )
        )

    # Posture
    if posture.reason_code == "runtime_compromised" or posture.recommended_treatment == "deny":
        if posture.reason_code in {"tool_inventory_changed", "runtime_compromised"} or (
            posture.tool_inventory_status in {"changed", "unexpected", "unauthorized"}
        ):
            code = posture.reason_code or "tool_inventory_changed"
            candidates.append(
                (
                    "deny",
                    code,
                    code,
                    "APSE found a hard posture failure that blocks the request.",
                )
            )
    if posture.evidence_freshness == "stale" or posture.posture_status == "stale":
        candidates.append(
            (
                "step_up",
                "posture_evidence_stale",
                "evidence_freshness_stale",
                "Posture evidence is stale and requires refresh before proceeding.",
            )
        )
    if posture.model_version_status in {"noncompliant", "outdated"}:
        candidates.append(
            (
                "step_up",
                "model_version_noncompliant",
                "model_version_noncompliant",
                "The agent model or runtime version is noncompliant and needs upgrade.",
            )
        )

    # Context / limits (business confirmation) — only if authority otherwise valid
    confirm_threshold = Decimal(str(policy.get("confirm_threshold", "5000.00")))
    if request.context == "unusual":
        candidates.append(
            (
                "confirm",
                "unusual_context",
                "unusual_context",
                "Authority is valid, but the operating context is unusual and needs confirmation.",
            )
        )
    if request.requested_amount > confirm_threshold:
        candidates.append(
            (
                "confirm",
                "confirmation_threshold",
                "amount_requires_confirmation",
                "Authority is valid, but the amount exceeds the autonomous confirmation threshold.",
            )
        )

    if not candidates:
        return (
            "allow",
            "policy_satisfied",
            None,
            "Identity, delegation, profile, posture, scope, limits, and context are satisfied.",
        )

    # Apply precedence: keep the most restrictive decision; on ties keep earlier stage.
    best = candidates[0]
    for item in candidates[1:]:
        if DECISION_RANK[item[0]] < DECISION_RANK[best[0]]:
            best = item
    return best

