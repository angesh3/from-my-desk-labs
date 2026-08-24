"""Delegated-authority chain evaluator."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .models import ActionRequest, DelegationEnvelope, DelegationResult, as_decimal


def parse_delegation(raw: Dict[str, Any]) -> DelegationEnvelope:
    return DelegationEnvelope.model_validate(raw)


def evaluate_delegation(
    request: ActionRequest,
    delegations: Dict[str, Dict[str, Any]],
    display_names: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None,
) -> DelegationResult:
    display = display_names or {}
    leaf_id = request.delegation_id
    if leaf_id not in delegations:
        return DelegationResult(
            chain_status="broken",
            chain_path=["Human Principal", "Unknown"],
            effective_capabilities=[],
            effective_resources=[],
            violated_constraint="delegation_chain_broken",
            reason_code="delegation_chain_broken",
        )

    chain: List[DelegationEnvelope] = []
    current_id: Optional[str] = leaf_id
    seen = set()
    while current_id:
        if current_id in seen:
            return DelegationResult(
                chain_status="broken",
                chain_path=["Human Principal"],
                effective_capabilities=[],
                effective_resources=[],
                violated_constraint="delegation_chain_broken",
                reason_code="delegation_chain_broken",
            )
        seen.add(current_id)
        raw = delegations.get(current_id)
        if raw is None:
            return DelegationResult(
                chain_status="broken",
                chain_path=_path_labels(chain, display, include_tool=True),
                effective_capabilities=[],
                effective_resources=[],
                violated_constraint="delegation_chain_broken",
                reason_code="delegation_chain_broken",
            )
        envelope = parse_delegation(raw)
        chain.append(envelope)
        current_id = envelope.parent_delegation_id

    # chain is leaf → root; reverse for parent→child checks
    chain_root_first = list(reversed(chain))
    path = _path_labels(chain, display, include_tool=True)

    for parent, child in zip(chain_root_first, chain_root_first[1:]):
        violation = _parent_child_violation(parent, child)
        if violation:
            code, constraint = violation
            return DelegationResult(
                chain_status="constraint_violation",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                violated_constraint=constraint,
                chain_version=_chain_version(chain),
                reason_code=code,
            )

    for node in chain_root_first:
        if node.status == "revoked":
            return DelegationResult(
                chain_status="revoked",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                violated_constraint="parent_revoked",
                chain_version=_chain_version(chain),
                reason_code="parent_revoked",
            )
        if node.status == "expired":
            return DelegationResult(
                chain_status="expired",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                violated_constraint="parent_expired",
                chain_version=_chain_version(chain),
                reason_code="parent_expired",
            )

    leaf = chain[0]
    if leaf.delegate_id != request.agent_id:
        return DelegationResult(
            chain_status="broken",
            chain_path=path,
            effective_capabilities=[],
            effective_resources=[],
            violated_constraint="delegation_chain_broken",
            chain_version=_chain_version(chain),
            reason_code="delegation_chain_broken",
        )

    effective_caps = set(leaf.capabilities)
    effective_resources = set(leaf.resources)
    effective_limit = leaf.maximum_amount
    effective_expiry = leaf.valid_until
    redelegation = leaf.may_redelegate
    for node in chain_root_first:
        effective_caps &= set(node.capabilities)
        effective_resources &= set(node.resources)
        effective_limit = min(effective_limit, node.maximum_amount)
        if node.valid_until < effective_expiry:
            effective_expiry = node.valid_until
        redelegation = redelegation and node.may_redelegate

    if request.requested_capability not in effective_caps:
        return DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_capability_not_in_effective_capabilities",
            chain_version=_chain_version(chain),
            reason_code="capability_not_delegated",
        )
    if request.requested_resource not in effective_resources:
        return DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_resource_not_in_effective_resources",
            chain_version=_chain_version(chain),
            reason_code="capability_not_delegated",
        )

    amount = as_decimal(request.requested_amount)
    if amount > effective_limit:
        return DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_amount_exceeds_effective_limit",
            chain_version=_chain_version(chain),
            reason_code="child_limit_exceeds_parent",
        )

    return DelegationResult(
        chain_status="valid",
        chain_path=path,
        effective_capabilities=sorted(effective_caps),
        effective_resources=sorted(effective_resources),
        effective_limit=str(effective_limit),
        effective_expiry=effective_expiry,
        redelegation_allowed=redelegation,
        chain_version=_chain_version(chain),
        reason_code=None,
    )


def _parent_child_violation(
    parent: DelegationEnvelope, child: DelegationEnvelope
) -> Optional[Tuple[str, str]]:
    if not set(child.capabilities).issubset(set(parent.capabilities)):
        return ("child_capability_exceeds_parent", "child_capability_exceeds_parent")
    if not set(child.resources).issubset(set(parent.resources)):
        return ("child_resource_exceeds_parent", "child_resource_exceeds_parent")
    if child.maximum_amount > parent.maximum_amount:
        return ("child_limit_exceeds_parent", "child_limit_exceeds_parent")
    if child.valid_until > parent.valid_until:
        return ("child_expiry_exceeds_parent", "child_expiry_exceeds_parent")
    if not parent.may_redelegate:
        return ("redelegation_prohibited", "redelegation_prohibited")
    if child.remaining_depth > parent.remaining_depth - 1 and parent.remaining_depth >= 0:
        # Child remaining depth must be within parent remaining depth after this hop.
        if parent.remaining_depth <= 0:
            return ("delegation_depth_exceeded", "delegation_depth_exceeded")
        if child.remaining_depth >= parent.remaining_depth:
            return ("delegation_depth_exceeded", "delegation_depth_exceeded")
    if parent.remaining_depth <= 0:
        return ("delegation_depth_exceeded", "delegation_depth_exceeded")
    return None


def _chain_version(chain: List[DelegationEnvelope]) -> str:
    return "+".join(item.version for item in reversed(chain))


def _path_labels(
    chain_leaf_first: List[DelegationEnvelope],
    display: Dict[str, str],
    include_tool: bool,
) -> List[str]:
    labels = ["Human Principal"]
    for envelope in reversed(chain_leaf_first):
        labels.append(display.get(envelope.delegate_id, envelope.delegate_id))
    if include_tool:
        labels.append("Requested Tool")
    return labels


def assert_child_subset(
    parent_caps: List[str],
    child_caps: List[str],
    parent_resources: List[str],
    child_resources: List[str],
    parent_limit: Decimal,
    child_limit: Decimal,
    parent_expiry: str,
    child_expiry: str,
) -> List[str]:
    """Return violated constraint codes for parent/child comparisons."""
    violations: List[str] = []
    if not set(child_caps).issubset(set(parent_caps)):
        violations.append("child_capability_exceeds_parent")
    if not set(child_resources).issubset(set(parent_resources)):
        violations.append("child_resource_exceeds_parent")
    if child_limit > parent_limit:
        violations.append("child_limit_exceeds_parent")
    if child_expiry > parent_expiry:
        violations.append("child_expiry_exceeds_parent")
    return violations
