"""Trust gateway / policy orchestrator for Lab 003."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .models import (
    AccessRequest,
    AgentProfile,
    Decision,
    DECISION_RANK,
    DelegationResult,
    EvaluationFragment,
    HARD_DENY_CODES,
    IdentityResult,
    PostureEvidence,
)


def reason_category_for(code: str) -> str:
    mapping = {
        "within_current_authority": "policy_satisfied",
        "human_consent_required": "business_confirmation",
        "limit_requires_confirmation": "business_confirmation",
        "posture_evidence_stale": "assurance_required",
        "model_version_noncompliant": "assurance_required",
        "context_change_requires_step_up": "assurance_required",
        "profile_mismatch": "profile_risk",
        "identity_invalid": "identity_failure",
        "agent_unknown": "identity_failure",
        "principal_mismatch": "identity_failure",
        "unknown_agent_protected_action": "identity_failure",
        "restricted_registration_permitted": "restricted_recovery",
        "capability_not_delegated": "delegation_failure",
        "parent_delegation_expired": "lifecycle_failure",
        "parent_delegation_revoked": "lifecycle_failure",
        "delegation_chain_broken": "delegation_failure",
        "purpose_not_permitted": "purpose_failure",
        "data_classification_exceeds_authority": "resource_failure",
        "tool_inventory_changed": "posture_risk",
        "invalid_request": "system_failure",
        "policy_unavailable": "system_failure",
        "audit_unavailable": "system_failure",
    }
    return mapping.get(code, "system_failure")


def decide(
    request: AccessRequest,
    fragments: List[EvaluationFragment],
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

    if request.restricted_operation and request.requested_action == "register":
        for fragment in fragments:
            if fragment.reason_code == "restricted_registration_permitted":
                return (
                    "allow",
                    "restricted_registration_permitted",
                    None,
                    (
                        "Unknown agent may complete restricted registration only; "
                        "no operational authority is granted."
                    ),
                )

    for fragment in fragments:
        if fragment.decision_signal and fragment.reason_code:
            if fragment.decision_signal == "deny" and fragment.reason_code in HARD_DENY_CODES:
                candidates.append(
                    (
                        "deny",
                        fragment.reason_code,
                        fragment.reason_code,
                        fragment.summary,
                    )
                )
            elif fragment.decision_signal == "step_up":
                candidates.append(
                    (
                        "step_up",
                        fragment.reason_code,
                        fragment.reason_code,
                        fragment.summary,
                    )
                )
            elif fragment.decision_signal == "confirm":
                candidates.append(
                    (
                        "confirm",
                        fragment.reason_code,
                        fragment.reason_code,
                        fragment.summary,
                    )
                )

    if delegation.reason_code in HARD_DENY_CODES:
        explanations = {
            "capability_not_delegated": (
                "The agent requested an action outside effective Cedar Quill Markets authority."
            ),
            "parent_delegation_revoked": (
                "A parent delegation was revoked; downstream authority is invalid."
            ),
            "parent_delegation_expired": (
                "A parent delegation expired; downstream authority is invalid."
            ),
            "delegation_chain_broken": "The delegation chain is incomplete or inconsistent.",
        }
        candidates.append(
            (
                "deny",
                delegation.reason_code,
                delegation.violated_constraint or delegation.reason_code,
                explanations.get(
                    delegation.reason_code,
                    "Delegation constraints were violated.",
                ),
            )
        )

    if profile.profile_status == "unknown" and not request.restricted_operation:
        candidates.append(
            (
                "deny",
                "agent_unknown",
                "profile_unknown",
                "No trusted APE profile exists for this agent.",
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

    if (
        request.requested_action not in set(delegation.effective_capabilities)
        and delegation.chain_status == "valid"
        and not request.restricted_operation
    ):
        candidates.append(
            (
                "deny",
                "capability_not_delegated",
                "requested_action_not_in_effective_capabilities",
                "Profiling cannot manufacture missing delegated authority.",
            )
        )

    if posture.reason_code == "tool_inventory_changed":
        candidates.append(
            (
                "deny",
                "tool_inventory_changed",
                "tool_inventory_changed",
                "APSE found an undeclared tool inventory change.",
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
                "The agent model or runtime version is noncompliant.",
            )
        )

    if identity.reason_code == "agent_unknown" and not request.restricted_operation:
        if not any(item[0] == "deny" for item in candidates):
            candidates.append(
                (
                    "deny",
                    "agent_unknown",
                    "agent_unknown",
                    "The requesting agent is unknown to the management plane.",
                )
            )

    if not candidates:
        return (
            "allow",
            "within_current_authority",
            None,
            (
                "Identity, delegation, profile, posture, scope, limits, purpose, "
                "and context are satisfied within current authority."
            ),
        )

    best = candidates[0]
    for item in candidates[1:]:
        if DECISION_RANK[item[0]] < DECISION_RANK[best[0]]:
            best = item
    return best
