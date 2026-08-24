"""Orchestrate Lab 002 scenario evaluation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .audit import create_audit_record
from .delegation import evaluate_delegation
from .fallback import recommend_fallback
from .identity import evaluate_identity
from .loader import Lab002Bundle, materialize_scenario
from .management import AgentManagementPlane
from .models import (
    ActionRequest,
    EvaluationResult,
    JourneyStep,
    ProfileSummary,
    PostureSummary,
    ScenarioMeta,
)
from .policy import decide, reason_category_for
from .posture import evaluate_posture
from .profiler import evaluate_profile


def _fingerprint(request: ActionRequest) -> str:
    raw = "|".join(
        [
            request.request_id,
            request.principal_id,
            request.agent_id,
            request.requested_capability,
            request.requested_resource,
            str(request.requested_amount),
            request.delegation_id,
            request.context,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def list_scenarios(bundle: Lab002Bundle) -> List[ScenarioMeta]:
    return bundle.scenario_meta()


def evaluate_scenario(
    bundle: Lab002Bundle,
    scenario_id: str,
    now: Optional[datetime] = None,
) -> EvaluationResult:
    scenario, agents, profiles, posture_map, delegations = materialize_scenario(
        bundle, scenario_id
    )
    stamp = now or datetime.now(timezone.utc)
    request_raw = scenario["request"]
    request = ActionRequest.model_validate(request_raw)

    management = AgentManagementPlane(agents)
    identity = evaluate_identity(request, agents, now=stamp)
    display = {
        agent_id: str(raw.get("display_name", agent_id))
        for agent_id, raw in agents.items()
    }
    delegation = evaluate_delegation(
        request, delegations, display_names=display, now=stamp
    )
    profile = evaluate_profile(request, profiles, management, now=stamp)
    posture = evaluate_posture(request, posture_map, management, now=stamp)

    policy = bundle.policies.get("delegation") or {}
    decision, reason_code, violated, explanation = decide(
        request, identity, delegation, profile, posture, policy
    )
    fallback = recommend_fallback(reason_code)
    audit = create_audit_record(
        request=request,
        decision=decision,
        reason_code=reason_code,
        delegation=delegation,
        profile=profile,
        posture=posture,
        policy_version=str(policy.get("policy_version", "lab002-delegation-1")),
        fallback_type=fallback.fallback_type,
        now=stamp,
    )

    journey = [
        JourneyStep(
            stage="identity",
            status=identity.identity_status,
            summary="Identity {0}; principal binding {1}.".format(
                identity.identity_status, identity.principal_binding
            ),
        ),
        JourneyStep(
            stage="delegation",
            status=delegation.chain_status,
            summary="Delegation chain {0}.".format(delegation.chain_status),
        ),
        JourneyStep(
            stage="ape",
            status=profile.profile_status,
            summary="APE classification {0} (confidence {1}).".format(
                profile.classification, profile.confidence
            ),
        ),
        JourneyStep(
            stage="apse",
            status=posture.posture_status,
            summary="APSE posture {0}; evidence {1}.".format(
                posture.posture_status, posture.evidence_freshness
            ),
        ),
        JourneyStep(
            stage="policy",
            status=decision,
            summary="Trust gateway decision: {0} ({1}).".format(decision, reason_code),
        ),
    ]

    valid_until = None
    if decision == "allow":
        ttl = int(policy.get("allow_ttl_seconds", 60))
        valid_until = (stamp + timedelta(seconds=ttl)).isoformat().replace("+00:00", "Z")

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
        evaluated_at=stamp.isoformat().replace("+00:00", "Z"),
        decision_valid_until=valid_until,
        fallback=fallback,
        execution="not_performed",
        journey=journey,
        request_fingerprint=_fingerprint(request),
        chain_version=delegation.chain_version,
        profile_version=profile.profile_version,
        posture_version=posture.posture_version,
        policy_version=str(policy.get("policy_version", "lab002-delegation-1")),
        scenario_id=scenario_id,
    )


def scenario_input_summary(
    bundle: Lab002Bundle, scenario_id: str
) -> Dict[str, Any]:
    scenario, agents, profiles, posture_map, delegations = materialize_scenario(
        bundle, scenario_id
    )
    request = scenario["request"]
    agent_id = request["agent_id"]
    agent = agents.get(agent_id) or {}
    profile = profiles.get(agent_id) or {}
    posture = posture_map.get(agent_id) or {}
    leaf = delegations.get(request["delegation_id"]) or {}
    parent_id = leaf.get("parent_delegation_id")
    parent = delegations.get(parent_id) if parent_id else None
    return {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "requested_capability": request["requested_capability"],
        "requested_resource": request["requested_resource"],
        "requested_amount": str(request["requested_amount"]),
        "request_time": request["request_time"],
        "agent_classification": profile.get("classification")
        or agent.get("classification")
        or "unknown",
        "profile_confidence": profile.get("confidence", "low"),
        "posture_status": posture.get("posture_status", "unknown"),
        "parent_delegation_status": (parent or {}).get("status", "n/a"),
        "request_json": request,
        "chain_preview": scenario.get("chain_preview") or [],
    }
