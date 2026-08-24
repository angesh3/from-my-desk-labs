"""Restricted fallback recommendations. Never overrides the original decision."""

from __future__ import annotations

from typing import Optional

from .models import FallbackRecommendation, FallbackType


_FALLBACKS: dict[str, FallbackRecommendation] = {
    "agent_unknown": FallbackRecommendation(
        available=True,
        fallback_type="register_agent",
        explanation="Register the agent in the management plane, then request a new evaluation.",
        permitted_operations=["register_agent", "collect_profile"],
        prohibited_operations=["execute_action", "restore_authority_automatically"],
        new_evaluation_required=True,
    ),
    "capability_not_delegated": FallbackRecommendation(
        available=True,
        fallback_type="request_new_delegation",
        explanation="Request a new, narrower or correctly scoped delegation with a new delegation ID.",
        permitted_operations=["request_new_delegation", "request_human_review"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "child_capability_exceeds_parent": FallbackRecommendation(
        available=True,
        fallback_type="request_narrower_action",
        explanation="Correct the child envelope so capabilities remain a subset of the parent.",
        permitted_operations=["request_narrower_action", "correct_delegation"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "child_limit_exceeds_parent": FallbackRecommendation(
        available=True,
        fallback_type="request_narrower_action",
        explanation="Reduce the child maximum amount to within the parent limit.",
        permitted_operations=["request_narrower_action"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "child_expiry_exceeds_parent": FallbackRecommendation(
        available=True,
        fallback_type="correct_delegation_period",
        explanation="Correct the child validity window so it does not exceed the parent.",
        permitted_operations=["correct_delegation_period"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "delegation_depth_exceeded": FallbackRecommendation(
        available=True,
        fallback_type="request_direct_delegation",
        explanation="Request a direct principal delegation instead of further redelegation.",
        permitted_operations=["request_direct_delegation"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "parent_expired": FallbackRecommendation(
        available=True,
        fallback_type="request_new_delegation",
        explanation="Expired authority is not restored automatically. Issue a new delegation.",
        permitted_operations=["request_new_delegation"],
        prohibited_operations=["execute_action", "restore_expired_authority"],
        new_evaluation_required=True,
    ),
    "parent_revoked": FallbackRecommendation(
        available=True,
        fallback_type="request_human_review",
        explanation="Revoked authority is not restored automatically. Human review is required.",
        permitted_operations=["request_human_review", "request_new_delegation"],
        prohibited_operations=["execute_action", "restore_revoked_authority"],
        new_evaluation_required=True,
    ),
    "posture_evidence_stale": FallbackRecommendation(
        available=True,
        fallback_type="refresh_posture",
        explanation="Refresh posture evidence, then submit a new evaluation.",
        permitted_operations=["refresh_posture"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "model_version_noncompliant": FallbackRecommendation(
        available=True,
        fallback_type="upgrade_version",
        explanation="Upgrade to an approved model/runtime version, then re-evaluate.",
        permitted_operations=["upgrade_version"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "tool_inventory_changed": FallbackRecommendation(
        available=True,
        fallback_type="investigate_tool_change",
        explanation="Investigate the unexpected tool inventory before any new authorization.",
        permitted_operations=["investigate_tool_change"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "profile_mismatch": FallbackRecommendation(
        available=True,
        fallback_type="request_human_review",
        explanation="Human review is required to resolve the profile mismatch.",
        permitted_operations=["request_human_review", "collect_profile"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "confirmation_threshold": FallbackRecommendation(
        available=True,
        fallback_type="request_human_review",
        explanation="Obtain principal confirmation, then submit a new evaluation.",
        permitted_operations=["request_human_review"],
        prohibited_operations=["execute_action_without_confirmation"],
        new_evaluation_required=True,
    ),
    "unusual_context": FallbackRecommendation(
        available=True,
        fallback_type="request_human_review",
        explanation="Confirm the unusual context with a human reviewer.",
        permitted_operations=["request_human_review"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "policy_satisfied": FallbackRecommendation(
        available=False,
        fallback_type="none",
        explanation="",
        permitted_operations=[],
        prohibited_operations=["execute_without_binding_check"],
        new_evaluation_required=False,
    ),
}


def recommend_fallback(reason_code: str) -> FallbackRecommendation:
    item = _FALLBACKS.get(reason_code)
    if item is None:
        return FallbackRecommendation(
            available=True,
            fallback_type="request_human_review",
            explanation="Human review is required before any remediation path proceeds.",
            permitted_operations=["request_human_review"],
            prohibited_operations=["execute_action", "override_deny"],
            new_evaluation_required=True,
        )
    # Return a copy so callers cannot mutate shared state
    return item.model_copy(deep=True)


def fallback_does_not_override(decision: str, fallback: FallbackRecommendation) -> bool:
    """Invariant: fallback never converts DENY into permission."""
    if decision == "deny" and fallback.available:
        return "execute_action" not in fallback.permitted_operations and (
            fallback.new_evaluation_required is True
        )
    return True
