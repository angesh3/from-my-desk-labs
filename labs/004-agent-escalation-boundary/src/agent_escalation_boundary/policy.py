"""Deterministic execution-judgment policy for Lab 004.

Authorization (ALLOW / CONFIRM / STEP_UP / DENY) is an input.
This engine decides whether the agent should PROCEED, CLARIFY, ESCALATE, or STOP.

Precedence: STOP > ESCALATE > CLARIFY > PROCEED
Exception: for an immediate threat with delegated session-revoke capability,
a bounded protective action may accompany ESCALATE without expanding authority.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set, Tuple

from .models import (
    AuthorizationOutcome,
    BoundedAction,
    EvaluateRequest,
    EvaluateResponse,
    EvidenceConfidence,
    ExecutionOutcome,
    GoalClarity,
    HumanAvailability,
    PolicyCoverage,
    PotentialImpact,
    Reversibility,
    TimeSensitivity,
    TriggeredRule,
)

POLICY_VERSION = "lab004-escalation-v1"

# Actions the Cedar Quill SOC agent may perform under fictional delegation.
SESSION_REVOKE_ACTIONS = {
    "revoke_suspicious_session",
    "revoke_session",
    "require_stronger_authentication",
}
SUSPEND_ACTIONS = {
    "suspend_account",
    "temporarily_suspend_access",
}
PROHIBITED_ACTIONS = {
    "permanently_delete_account",
    "wipe_mailbox",
    "disable_mfa_globally",
}
KNOWN_CAPABILITIES = {
    "revoke_sessions",
    "temporarily_suspend_access",
    "require_stronger_authentication",
    "preserve_evidence",
    "notify_incident_lead",
}

ESCALATION_CONTACT = "cq-soc-incident-lead@cedarquill.example"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _capability_covers(request: EvaluateRequest) -> bool:
    action = request.requested_action.strip().lower().replace(" ", "_")
    capability = request.delegated_capability.strip().lower().replace(" ", "_")
    if action in PROHIBITED_ACTIONS:
        return False
    allowed_by_capability = {
        "revoke_sessions": SESSION_REVOKE_ACTIONS | {"preserve_evidence", "notify_incident_lead"},
        "temporarily_suspend_access": SUSPEND_ACTIONS
        | SESSION_REVOKE_ACTIONS
        | {"preserve_evidence", "notify_incident_lead"},
        "require_stronger_authentication": {"require_stronger_authentication"},
        "preserve_evidence": {"preserve_evidence"},
        "notify_incident_lead": {"notify_incident_lead"},
    }
    if capability in allowed_by_capability:
        return action in allowed_by_capability[capability]
    return action == capability


def _identity_valid(request: EvaluateRequest) -> bool:
    if not request.agent_id.strip() or not request.principal_id.strip():
        return False
    if not request.target_account.strip():
        return False
    if request.agent_id.strip().lower() in {"unknown", "invalid", "n/a"}:
        return False
    return True


def _high_or_critical(impact: PotentialImpact) -> bool:
    return impact in {PotentialImpact.high, PotentialImpact.critical}


def _hard_to_reverse(reversibility: Reversibility) -> bool:
    return reversibility in {
        Reversibility.difficult_to_reverse,
        Reversibility.irreversible,
    }


def _collect_stop_rules(request: EvaluateRequest) -> List[TriggeredRule]:
    rules: List[TriggeredRule] = []
    if request.authorization_outcome == AuthorizationOutcome.deny:
        rules.append(
            TriggeredRule(
                rule_id="stop.authorization_deny",
                outcome=ExecutionOutcome.stop,
                summary="Authorization outcome is DENY; the agent must not continue.",
            )
        )
    if request.policy_coverage == PolicyCoverage.prohibited:
        rules.append(
            TriggeredRule(
                rule_id="stop.policy_prohibited",
                outcome=ExecutionOutcome.stop,
                summary="Policy coverage is prohibited for this action.",
            )
        )
    if request.requested_action.strip().lower() in PROHIBITED_ACTIONS:
        rules.append(
            TriggeredRule(
                rule_id="stop.action_prohibited",
                outcome=ExecutionOutcome.stop,
                summary="The requested action is outside organizational safety policy.",
            )
        )
    if not _capability_covers(request):
        rules.append(
            TriggeredRule(
                rule_id="stop.capability_mismatch",
                outcome=ExecutionOutcome.stop,
                summary="Delegated capability does not cover the requested action.",
            )
        )
    if not _identity_valid(request):
        rules.append(
            TriggeredRule(
                rule_id="stop.invalid_identity",
                outcome=ExecutionOutcome.stop,
                summary="Required identity, principal, or target account information is invalid.",
            )
        )
    if (
        request.reversibility == Reversibility.irreversible
        and request.potential_impact == PotentialImpact.critical
        and request.human_availability
        in {HumanAvailability.unavailable, HumanAvailability.delayed}
    ):
        rules.append(
            TriggeredRule(
                rule_id="stop.irreversible_without_approval",
                outcome=ExecutionOutcome.stop,
                summary=(
                    "Irreversible action with critical impact cannot proceed when "
                    "required approval is unavailable."
                ),
            )
        )
    return rules


def _collect_escalate_rules(request: EvaluateRequest) -> List[TriggeredRule]:
    rules: List[TriggeredRule] = []
    if request.authorization_outcome == AuthorizationOutcome.confirm and not request.confirmation_satisfied:
        rules.append(
            TriggeredRule(
                rule_id="escalate.confirm_pending",
                outcome=ExecutionOutcome.escalate,
                summary="Authorization requires CONFIRM and confirmation is not satisfied.",
            )
        )
    if request.authorization_outcome == AuthorizationOutcome.step_up and not request.stronger_auth_completed:
        rules.append(
            TriggeredRule(
                rule_id="escalate.step_up_pending",
                outcome=ExecutionOutcome.escalate,
                summary="Authorization requires STEP_UP and stronger authentication is not completed.",
            )
        )
    if request.evidence_confidence in {
        EvidenceConfidence.low,
        EvidenceConfidence.conflicting,
    } and _high_or_critical(request.potential_impact):
        rules.append(
            TriggeredRule(
                rule_id="escalate.weak_evidence_high_impact",
                outcome=ExecutionOutcome.escalate,
                summary="Evidence is low or conflicting while impact is high or critical.",
            )
        )
    if (
        request.policy_coverage == PolicyCoverage.partially_covered
        and _high_or_critical(request.potential_impact)
    ):
        rules.append(
            TriggeredRule(
                rule_id="escalate.partial_policy_high_impact",
                outcome=ExecutionOutcome.escalate,
                summary="Policy only partially covers a high-impact action.",
            )
        )
    if _hard_to_reverse(request.reversibility) and _high_or_critical(request.potential_impact):
        rules.append(
            TriggeredRule(
                rule_id="escalate.hard_reverse_high_impact",
                outcome=ExecutionOutcome.escalate,
                summary="Action is difficult to reverse or irreversible under high or critical impact.",
            )
        )
    if request.human_availability == HumanAvailability.available_now and _high_or_critical(
        request.potential_impact
    ) and request.evidence_confidence in {
        EvidenceConfidence.low,
        EvidenceConfidence.conflicting,
        EvidenceConfidence.medium,
    }:
        # Human accountability required when a person is available for high-impact uncertain cases.
        if not any(r.rule_id == "escalate.weak_evidence_high_impact" for r in rules):
            rules.append(
                TriggeredRule(
                    rule_id="escalate.human_accountability",
                    outcome=ExecutionOutcome.escalate,
                    summary="High-impact action requires human accountability before independent completion.",
                )
            )
    if (
        request.requested_action.strip().lower() in SUSPEND_ACTIONS
        and request.delegated_capability.strip().lower() == "revoke_sessions"
    ):
        # Already covered by capability mismatch STOP; keep escalate only if somehow allowed.
        pass
    if (
        request.authorization_outcome == AuthorizationOutcome.allow
        and request.potential_impact == PotentialImpact.critical
        and request.time_sensitivity == TimeSensitivity.immediate_threat
    ):
        rules.append(
            TriggeredRule(
                rule_id="escalate.immediate_threat_boundary",
                outcome=ExecutionOutcome.escalate,
                summary=(
                    "Immediate threat with critical impact exceeds independent decision "
                    "boundary; escalate with any permitted bounded protective action."
                ),
            )
        )
    return rules


def _collect_clarify_rules(request: EvaluateRequest) -> List[TriggeredRule]:
    rules: List[TriggeredRule] = []
    if request.goal_clarity == GoalClarity.ambiguous:
        rules.append(
            TriggeredRule(
                rule_id="clarify.ambiguous_goal",
                outcome=ExecutionOutcome.clarify,
                summary="Goal clarity is ambiguous; different interpretations could produce different actions.",
            )
        )
    if not request.requested_action.strip() or not request.target_account.strip():
        rules.append(
            TriggeredRule(
                rule_id="clarify.missing_target",
                outcome=ExecutionOutcome.clarify,
                summary="A required target, scope, or action parameter is missing.",
            )
        )
    if (
        request.goal_clarity == GoalClarity.partially_clear
        and request.potential_impact in {PotentialImpact.low, PotentialImpact.moderate}
        and request.evidence_confidence != EvidenceConfidence.conflicting
    ):
        rules.append(
            TriggeredRule(
                rule_id="clarify.partial_goal",
                outcome=ExecutionOutcome.clarify,
                summary="Goal is only partially clear; clarify scope before acting.",
            )
        )
    return rules


def _bounded_protective_action(request: EvaluateRequest) -> BoundedAction:
    """Permit bounded protective steps under immediate threat without expanding authority."""
    if request.time_sensitivity != TimeSensitivity.immediate_threat:
        return BoundedAction(available=False)
    if request.authorization_outcome == AuthorizationOutcome.deny:
        return BoundedAction(available=False)
    if request.policy_coverage == PolicyCoverage.prohibited:
        return BoundedAction(available=False)
    capability = request.delegated_capability.strip().lower()
    if capability not in {"revoke_sessions", "temporarily_suspend_access"}:
        return BoundedAction(available=False)
    actions = [
        "Revoke only the suspicious session",
        "Require stronger authentication for new sessions",
        "Preserve relevant evidence",
        "Increase monitoring on the account",
        "Notify the incident lead",
    ]
    return BoundedAction(
        available=True,
        actions=actions,
        explanation=(
            "Under an immediate threat, the agent may take these bounded protective steps "
            "that stay within delegated session and monitoring authority. Full account "
            "suspension remains behind human approval and does not expand the agent's authority."
        ),
        expands_authority=False,
    )


def _missing_evidence(request: EvaluateRequest) -> List[str]:
    items: List[str] = []
    if request.evidence_confidence == EvidenceConfidence.conflicting:
        items.append("Login location and device evidence conflict with possible legitimate travel.")
        items.append("Sensitive-file access timing overlaps an active customer meeting.")
    elif request.evidence_confidence == EvidenceConfidence.low:
        items.append("Evidence confidence is low; corroborating signals are incomplete.")
    if request.goal_clarity == GoalClarity.ambiguous:
        items.append("Requested goal does not specify whether to monitor, challenge, revoke, or suspend.")
    if request.policy_coverage == PolicyCoverage.partially_covered:
        items.append("Policy guidance is incomplete for the full requested action.")
    if request.authorization_outcome == AuthorizationOutcome.step_up and not request.stronger_auth_completed:
        items.append("Stronger authentication has not been completed.")
    if request.authorization_outcome == AuthorizationOutcome.confirm and not request.confirmation_satisfied:
        items.append("Required human confirmation has not been recorded.")
    return items


def _impact_copy(request: EvaluateRequest) -> Tuple[str, str]:
    acting = {
        PotentialImpact.low: "Acting now has limited blast radius and is easier to reverse.",
        PotentialImpact.moderate: "Acting now may briefly disrupt the employee workflow.",
        PotentialImpact.high: "Acting now could interrupt production or customer-facing work.",
        PotentialImpact.critical: (
            "Acting now (especially full suspension) could disrupt a critical customer "
            "workflow while an investigation is still incomplete."
        ),
    }[request.potential_impact]
    waiting = {
        TimeSensitivity.low: "Waiting has low near-term risk.",
        TimeSensitivity.moderate: "Waiting increases exposure if the session is malicious.",
        TimeSensitivity.urgent: "Waiting lengthens the attacker window if compromise is real.",
        TimeSensitivity.immediate_threat: (
            "Waiting without any protective step leaves a live suspicious session active."
        ),
    }[request.time_sensitivity]
    return acting, waiting


def _safe_and_approval_actions(
    request: EvaluateRequest, outcome: ExecutionOutcome, bounded: BoundedAction
) -> Tuple[List[str], List[str]]:
    safe: List[str] = []
    approval: List[str] = []
    if bounded.available:
        safe.extend(bounded.actions)
        approval.append("Decide whether to fully suspend the account")
    elif outcome == ExecutionOutcome.proceed:
        safe.append(request.requested_action.replace("_", " "))
    elif outcome == ExecutionOutcome.clarify:
        safe.append("Ask for a precise action scope (monitor, challenge, revoke, or suspend)")
        approval.append("No protective change until the goal is clarified")
    elif outcome == ExecutionOutcome.escalate:
        safe.append("Preserve evidence and notify the incident lead")
        if request.delegated_capability.strip().lower() == "revoke_sessions":
            safe.append("Revoke a clearly identified suspicious session if confirmed")
        approval.append("Full account suspension or irreversible changes")
    else:
        approval.append(request.requested_action.replace("_", " "))
        safe.append("Record the stop decision and retain audit evidence")
    return safe, approval


def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    stop_rules = _collect_stop_rules(request)
    escalate_rules = _collect_escalate_rules(request)
    clarify_rules = _collect_clarify_rules(request)

    bounded = BoundedAction(available=False)
    # Immediate-threat exception: escalate with bounded protective action when
    # stop is not required solely by deny/prohibited/capability, OR when escalate
    # fires and threat is immediate.
    if request.time_sensitivity == TimeSensitivity.immediate_threat:
        # Hard stops still win, except we still describe why.
        if not stop_rules or (
            stop_rules
            and all(
                r.rule_id
                not in {
                    "stop.authorization_deny",
                    "stop.policy_prohibited",
                    "stop.action_prohibited",
                    "stop.capability_mismatch",
                    "stop.invalid_identity",
                    "stop.irreversible_without_approval",
                }
                for r in stop_rules
            )
        ):
            pass
        if not any(
            r.rule_id
            in {
                "stop.authorization_deny",
                "stop.policy_prohibited",
                "stop.action_prohibited",
                "stop.capability_mismatch",
                "stop.invalid_identity",
                "stop.irreversible_without_approval",
            }
            for r in stop_rules
        ):
            bounded = _bounded_protective_action(request)

    if stop_rules:
        outcome = ExecutionOutcome.stop
        triggered = stop_rules
    elif escalate_rules or (
        bounded.available and request.time_sensitivity == TimeSensitivity.immediate_threat
    ):
        outcome = ExecutionOutcome.escalate
        triggered = escalate_rules or [
            TriggeredRule(
                rule_id="escalate.immediate_threat_boundary",
                outcome=ExecutionOutcome.escalate,
                summary="Immediate threat requires escalation with bounded protective action.",
            )
        ]
        if bounded.available and not any(
            r.rule_id == "escalate.immediate_threat_boundary" for r in triggered
        ):
            triggered = list(triggered) + [
                TriggeredRule(
                    rule_id="escalate.bounded_protective_action",
                    outcome=ExecutionOutcome.escalate,
                    summary="Bounded protective action is available without expanding authority.",
                )
            ]
    elif clarify_rules:
        outcome = ExecutionOutcome.clarify
        triggered = clarify_rules
    else:
        # PROCEED gate
        proceed_ok = (
            request.authorization_outcome == AuthorizationOutcome.allow
            and request.goal_clarity == GoalClarity.clear
            and request.evidence_confidence
            in {EvidenceConfidence.medium, EvidenceConfidence.high}
            and request.policy_coverage == PolicyCoverage.explicitly_covered
            and request.potential_impact in {PotentialImpact.low, PotentialImpact.moderate}
            and request.reversibility
            in {Reversibility.easily_reversible, Reversibility.partially_reversible}
        )
        if proceed_ok:
            outcome = ExecutionOutcome.proceed
            triggered = [
                TriggeredRule(
                    rule_id="proceed.independent_boundary",
                    outcome=ExecutionOutcome.proceed,
                    summary=(
                        "Authorization is ALLOW, goal is clear, evidence is sufficient, "
                        "policy explicitly covers the action, and impact is reversible."
                    ),
                )
            ]
        else:
            outcome = ExecutionOutcome.escalate
            triggered = [
                TriggeredRule(
                    rule_id="escalate.exceeds_independent_boundary",
                    outcome=ExecutionOutcome.escalate,
                    summary="Conditions exceed the agent's independent decision boundary.",
                )
            ]

    acting, waiting = _impact_copy(request)
    safe, approval = _safe_and_approval_actions(request, outcome, bounded)
    missing = _missing_evidence(request)

    explanations = {
        ExecutionOutcome.proceed: (
            "The agent may continue independently. Authorization permits the action, "
            "the goal is clear, evidence supports acting, and consequence stays within "
            "the reversible, explicitly covered boundary."
        ),
        ExecutionOutcome.clarify: (
            "The agent should pause and ask for clarification before choosing a concrete "
            "protective action. Continuing alone risks applying the wrong control."
        ),
        ExecutionOutcome.escalate: (
            "The agent should escalate rather than complete the high-consequence decision alone. "
            "Authorization may still permit related protective steps, but human judgment is required."
        ),
        ExecutionOutcome.stop: (
            "The agent must stop. Continuing would violate authorization, policy, or "
            "delegated capability boundaries."
        ),
    }

    next_steps = {
        ExecutionOutcome.proceed: f"Perform {request.requested_action.replace('_', ' ')} and record the decision.",
        ExecutionOutcome.clarify: (
            "Ask the requester to specify whether to monitor, challenge, revoke sessions, "
            "or suspend access."
        ),
        ExecutionOutcome.escalate: (
            "Notify the incident lead with evidence summary; apply any permitted bounded "
            "protective steps; await human decision on full suspension."
            if bounded.available
            else "Hand the case to the incident lead with evidence, impact, and recommended options."
        ),
        ExecutionOutcome.stop: "Do not perform the requested action. Retain the audit record.",
    }

    why = explanations[outcome]
    if bounded.available and outcome == ExecutionOutcome.escalate:
        why += (
            " A bounded protective path is available: revoke the suspicious session, "
            "require stronger authentication, preserve evidence, and notify the incident lead "
            "without expanding delegated authority."
        )

    return EvaluateResponse(
        authorization_outcome=request.authorization_outcome,
        execution_outcome=outcome,
        decision_id="cq-esc-" + uuid.uuid4().hex[:12],
        evaluated_at=_utc_now(),
        explanation=why,
        evidence_assessment=(
            f"Evidence confidence: {request.evidence_confidence.value.replace('_', ' ')}. "
            f"Goal clarity: {request.goal_clarity.value.replace('_', ' ')}."
        ),
        triggered_rules=triggered,
        why_paused_or_proceeded=why,
        missing_or_conflicting_evidence=missing,
        impact_of_acting=acting,
        impact_of_waiting=waiting,
        safe_actions_permitted=safe,
        actions_requiring_approval=approval,
        recommended_next_step=next_steps[outcome],
        escalation_destination=ESCALATION_CONTACT
        if outcome in {ExecutionOutcome.escalate, ExecutionOutcome.stop}
        else None,
        authority_chain_summary=(
            f"{request.principal_id} → {request.agent_id} "
            f"(capability: {request.delegated_capability}) → "
            f"{request.requested_action} on {request.target_account}"
        ),
        bounded_protective_action=bounded,
        execution="not_performed",
        policy_version=POLICY_VERSION,
        preset_id=request.preset_id,
    )
