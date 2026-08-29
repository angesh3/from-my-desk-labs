"""Restricted recovery recommendations. Never overrides the original decision."""

from __future__ import annotations

from .models import RestrictedRecommendation, RestrictedType


_RESTRICTED: dict[str, RestrictedRecommendation] = {
    "restricted_registration_permitted": RestrictedRecommendation(
        available=True,
        restricted_type="register_agent",
        explanation=(
            "Complete restricted agent registration, collect profile evidence, "
            "then request a new evaluation before any operational action."
        ),
        permitted_operations=["register_agent", "collect_profile"],
        prohibited_operations=["execute_action", "restore_authority_automatically"],
        new_evaluation_required=True,
    ),
    "unknown_agent_protected_action": RestrictedRecommendation(
        available=True,
        restricted_type="register_agent",
        explanation=(
            "Register the agent through the restricted onboarding path before "
            "attempting protected tools or actions."
        ),
        permitted_operations=["register_agent"],
        prohibited_operations=["execute_action", "use_protected_tools"],
        new_evaluation_required=True,
    ),
    "capability_not_delegated": RestrictedRecommendation(
        available=True,
        restricted_type="request_new_delegation",
        explanation="Request a new, correctly scoped delegation with a new delegation ID.",
        permitted_operations=["request_new_delegation", "request_human_review"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "parent_delegation_expired": RestrictedRecommendation(
        available=True,
        restricted_type="request_new_delegation",
        explanation="Expired authority is not restored automatically. Issue a new delegation.",
        permitted_operations=["request_new_delegation"],
        prohibited_operations=["execute_action", "restore_expired_authority"],
        new_evaluation_required=True,
    ),
    "parent_delegation_revoked": RestrictedRecommendation(
        available=True,
        restricted_type="request_human_review",
        explanation="Revoked authority requires human review before any new delegation.",
        permitted_operations=["request_human_review", "request_new_delegation"],
        prohibited_operations=["execute_action", "restore_revoked_authority"],
        new_evaluation_required=True,
    ),
    "posture_evidence_stale": RestrictedRecommendation(
        available=True,
        restricted_type="refresh_posture",
        explanation="Refresh runtime attestation evidence, then submit a new evaluation.",
        permitted_operations=["refresh_posture"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "model_version_noncompliant": RestrictedRecommendation(
        available=True,
        restricted_type="upgrade_version",
        explanation="Upgrade to an approved Cedar Quill Markets model version, then re-evaluate.",
        permitted_operations=["upgrade_version"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "tool_inventory_changed": RestrictedRecommendation(
        available=True,
        restricted_type="investigate_tool_change",
        explanation="Investigate the unexpected tool inventory before any new authorization.",
        permitted_operations=["investigate_tool_change"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "data_classification_exceeds_authority": RestrictedRecommendation(
        available=True,
        restricted_type="request_new_delegation",
        explanation="Request narrower data access or a delegation with higher classification bounds.",
        permitted_operations=["request_new_delegation", "request_human_review"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "purpose_not_permitted": RestrictedRecommendation(
        available=True,
        restricted_type="request_human_review",
        explanation="Correct the stated purpose or obtain a delegation that permits it.",
        permitted_operations=["request_human_review", "request_new_delegation"],
        prohibited_operations=["execute_action", "override_deny"],
        new_evaluation_required=True,
    ),
    "human_consent_required": RestrictedRecommendation(
        available=True,
        restricted_type="request_consent",
        explanation="Obtain explicit human consent, then submit a new evaluation.",
        permitted_operations=["request_consent", "request_human_review"],
        prohibited_operations=["execute_action_without_consent"],
        new_evaluation_required=True,
    ),
    "limit_requires_confirmation": RestrictedRecommendation(
        available=True,
        restricted_type="request_consent",
        explanation="Confirm the exposure amount with a human reviewer before proceeding.",
        permitted_operations=["request_consent", "request_human_review"],
        prohibited_operations=["execute_action_without_confirmation"],
        new_evaluation_required=True,
    ),
    "context_change_requires_step_up": RestrictedRecommendation(
        available=True,
        restricted_type="context_review",
        explanation="Review the material context change and refresh assurance before proceeding.",
        permitted_operations=["context_review", "refresh_posture"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "profile_mismatch": RestrictedRecommendation(
        available=True,
        restricted_type="request_human_review",
        explanation="Human review is required to resolve the APE profile mismatch.",
        permitted_operations=["request_human_review", "collect_profile"],
        prohibited_operations=["execute_action"],
        new_evaluation_required=True,
    ),
    "within_current_authority": RestrictedRecommendation(
        available=False,
        restricted_type="none",
        explanation="",
        permitted_operations=[],
        prohibited_operations=["execute_without_binding_check"],
        new_evaluation_required=False,
    ),
}


def recommend_restricted(reason_code: str) -> RestrictedRecommendation:
    item = _RESTRICTED.get(reason_code)
    if item is None:
        return RestrictedRecommendation(
            available=True,
            restricted_type="request_human_review",
            explanation="Human review is required before any remediation path proceeds.",
            permitted_operations=["request_human_review"],
            prohibited_operations=["execute_action", "override_deny"],
            new_evaluation_required=True,
        )
    return item.model_copy(deep=True)


def restricted_does_not_override(decision: str, restricted: RestrictedRecommendation) -> bool:
    """Invariant: restricted recovery never converts DENY into permission."""
    if decision == "deny" and restricted.available:
        return "execute_action" not in restricted.permitted_operations and (
            restricted.new_evaluation_required is True
        )
    return True
