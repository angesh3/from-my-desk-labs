"""Audit evidence tests."""

from __future__ import annotations

from delegated_authority.loader import load_bundle
from delegated_authority.service import evaluate_scenario


def test_every_decision_produces_audit_and_versions():
    for scenario_id in load_bundle().scenarios:
        result = evaluate_scenario(load_bundle(), scenario_id)
        assert result.audit_id
        assert result.policy_version
        assert result.chain_version is not None or result.decision == "deny"
        assert result.profile_version
        assert result.posture_version
        assert result.posture_summary.evidence_freshness
        assert result.execution == "not_performed"
        # Sanitized: no credential/attestation blobs in response model fields
        payload = result.model_dump()
        text = str(payload)
        assert "credential_material" not in text
        assert "attestation_blob" not in text
