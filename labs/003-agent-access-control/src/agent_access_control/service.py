"""Orchestrate Lab 003 scenario evaluation with canonical events."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .action import evaluate_action
from .audit import create_audit_record
from .context import evaluate_context
from .delegation import evaluate_delegation
from .identity import evaluate_identity
from .limits import evaluate_limits
from .loader import Lab003Bundle, materialize_scenario
from .management import AgentManagementPlane, evaluate_registration
from .models import (
    AccessRequest,
    AgentProfile,
    DelegationResult,
    EvaluationEvent,
    EvaluationFragment,
    EvaluationResult,
    IdentityResult,
    PostureEvidence,
    ProfileSummary,
    PostureSummary,
    ScenarioMeta,
)
from .policy import decide, reason_category_for
from .posture import evaluate_posture
from .principal import evaluate_principal
from .profiler import evaluate_profile
from .purpose import evaluate_purpose
from .resource import evaluate_resource
from .restricted import recommend_restricted
from .tool import evaluate_tool

CANONICAL_EVENT_ORDER = [
    "request.received",
    "agent.discovered",
    "agent.registration_evaluated",
    "agent.identity_evaluated",
    "principal.evaluated",
    "action.evaluated",
    "tool.evaluated",
    "resource_data.evaluated",
    "purpose.evaluated",
    "limits.evaluated",
    "delegation.evaluated",
    "posture.evaluated",
    "context.evaluated",
    "decision.produced",
    "restricted_path.recommended",
    "audit.completed",
]

EVALUATION_EVENT_STAGES: List[Tuple[str, str]] = [
    ("agent.registration_evaluated", "registration"),
    ("agent.identity_evaluated", "identity"),
    ("principal.evaluated", "principal"),
    ("action.evaluated", "action"),
    ("tool.evaluated", "tool"),
    ("resource_data.evaluated", "resource"),
    ("purpose.evaluated", "purpose"),
    ("limits.evaluated", "limits"),
    ("delegation.evaluated", "delegation"),
    ("posture.evaluated", "posture"),
    ("context.evaluated", "context"),
]


def _fingerprint(request: AccessRequest) -> str:
    raw = "|".join(
        [
            request.request_id,
            request.principal_id,
            request.agent_id,
            request.requested_action,
            request.requested_tool,
            request.requested_resource,
            request.data_classification,
            str(request.requested_amount),
            request.stated_purpose,
            request.delegation_id,
            request.context,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _stamp(now: datetime) -> str:
    return now.isoformat().replace("+00:00", "Z")


def _event(
    event_type: str,
    *,
    now: datetime,
    summary: str,
    status: str = "completed",
    skip_reason: Optional[str] = None,
    fragment: Optional[EvaluationFragment] = None,
) -> EvaluationEvent:
    return EvaluationEvent(
        event_type=event_type,
        status=status,  # type: ignore[arg-type]
        timestamp=_stamp(now),
        summary=summary,
        skip_reason=skip_reason,
        fragment=fragment,
    )


def list_scenarios(bundle: Lab003Bundle) -> List[ScenarioMeta]:
    return bundle.scenario_meta()


def evaluate_scenario(
    bundle: Lab003Bundle,
    scenario_id: str,
    now: Optional[datetime] = None,
) -> EvaluationResult:
    scenario, agents, profiles, posture_map, delegations = materialize_scenario(
        bundle, scenario_id
    )
    stamp = now or datetime.now(timezone.utc)
    request = AccessRequest.model_validate(scenario["request"])
    policy = bundle.policies.get("access") or {}
    management = AgentManagementPlane(agents)
    display = {
        agent_id: str(raw.get("display_name", agent_id))
        for agent_id, raw in agents.items()
    }

    registration = evaluate_registration(
        request.agent_id, management, request.restricted_operation
    )
    identity, identity_fragment = evaluate_identity(request, agents, now=stamp)
    principal_fragment = evaluate_principal(request, identity, agents)
    profile, profiler_fragment = evaluate_profile(request, profiles, management, now=stamp)
    action_fragment = evaluate_action(request, agents, policy)
    tool_fragment = evaluate_tool(request, management, profile, policy)
    delegation, delegation_fragment = evaluate_delegation(
        request, delegations, display_names=display, now=stamp
    )
    resource_fragment = evaluate_resource(request, delegation, policy)
    purpose_fragment = evaluate_purpose(request, delegation)
    limits_fragment = evaluate_limits(request, delegation, policy)
    posture, posture_fragment = evaluate_posture(
        request, posture_map, management, now=stamp
    )
    context_fragment = evaluate_context(request, policy)

    fragments_by_stage = {
        "registration": registration,
        "identity": identity_fragment,
        "principal": principal_fragment,
        "profiler": profiler_fragment,
        "action": action_fragment,
        "tool": tool_fragment,
        "resource": resource_fragment,
        "purpose": purpose_fragment,
        "limits": limits_fragment,
        "delegation": delegation_fragment,
        "posture": posture_fragment,
        "context": context_fragment,
    }
    all_fragments = list(fragments_by_stage.values())

    decision, reason_code, violated, explanation = decide(
        request,
        all_fragments,
        identity,
        delegation,
        profile,
        posture,
        policy,
    )
    restricted = recommend_restricted(reason_code)
    audit = create_audit_record(
        request=request,
        decision=decision,
        reason_code=reason_code,
        registration_state=management.registration_state(request.agent_id),
        delegation=delegation,
        profile=profile,
        posture=posture,
        policy_version=str(policy.get("policy_version", "lab003-access-1")),
        restricted_type=restricted.restricted_type,
        now=stamp,
    )

    events: List[EvaluationEvent] = []
    events.append(
        _event(
            "request.received",
            now=stamp,
            summary="Access request {0} received at Cedar Quill Markets gateway.".format(
                request.request_id
            ),
        )
    )
    events.append(
        _event(
            "agent.discovered",
            now=stamp,
            summary=profiler_fragment.summary,
            fragment=profiler_fragment,
        )
    )

    authority_boundary_failed = False
    for event_type, stage in EVALUATION_EVENT_STAGES:
        fragment = fragments_by_stage[stage]
        if authority_boundary_failed:
            events.append(
                _event(
                    event_type,
                    now=stamp,
                    summary="Evaluation skipped because authority boundary already failed.",
                    status="skipped",
                    skip_reason="authority_boundary_already_failed",
                    fragment=fragment,
                )
            )
            continue
        events.append(
            _event(
                event_type,
                now=stamp,
                summary=fragment.summary,
                fragment=fragment,
            )
        )
        if fragment.hard_authority_failure:
            authority_boundary_failed = True

    events.append(
        _event(
            "decision.produced",
            now=stamp,
            summary="Trust gateway decision: {0} ({1}).".format(decision, reason_code),
        )
    )
    if restricted.available:
        events.append(
            _event(
                "restricted_path.recommended",
                now=stamp,
                summary=restricted.explanation,
            )
        )
    events.append(
        _event(
            "audit.completed",
            now=stamp,
            summary="Audit record {0} written (execution not performed).".format(
                audit.audit_id
            ),
        )
    )

    valid_until = None
    if decision == "allow":
        ttl = int(policy.get("allow_ttl_seconds", 60))
        valid_until = _stamp(stamp + timedelta(seconds=ttl))

    return EvaluationResult(
        decision=decision,
        reason_code=reason_code,
        reason_category=reason_category_for(reason_code),  # type: ignore[arg-type]
        explanation=explanation,
        violated_constraint=violated,
        delegation_path=delegation.chain_path,
        profile_summary=ProfileSummary(
            classification=profile.classification,
            confidence=profile.confidence,
            profile_mismatch=profile.profile_mismatch,
            profile_status=profile.profile_status,
        ),
        posture_summary=PostureSummary(
            status=posture.posture_status,
            evidence_freshness=posture.evidence_freshness,
            risk_level=posture.risk_level,
        ),
        audit_id=audit.audit_id,
        evaluated_at=_stamp(stamp),
        decision_valid_until=valid_until,
        restricted=restricted,
        execution="not_performed",
        events=events,
        request_fingerprint=_fingerprint(request),
        chain_version=delegation.chain_version,
        profile_version=profile.profile_version,
        posture_version=posture.posture_version,
        policy_version=str(policy.get("policy_version", "lab003-access-1")),
        scenario_id=scenario_id,
    )
