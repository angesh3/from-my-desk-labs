"""Deterministic containment-assurance policy for Lab 007."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    REQUIRED_CHECK_IDS,
    AssuranceCheck,
    AssuranceStatus,
    AttemptedEnforcement,
    CheckOutcome,
    EvaluatedCheck,
    EvaluateRequest,
    EvaluateResponse,
    EvidenceFreshness,
    EvidenceSource,
)

POLICY_VERSION = "lab007-assurance-v1"

_STATUS_RANK = {
    AssuranceStatus.confirmed: 0,
    AssuranceStatus.unverified: 1,
    AssuranceStatus.partial: 2,
    AssuranceStatus.failed: 3,
}

# Observed states that indicate the control is NOT in the contained condition.
_BAD_OBSERVED = {
    "primary_runtime_stopped": {"running", "restarting", "unknown"},
    "active_sessions_revoked": {"active", "partially_active", "unknown"},
    "delegated_credentials_revoked": {"valid", "cached_valid", "unknown"},
    "tool_access_disabled": {"enabled", "partially_enabled", "unknown"},
    "queued_actions_cancelled": {"executable", "pending", "unknown"},
    "scheduled_work_cancelled": {"scheduled", "pending", "unknown"},
    "child_agents_stopped": {"running", "processing", "unknown"},
    "network_egress_blocked": {"open", "partially_open", "unknown"},
    "alternate_network_paths_checked": {"open", "reachable", "unknown"},
    "persistent_state_quarantined": {"available", "retained", "unknown"},
    "restart_recovery_disabled": {"enabled", "active", "unknown"},
    "telemetry_coverage_complete": {"incomplete", "partial", "unknown"},
    "evidence_freshness_acceptable": {"stale", "unknown"},
    "evidence_source_independence": {"agent_only", "insufficient", "unknown"},
    "post_containment_activity_absent": {"detected", "present", "unknown"},
}

# Residual-path capable checks (PARTIAL when fail without continued execution)
_RESIDUAL_CHECKS = {
    "delegated_credentials_revoked",
    "queued_actions_cancelled",
    "scheduled_work_cancelled",
    "tool_access_disabled",
    "alternate_network_paths_checked",
    "persistent_state_quarantined",
    "active_sessions_revoked",
    "network_egress_blocked",
}

# Continued-execution indicators (FAILED)
_CONTINUED_EXECUTION_CHECKS = {
    "child_agents_stopped",
    "primary_runtime_stopped",
    "restart_recovery_disabled",
    "post_containment_activity_absent",
}


def _new_id() -> str:
    return f"eval-cq-007-{uuid.uuid4().hex[:12]}"


def _raise(current: AssuranceStatus, candidate: AssuranceStatus) -> AssuranceStatus:
    if _STATUS_RANK[candidate] > _STATUS_RANK[current]:
        return candidate
    return current


def _is_independent(source: EvidenceSource) -> bool:
    return source == EvidenceSource.independent_control_plane


def _evaluate_check(check: AssuranceCheck) -> EvaluatedCheck:
    """Evaluate one assurance check deterministically."""
    cid = check.check_id
    observed = check.observed_state.strip().lower()
    expected = check.expected_state.strip().lower()
    reasons: List[str] = []

    # Agent self-report alone is never sufficient independent evidence.
    if check.evidence_source == EvidenceSource.agent_self_report:
        return EvaluatedCheck(
            check_id=cid,
            expected_state=check.expected_state,
            observed_state=check.observed_state,
            evidence_reference=check.evidence_reference,
            evidence_freshness=check.evidence_freshness,
            evidence_source=check.evidence_source,
            check_result=CheckOutcome.missing,
            reason=check.reason
            or "Agent self-report is not independent assurance evidence.",
        )

    if (
        check.evidence_source in {EvidenceSource.none, EvidenceSource.partial_telemetry}
        or not check.evidence_reference
        or check.evidence_freshness == EvidenceFreshness.unknown
        or observed in {"unknown", "incomplete"}
    ):
        # Incomplete independent evidence → missing (feeds UNVERIFIED unless FAILED wins)
        if observed in _BAD_OBSERVED.get(cid, set()) - {"unknown"} and _is_independent(
            check.evidence_source
        ):
            # Known bad state with some independent signal still fails the check
            return EvaluatedCheck(
                check_id=cid,
                expected_state=check.expected_state,
                observed_state=check.observed_state,
                evidence_reference=check.evidence_reference,
                evidence_freshness=check.evidence_freshness,
                evidence_source=check.evidence_source,
                check_result=CheckOutcome.fail,
                reason=check.reason
                or f"Observed state '{check.observed_state}' does not meet expected '{check.expected_state}'.",
            )
        return EvaluatedCheck(
            check_id=cid,
            expected_state=check.expected_state,
            observed_state=check.observed_state,
            evidence_reference=check.evidence_reference,
            evidence_freshness=check.evidence_freshness,
            evidence_source=check.evidence_source,
            check_result=CheckOutcome.missing,
            reason=check.reason
            or "Independent evidence is incomplete or telemetry coverage is insufficient.",
        )

    if check.evidence_freshness == EvidenceFreshness.stale:
        return EvaluatedCheck(
            check_id=cid,
            expected_state=check.expected_state,
            observed_state=check.observed_state,
            evidence_reference=check.evidence_reference,
            evidence_freshness=check.evidence_freshness,
            evidence_source=check.evidence_source,
            check_result=CheckOutcome.missing,
            reason=check.reason or "Evidence freshness is stale for the assurance window.",
        )

    if not _is_independent(check.evidence_source):
        return EvaluatedCheck(
            check_id=cid,
            expected_state=check.expected_state,
            observed_state=check.observed_state,
            evidence_reference=check.evidence_reference,
            evidence_freshness=check.evidence_freshness,
            evidence_source=check.evidence_source,
            check_result=CheckOutcome.missing,
            reason=check.reason
            or "Evidence source is not an independent control-plane signal.",
        )

    # Independent, fresh evidence present
    if observed == expected or (
        cid == "post_containment_activity_absent" and observed in {"absent", "none"}
    ):
        result = CheckOutcome.pass_
        reasons.append("Observed state matches the expected contained condition.")
    elif observed in _BAD_OBSERVED.get(cid, set()) or observed != expected:
        result = CheckOutcome.fail
        reasons.append(
            f"Observed state '{check.observed_state}' does not meet expected "
            f"'{check.expected_state}'."
        )
    else:
        result = CheckOutcome.pass_
        reasons.append("Observed state matches the expected contained condition.")

    return EvaluatedCheck(
        check_id=cid,
        expected_state=check.expected_state,
        observed_state=check.observed_state,
        evidence_reference=check.evidence_reference,
        evidence_freshness=check.evidence_freshness,
        evidence_source=check.evidence_source,
        check_result=result,
        reason=check.reason or " ".join(reasons),
    )


def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """Evaluate containment assurance from independent fictional evidence."""
    by_id: Dict[str, AssuranceCheck] = {c.check_id: c for c in request.checks}
    evaluated: List[EvaluatedCheck] = []
    reason_codes: List[str] = []
    residual: List[str] = []
    missing: List[str] = []
    failed: List[str] = []
    passed: List[str] = []

    # Ensure all required dimensions are considered (missing → missing evidence)
    for required in REQUIRED_CHECK_IDS:
        if required not in by_id:
            evaluated.append(
                EvaluatedCheck(
                    check_id=required,
                    expected_state="required",
                    observed_state="missing_from_request",
                    evidence_reference=None,
                    evidence_freshness=EvidenceFreshness.unknown,
                    evidence_source=EvidenceSource.none,
                    check_result=CheckOutcome.missing,
                    reason="Required assurance dimension was not supplied.",
                )
            )
            missing.append(required)
            reason_codes.append(f"evidence.missing.{required}")
        else:
            result = _evaluate_check(by_id[required])
            evaluated.append(result)
            if result.check_result == CheckOutcome.pass_:
                passed.append(required)
            elif result.check_result == CheckOutcome.fail:
                failed.append(required)
            else:
                missing.append(required)
                reason_codes.append(f"evidence.missing.{required}")

    # Extra checks beyond required are also evaluated
    for check in request.checks:
        if check.check_id in REQUIRED_CHECK_IDS:
            continue
        result = _evaluate_check(check)
        evaluated.append(result)
        if result.check_result == CheckOutcome.pass_:
            passed.append(check.check_id)
        elif result.check_result == CheckOutcome.fail:
            failed.append(check.check_id)
        else:
            missing.append(check.check_id)

    status = AssuranceStatus.confirmed
    continued = bool(request.post_containment_activity)

    if request.containment_regression_detected:
        status = AssuranceStatus.failed
        reason_codes.append("assurance.containment_regression")
        residual.append(
            "Previously confirmed containment later restored an execution boundary."
        )

    if continued:
        status = _raise(status, AssuranceStatus.failed)
        reason_codes.append("assurance.post_containment_activity")

    # Map failed checks to residual paths / continued execution
    for check_id in failed:
        item = next(c for c in evaluated if c.check_id == check_id)
        if check_id in _CONTINUED_EXECUTION_CHECKS or (
            check_id == "post_containment_activity_absent"
            and item.observed_state.lower() in {"detected", "present"}
        ):
            status = _raise(status, AssuranceStatus.failed)
            reason_codes.append(f"assurance.continued.{check_id}")
            if check_id == "child_agents_stopped":
                residual.append(
                    f"Delegated child agent still active (observed: {item.observed_state})."
                )
            elif check_id == "restart_recovery_disabled":
                residual.append(
                    f"Restart/recovery path remains enabled (observed: {item.observed_state})."
                )
            elif check_id == "primary_runtime_stopped":
                residual.append(
                    f"Primary runtime not stopped (observed: {item.observed_state})."
                )
            elif check_id == "post_containment_activity_absent":
                residual.append("Post-containment activity was detected.")
            else:
                residual.append(f"{check_id}: {item.observed_state}")
        elif check_id in _RESIDUAL_CHECKS:
            status = _raise(status, AssuranceStatus.partial)
            reason_codes.append(f"assurance.residual.{check_id}")
            residual.append(_residual_label(check_id, item.observed_state))
        else:
            status = _raise(status, AssuranceStatus.partial)
            reason_codes.append(f"assurance.check_failed.{check_id}")
            residual.append(f"{check_id}: {item.observed_state}")

    # Missing evidence → UNVERIFIED unless FAILED already wins.
    # Known continued execution overrides incomplete telemetry (FAILED stays).
    if missing and status != AssuranceStatus.failed:
        # If we only have missing (no fails), UNVERIFIED; if fails already PARTIAL, keep PARTIAL
        if status == AssuranceStatus.confirmed:
            status = AssuranceStatus.unverified
            reason_codes.append("assurance.insufficient_telemetry")
        elif status == AssuranceStatus.partial:
            reason_codes.append("assurance.residual_with_gaps")
        else:
            status = _raise(status, AssuranceStatus.unverified)
            reason_codes.append("assurance.insufficient_telemetry")

    # Agent self-report alone cannot produce CONFIRMED
    if status == AssuranceStatus.confirmed and request.agent_self_report_stopped:
        independent_passes = [
            c
            for c in evaluated
            if c.check_result == CheckOutcome.pass_
            and c.evidence_source == EvidenceSource.independent_control_plane
        ]
        if len(independent_passes) < len(REQUIRED_CHECK_IDS):
            status = AssuranceStatus.unverified
            reason_codes.append("assurance.self_report_insufficient")

    # CONFIRMED requires positive evidence on all required checks
    if status == AssuranceStatus.confirmed:
        if failed or missing:
            status = (
                AssuranceStatus.partial if failed else AssuranceStatus.unverified
            )
        else:
            reason_codes.append("assurance.confirmed_within_window")
            reason_codes.append("evidence.independent_complete")

    if request.attempted_enforcement == AttemptedEnforcement.terminate:
        reason_codes.append("enforcement.terminate_attempted")
    elif request.attempted_enforcement == AttemptedEnforcement.isolate:
        reason_codes.append("enforcement.isolate_attempted")
    else:
        reason_codes.append("enforcement.restrict_attempted")

    containment_effective = status == AssuranceStatus.confirmed
    if request.containment_regression_detected:
        containment_effective = False

    summary, explanation = _summarize(
        request.attempted_enforcement, status, residual, missing, continued
    )

    def uniq(items: List[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    return EvaluateResponse(
        evaluation_id=_new_id(),
        preset_id=request.preset_id,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        agent_id=request.agent_id,
        principal_id=request.principal_id,
        attempted_enforcement=request.attempted_enforcement,
        assurance_status=status,
        containment_effective=containment_effective,
        evaluated_at=request.evaluated_at,
        evidence_window_minutes=request.evidence_window_minutes,
        checks=evaluated,
        passed_checks=uniq(passed),
        failed_checks=uniq(failed),
        missing_evidence=uniq(missing),
        residual_paths=uniq(residual),
        post_containment_activity=list(request.post_containment_activity),
        reason_codes=uniq(reason_codes),
        explanation=explanation,
        summary=summary,
        execution="not_performed",
        policy_version=POLICY_VERSION,
    )


def _residual_label(check_id: str, observed: str) -> str:
    labels = {
        "delegated_credentials_revoked": f"Active or cached credential remains valid ({observed}).",
        "queued_actions_cancelled": f"Executable queued action remains ({observed}).",
        "scheduled_work_cancelled": f"Scheduled work remains pending ({observed}).",
        "tool_access_disabled": f"Tool access remains enabled ({observed}).",
        "alternate_network_paths_checked": f"Alternate network path remains reachable ({observed}).",
        "persistent_state_quarantined": f"Persistent state remains available ({observed}).",
        "active_sessions_revoked": f"Active session remains ({observed}).",
        "network_egress_blocked": f"Network egress remains open ({observed}).",
    }
    return labels.get(check_id, f"{check_id}: {observed}")


def _summarize(
    enforcement: AttemptedEnforcement,
    status: AssuranceStatus,
    residual: List[str],
    missing: List[str],
    continued: bool,
) -> Tuple[str, str]:
    summary = (
        f"Attempted enforcement: {enforcement.value}. "
        f"Assurance status: {status.value}."
    )
    explanation = (
        "Containment action and containment assurance are separate decisions. "
        "An agent must never certify its own containment. "
        "Assurance is produced by an independent control plane using external evidence. "
    )
    if status == AssuranceStatus.confirmed:
        explanation += (
            "All required controls have independent supporting evidence within the "
            "modeled evidence window. CONFIRMED is time-bounded and not absolute proof "
            "that no unknown path exists. "
        )
    elif status == AssuranceStatus.partial:
        explanation += (
            "The primary containment action appears to have succeeded, but residual "
            "capability remains. "
        )
        if residual:
            explanation += "Residual paths: " + "; ".join(residual[:3]) + ". "
    elif status == AssuranceStatus.unverified:
        explanation += (
            "Independent evidence or telemetry is insufficient to determine whether "
            "containment is complete. Absence of observed activity is not positive proof. "
        )
        if missing:
            explanation += f"Missing evidence dimensions: {len(missing)}. "
    else:
        explanation += (
            "A known execution path remains active, post-containment activity was "
            "detected, or containment later regressed. "
        )
        if continued:
            explanation += "Post-containment activity was reported. "
    explanation += "Real execution is not_performed."
    return summary, explanation
