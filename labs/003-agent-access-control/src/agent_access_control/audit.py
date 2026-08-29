"""Fictional audit evidence for Lab 003 evaluations."""

from __future__ import annotations

import itertools
from datetime import datetime, timezone
from typing import Optional

from .models import (
    AccessRequest,
    AgentProfile,
    AuditRecord,
    Decision,
    DelegationResult,
    PostureEvidence,
)

_counter = itertools.count(1)


def reset_audit_counter() -> None:
    global _counter
    _counter = itertools.count(1)


def create_audit_record(
    request: AccessRequest,
    decision: Decision,
    reason_code: str,
    registration_state: str,
    delegation: DelegationResult,
    profile: AgentProfile,
    posture: PostureEvidence,
    policy_version: str,
    restricted_type: str,
    now: Optional[datetime] = None,
) -> AuditRecord:
    stamp = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    audit_id = "audit_demo_{0:04d}".format(next(_counter))
    return AuditRecord(
        audit_id=audit_id,
        request_id=request.request_id,
        timestamp=stamp,
        principal_reference="principal_ref",
        agent_reference="agent_ref",
        registration_state=registration_state,
        delegation_chain_reference=request.delegation_id,
        delegation_chain_version=delegation.chain_version,
        ape_profile_status=profile.profile_status,
        ape_profile_version=profile.profile_version,
        apse_posture_status=posture.posture_status,
        apse_posture_version=posture.posture_version,
        evidence_freshness=posture.evidence_freshness,
        policy_version=policy_version,
        decision=decision,
        reason_code=reason_code,
        restricted_path_offered=restricted_type,
        execution="not_performed",
    )
