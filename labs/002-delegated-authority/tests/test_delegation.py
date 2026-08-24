"""Delegation parent-child constraint tests."""

from __future__ import annotations

from decimal import Decimal

from delegated_authority.delegation import assert_child_subset, evaluate_delegation
from delegated_authority.loader import load_bundle
from delegated_authority.models import ActionRequest


def _req(**overrides):
    base = dict(
        request_id="req-t",
        principal_id="principal-demo-001",
        agent_id="research-agent-001",
        requested_capability="research",
        requested_resource="market-summaries",
        requested_amount="100.00",
        request_time="2026-03-15T14:00:00Z",
        delegation_id="del-portfolio-research",
        context="normal",
    )
    base.update(overrides)
    return ActionRequest.model_validate(base)


def test_child_subset_helpers():
    assert assert_child_subset(
        ["research", "propose"],
        ["research"],
        ["a", "b"],
        ["a"],
        Decimal("100"),
        Decimal("50"),
        "2026-12-31",
        "2026-06-30",
    ) == []
    assert "child_capability_exceeds_parent" in assert_child_subset(
        ["research"], ["research", "execute"], ["a"], ["a"], Decimal("10"), Decimal("5"), "2026", "2025"
    )
    assert "child_resource_exceeds_parent" in assert_child_subset(
        ["research"], ["research"], ["a"], ["a", "b"], Decimal("10"), Decimal("5"), "2026", "2025"
    )
    assert "child_limit_exceeds_parent" in assert_child_subset(
        ["research"], ["research"], ["a"], ["a"], Decimal("10"), Decimal("20"), "2026", "2025"
    )
    assert "child_expiry_exceeds_parent" in assert_child_subset(
        ["research"], ["research"], ["a"], ["a"], Decimal("10"), Decimal("5"), "2026-01-01", "2027-01-01"
    )


def test_requested_capability_must_be_delegated():
    bundle = load_bundle()
    result = evaluate_delegation(
        _req(requested_capability="execute"),
        bundle.delegations,
    )
    assert result.reason_code == "capability_not_delegated"


def test_parent_revocation_and_expiry():
    bundle = load_bundle()
    revoked = evaluate_delegation(
        _req(delegation_id="del-parent-revoked-child"),
        bundle.delegations,
    )
    assert revoked.reason_code == "parent_revoked"
    expired = evaluate_delegation(
        _req(delegation_id="del-parent-expired-child"),
        bundle.delegations,
    )
    assert expired.reason_code == "parent_expired"


def test_depth_and_capability_exceed():
    bundle = load_bundle()
    depth = evaluate_delegation(
        _req(delegation_id="del-depth-leaf"),
        bundle.delegations,
    )
    assert depth.reason_code == "delegation_depth_exceeded"
    caps = evaluate_delegation(
        _req(delegation_id="del-child-cap-exceeds"),
        bundle.delegations,
    )
    assert caps.reason_code == "child_capability_exceeds_parent"
