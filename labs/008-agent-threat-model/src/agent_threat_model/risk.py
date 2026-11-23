"""Deterministic categorical risk matrix for Lab 008."""

from __future__ import annotations

from .models import Impact, Likelihood, RiskLevel

# likelihood x impact -> risk
RISK_MATRIX = {
    (Likelihood.low, Impact.low): RiskLevel.low,
    (Likelihood.low, Impact.medium): RiskLevel.low,
    (Likelihood.low, Impact.high): RiskLevel.medium,
    (Likelihood.low, Impact.critical): RiskLevel.high,
    (Likelihood.medium, Impact.low): RiskLevel.low,
    (Likelihood.medium, Impact.medium): RiskLevel.medium,
    (Likelihood.medium, Impact.high): RiskLevel.high,
    (Likelihood.medium, Impact.critical): RiskLevel.critical,
    (Likelihood.high, Impact.low): RiskLevel.medium,
    (Likelihood.high, Impact.medium): RiskLevel.high,
    (Likelihood.high, Impact.high): RiskLevel.critical,
    (Likelihood.high, Impact.critical): RiskLevel.critical,
}


def classify_risk(likelihood: Likelihood, impact: Impact) -> RiskLevel:
    """Return categorical risk from the documented matrix."""
    return RISK_MATRIX[(likelihood, impact)]
