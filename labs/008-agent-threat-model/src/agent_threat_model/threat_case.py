"""Deterministic threat-case evaluation for Lab 008."""

from __future__ import annotations

import uuid
from typing import List, Optional, Set, Tuple

from .models import (
    ControlCoverage,
    ControlItem,
    ControlStatus,
    CrossCuttingDimension,
    EvaluateRequest,
    EvaluateResponse,
    ExposureLevel,
    Impact,
    Likelihood,
    OrganizationalExposure,
    RiskLevel,
    ThreatSurface,
)
from .risk import classify_risk

POLICY_VERSION = "lab008-threat-model-v1"

_SURFACE_CODES = {
    ThreatSurface.identity: "surface.identity",
    ThreatSurface.authority: "surface.authority",
    ThreatSurface.instructions: "surface.instructions",
    ThreatSurface.memory_context: "surface.memory_context",
    ThreatSurface.tools_execution: "surface.tools_execution",
    ThreatSurface.delegation: "surface.delegation",
    ThreatSurface.evidence_control: "surface.evidence_control",
}

_DIMENSION_CODES = {
    CrossCuttingDimension.behavior_usage_drift: "dimension.behavior_usage_drift",
    CrossCuttingDimension.learning_memory_drift: "dimension.learning_memory_drift",
    CrossCuttingDimension.external_model_exposure: "dimension.external_model_exposure",
    CrossCuttingDimension.network_resource_impact: "dimension.network_resource_impact",
}


def _new_id() -> str:
    return f"eval-cq-008-{uuid.uuid4().hex[:12]}"


def _uniq(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _all_controls(request: EvaluateRequest) -> List[ControlItem]:
    return (
        list(request.preventive_controls)
        + list(request.detective_controls)
        + list(request.containment_controls)
        + list(request.recovery_controls)
    )


def _material_gaps(controls: List[ControlItem]) -> List[str]:
    gaps: List[str] = []
    for item in controls:
        if item.status in {
            ControlStatus.missing,
            ControlStatus.ineffective,
            ControlStatus.unknown,
        }:
            gaps.append(
                f"{item.category.value}:{item.control_id} ({item.status.value}) — {item.name}"
            )
    return gaps


def _coverage(
    controls: List[ControlItem],
    *,
    independent_evidence_sufficient: bool,
    evidence_gaps: List[str],
    agent_self_report_only: bool,
) -> Tuple[ControlCoverage, List[str]]:
    codes: List[str] = []
    if agent_self_report_only or (
        not independent_evidence_sufficient and evidence_gaps
    ):
        codes.append("evidence.incomplete")
        codes.append("assessment.unverified")
        return ControlCoverage.unverified, codes

    if not independent_evidence_sufficient:
        codes.append("evidence.incomplete")
        codes.append("assessment.unverified")
        return ControlCoverage.unverified, codes

    if not controls:
        codes.append("assessment.none")
        return ControlCoverage.none, codes

    present = [c for c in controls if c.status == ControlStatus.present]
    gaps = [
        c
        for c in controls
        if c.status
        in {ControlStatus.missing, ControlStatus.ineffective, ControlStatus.unknown}
    ]

    if present and not gaps:
        codes.append(
            "control.preventive.present"
            if any(c.category.value == "preventive" for c in present)
            else "assessment.complete"
        )
        codes.append("evidence.independent_present")
        codes.append("assessment.complete")
        return ControlCoverage.complete, codes

    if not present and gaps:
        if all(c.status == ControlStatus.unknown for c in gaps) and not evidence_gaps:
            codes.append("assessment.unverified")
            return ControlCoverage.unverified, codes
        if all(
            c.status in {ControlStatus.missing, ControlStatus.ineffective}
            for c in gaps
        ) or any(c.status == ControlStatus.missing for c in gaps):
            codes.append("assessment.none")
            return ControlCoverage.none, codes
        codes.append("assessment.unverified")
        return ControlCoverage.unverified, codes

    if present and gaps:
        codes.append("assessment.partial")
        if any(c.status == ControlStatus.missing for c in gaps):
            codes.append("control.detective.missing")
        return ControlCoverage.partial, codes

    codes.append("assessment.unverified")
    return ControlCoverage.unverified, codes


def _residual(
    request: EvaluateRequest,
    coverage: ControlCoverage,
) -> Tuple[Optional[Likelihood], Optional[Impact], RiskLevel, str, List[str]]:
    codes: List[str] = []
    if coverage == ControlCoverage.unverified:
        codes.append("risk.residual_unknown")
        return (
            None,
            None,
            RiskLevel.unknown,
            "Independent evidence is insufficient to determine residual risk for this fictional case.",
            codes,
        )

    likelihood = request.residual_likelihood
    impact = request.residual_impact

    if likelihood is None or impact is None:
        if coverage == ControlCoverage.complete:
            likelihood = Likelihood.low
            impact = (
                Impact.medium
                if request.initial_impact in {Impact.high, Impact.critical}
                else request.initial_impact
            )
            if impact == Impact.critical:
                impact = Impact.high
        elif coverage == ControlCoverage.partial:
            likelihood = (
                Likelihood.medium
                if request.initial_likelihood == Likelihood.high
                else request.initial_likelihood
            )
            if likelihood == Likelihood.low:
                likelihood = Likelihood.medium
            impact = request.initial_impact
        else:
            likelihood = request.initial_likelihood
            impact = request.initial_impact

    residual = classify_risk(likelihood, impact)
    if residual == RiskLevel.low:
        codes.append("risk.residual_low")
    elif residual in {RiskLevel.high, RiskLevel.critical}:
        codes.append("risk.residual_high")
    else:
        codes.append(f"risk.residual_{residual.value.lower()}")

    explanation = (
        f"Residual risk is {residual.value} for this fictional scenario after evaluating "
        f"modeled controls and independent evidence (coverage: {coverage.value}). "
        "COMPLETE coverage does not mean zero risk."
    )
    return likelihood, impact, residual, explanation, codes


def _default_exposure(
    request: EvaluateRequest, coverage: ControlCoverage
) -> OrganizationalExposure:
    if request.organizational_exposure is not None:
        return request.organizational_exposure

    dims = set(request.cross_cutting_dimensions)
    high = ExposureLevel.high
    medium = ExposureLevel.medium
    low = ExposureLevel.low
    none = ExposureLevel.none
    unknown = ExposureLevel.unknown

    sensitive = high if CrossCuttingDimension.external_model_exposure in dims else medium
    public_model = (
        high
        if CrossCuttingDimension.external_model_exposure in dims
        else none
    )
    credential = (
        high
        if CrossCuttingDimension.network_resource_impact in dims
        else medium
    )
    network = (
        high
        if CrossCuttingDimension.network_resource_impact in dims
        else low
    )
    compute = (
        high
        if CrossCuttingDimension.network_resource_impact in dims
        else medium
    )
    queued = (
        high
        if CrossCuttingDimension.network_resource_impact in dims
        or ThreatSurface.tools_execution
        in ([request.primary_surface] + list(request.secondary_surfaces))
        else low
    )
    memory = (
        high
        if CrossCuttingDimension.learning_memory_drift in dims
        or ThreatSurface.memory_context
        in ([request.primary_surface] + list(request.secondary_surfaces))
        else low
    )
    children = (
        high
        if ThreatSurface.delegation
        in ([request.primary_surface] + list(request.secondary_surfaces))
        else low
    )
    if coverage == ControlCoverage.complete:
        recoverability = low
        telemetry = high
    elif coverage == ControlCoverage.partial:
        recoverability = medium
        telemetry = medium
    elif coverage == ControlCoverage.none:
        recoverability = high
        telemetry = low
    else:
        recoverability = unknown
        telemetry = unknown

    parts = []
    if public_model != none:
        parts.append("public-model transmission")
    if CrossCuttingDimension.behavior_usage_drift in dims:
        parts.append("usage drift beyond approved purpose")
    if CrossCuttingDimension.learning_memory_drift in dims:
        parts.append("learning or memory influencing later privileged work")
    if CrossCuttingDimension.network_resource_impact in dims:
        parts.append("internal network and resource consumption")
    summary = (
        "Organizational exposure includes "
        + (", ".join(parts) if parts else "the modeled surfaces and evidence gaps")
        + " for this fictional Cedar Quill Markets case."
    )
    return OrganizationalExposure(
        sensitive_data=sensitive,
        public_model_transmission=public_model,
        credential_reach=credential,
        internal_network_reach=network,
        compute_token_cost=compute,
        queued_work=queued,
        persistent_memory=memory,
        child_agents=children,
        recoverability=recoverability,
        independent_telemetry=telemetry,
        summary=summary,
    )


def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """Evaluate a fictional agent threat case deterministically."""
    reasons: List[str] = [_SURFACE_CODES[request.primary_surface]]
    for surface in request.secondary_surfaces:
        reasons.append(_SURFACE_CODES[surface])
    for dimension in request.cross_cutting_dimensions:
        reasons.append(_DIMENSION_CODES[dimension])

    initial_risk = classify_risk(request.initial_likelihood, request.initial_impact)
    reasons.append(f"risk.initial_{initial_risk.value.lower()}")

    controls = _all_controls(request)
    for item in controls:
        if item.status == ControlStatus.present:
            reasons.append(f"control.{item.category.value}.present")
        elif item.status == ControlStatus.missing:
            reasons.append(f"control.{item.category.value}.missing")
        elif item.status == ControlStatus.ineffective:
            reasons.append(f"control.{item.category.value}.ineffective")
        else:
            reasons.append(f"control.{item.category.value}.unknown")

    independent_sources = [
        s
        for s in request.evidence_sources
        if "self-report" not in s.lower() and "self_report" not in s.lower()
    ]
    agent_self_report_only = request.agent_self_report_present and not independent_sources

    independent_ok = (
        request.independent_evidence_sufficient
        and not agent_self_report_only
        and bool(independent_sources or not request.agent_self_report_present)
    )
    if not request.independent_evidence_sufficient:
        independent_ok = False

    coverage, coverage_codes = _coverage(
        controls,
        independent_evidence_sufficient=independent_ok,
        evidence_gaps=list(request.evidence_gaps),
        agent_self_report_only=agent_self_report_only,
    )
    reasons.extend(coverage_codes)

    if request.agent_self_report_present:
        reasons.append("evidence.agent_self_report_preserved")
        if agent_self_report_only:
            reasons.append("evidence.self_report_not_independent")

    residual_likelihood, residual_impact, residual_risk, residual_explain, residual_codes = (
        _residual(request, coverage)
    )
    reasons.extend(residual_codes)
    reasons.append("execution.not_performed")

    gaps = _material_gaps(controls)
    if request.evidence_gaps:
        for gap in request.evidence_gaps:
            gaps.append(f"evidence:{gap}")

    recommendations: List[str] = []
    recommended_controls: List[str] = []
    recommended_evidence: List[str] = []

    if coverage == ControlCoverage.none:
        recommendations.append(
            "Introduce preventive controls on the primary trust boundary before privileged execution."
        )
        recommendations.append(
            "Add detective telemetry that can independently observe the modeled threat path."
        )
    elif coverage == ControlCoverage.partial:
        recommendations.append(
            "Close material control gaps on the primary threat surface before expanding agent scope."
        )
        recommendations.append(
            "Bind authorization to intent, action, target, purpose, and validity window—not only tool endpoints."
        )
    elif coverage == ControlCoverage.unverified:
        recommendations.append(
            "Collect independent evidence across runtime, credentials, delegates, queues, and network paths."
        )
        recommendations.append(
            "Do not treat agent self-report as verification of control effectiveness."
        )
    else:
        recommendations.append(
            "Maintain independent evidence collection; COMPLETE coverage is time-bounded and not zero risk."
        )
        recommendations.append(
            "Re-evaluate residual risk when authority, memory, tools, or delegation change."
        )

    surfaces = [request.primary_surface] + list(request.secondary_surfaces)
    if ThreatSurface.delegation in surfaces:
        recommendations.append(
            "Ensure delegated authority narrows at every handoff and cannot expand."
        )
        recommended_controls.append("Delegation narrowing and revoke-on-expansion")
    if ThreatSurface.memory_context in surfaces:
        recommendations.append(
            "Treat persistent memory and retrieved content as untrusted data until validated."
        )
        recommended_controls.append("Memory integrity labeling and privileged-task gates")

    dims = set(request.cross_cutting_dimensions)
    if CrossCuttingDimension.behavior_usage_drift in dims:
        recommended_controls.append("Purpose-bound authorization and usage-drift detection")
        recommended_evidence.append("Purpose-vs-activity correlation across sessions")
        recommendations.append(
            "Detect gradual usage drift that exceeds the approved business purpose."
        )
    if CrossCuttingDimension.learning_memory_drift in dims:
        recommended_controls.append("Reviewed learning promotion and memory lifetime limits")
        recommended_evidence.append("Cross-session memory provenance for privileged tasks")
        recommendations.append(
            "Separate behavioral/memory drift from model-weight drift; require review before learning becomes instruction."
        )
    if CrossCuttingDimension.external_model_exposure in dims:
        recommended_controls.append("Approved-model allowlist and sensitive-context egress controls")
        recommended_evidence.append("Public-model call logs with payload classification")
        recommendations.append(
            "Block unapproved public-model endpoints and classify data before external inference."
        )
    if CrossCuttingDimension.network_resource_impact in dims:
        recommended_controls.append("Network egress, credential blast-radius, and resource budgets")
        recommended_evidence.append("API, token, compute, queue, and lateral-movement telemetry")
        recommendations.append(
            "Bound agent credential reach, internal network expansion, and cost amplification."
        )

    recommended_controls.append("Independent evidence collection outside the agent runtime")
    recommended_evidence.append("Independent control-plane and telemetry evidence")
    if not recommended_evidence:
        recommended_evidence.append("Runtime, credential, queue, and network evidence planes")

    blast = list(request.organizational_blast_radius)
    if not blast:
        if CrossCuttingDimension.external_model_exposure in dims:
            blast.append("Sensitive context may leave organizational control via public models")
        if CrossCuttingDimension.network_resource_impact in dims:
            blast.append("Internal services, credentials, queues, and compute budgets")
        if CrossCuttingDimension.learning_memory_drift in dims:
            blast.append("Later privileged tasks influenced by earlier unreviewed learning")
        if CrossCuttingDimension.behavior_usage_drift in dims:
            blast.append("Approved capability reused for unapproved business purpose")
        if not blast:
            blast.append("Modeled trust boundaries for the selected threat surfaces")

    exposure = _default_exposure(request, coverage)

    assumptions = [
        "The scenario uses fictional Cedar Quill Markets identities, assets, and evidence.",
        "Control statuses and evidence references are supplied as educational inputs.",
        "Risk categories are illustrative and are not a production risk certification.",
        "Behavioral drift is distinct from model-weight drift; memory updates are not retraining.",
    ]
    limitations = [
        "This Lab is an educational prototype, not a production threat-modeling or scanning system.",
        "COMPLETE control coverage does not mean zero risk.",
        "Agent self-report is preserved but never counts as independent verification by itself.",
        "No real tool, credential, runtime, or network path is evaluated or modified.",
        "Every evaluation returns execution: not_performed.",
        "Availability impact and security compromise are related but not identical.",
    ]

    summary = (
        f"{request.title}: initial risk {initial_risk.value}; "
        f"control coverage {coverage.value}; residual risk {residual_risk.value}."
    )
    explanation = (
        "An autonomous agent is not only a model. This fictional evaluation maps assets, "
        "trust boundaries, threat paths, controls, cross-cutting dimensions, and independent "
        "evidence across identity, authority, instructions, memory, tools, delegation, and control. "
        f"{residual_explain} Real execution is not_performed."
    )

    return EvaluateResponse(
        evaluation_id=_new_id(),
        case_id=request.case_id,
        preset_id=request.preset_id,
        title=request.title,
        primary_surface=request.primary_surface,
        secondary_surfaces=list(request.secondary_surfaces),
        cross_cutting_dimensions=list(request.cross_cutting_dimensions),
        initial_likelihood=request.initial_likelihood,
        initial_impact=request.initial_impact,
        initial_risk=initial_risk,
        control_coverage=coverage,
        residual_likelihood=residual_likelihood,
        residual_impact=residual_impact,
        residual_risk=residual_risk,
        residual_risk_explanation=residual_explain,
        material_gaps=_uniq(gaps),
        organizational_blast_radius=_uniq(blast),
        organizational_exposure=exposure,
        recommended_actions=_uniq(recommendations),
        recommended_controls=_uniq(recommended_controls),
        recommended_evidence=_uniq(recommended_evidence),
        assumptions=assumptions,
        limitations=limitations,
        reason_codes=_uniq(reasons),
        summary=summary,
        explanation=explanation,
        preventive_controls=list(request.preventive_controls),
        detective_controls=list(request.detective_controls),
        containment_controls=list(request.containment_controls),
        recovery_controls=list(request.recovery_controls),
        evidence_gaps=list(request.evidence_gaps),
        execution="not_performed",
        policy_version=POLICY_VERSION,
    )
