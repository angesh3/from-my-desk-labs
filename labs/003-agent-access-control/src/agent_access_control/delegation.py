"""Delegated-authority chain evaluator for Lab 003."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    AccessRequest,
    DelegationEnvelope,
    DelegationResult,
    EvaluationFragment,
    as_decimal,
)


def parse_delegation(raw: Dict[str, Any]) -> DelegationEnvelope:
    return DelegationEnvelope.model_validate(raw)


def evaluate_delegation(
    request: AccessRequest,
    delegations: Dict[str, Dict[str, Any]],
    display_names: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None,
) -> tuple[DelegationResult, EvaluationFragment]:
    display = display_names or {}
    if request.restricted_operation and request.requested_action == "register":
        result = DelegationResult(
            chain_status="valid",
            chain_path=["Human Principal", "Restricted Registration"],
            effective_capabilities=["register"],
            effective_resources=list(request.requested_resource.split()),
            effective_purposes=["agent_onboarding"],
            effective_data_classification="public",
            effective_limit="0.00",
            effective_expiry="registration-bound",
            redelegation_allowed=False,
            chain_version="restricted-1",
            reason_code=None,
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="restricted",
            summary="No operational delegation is required for restricted registration.",
            details={"chain_status": "restricted_path"},
        )
        return result, fragment

    leaf_id = request.delegation_id
    if leaf_id not in delegations:
        result = DelegationResult(
            chain_status="broken",
            chain_path=["Human Principal", "Unknown"],
            effective_capabilities=[],
            effective_resources=[],
            effective_purposes=[],
            violated_constraint="delegation_chain_broken",
            reason_code="delegation_chain_broken",
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="failed",
            decision_signal="deny",
            reason_code="delegation_chain_broken",
            hard_authority_failure=True,
            summary="Delegation chain is incomplete or unknown.",
            details={"chain_status": "broken"},
        )
        return result, fragment

    chain: List[DelegationEnvelope] = []
    current_id: Optional[str] = leaf_id
    seen = set()
    while current_id:
        if current_id in seen:
            result = DelegationResult(
                chain_status="broken",
                chain_path=["Human Principal"],
                effective_capabilities=[],
                effective_resources=[],
                effective_purposes=[],
                violated_constraint="delegation_chain_broken",
                reason_code="delegation_chain_broken",
            )
            fragment = EvaluationFragment(
                stage="delegation",
                outcome="failed",
                decision_signal="deny",
                reason_code="delegation_chain_broken",
                hard_authority_failure=True,
                summary="Delegation chain contains a cycle.",
                details={"chain_status": "broken"},
            )
            return result, fragment
        seen.add(current_id)
        raw = delegations.get(current_id)
        if raw is None:
            result = DelegationResult(
                chain_status="broken",
                chain_path=_path_labels(chain, display, include_tool=True),
                effective_capabilities=[],
                effective_resources=[],
                effective_purposes=[],
                violated_constraint="delegation_chain_broken",
                reason_code="delegation_chain_broken",
            )
            fragment = EvaluationFragment(
                stage="delegation",
                outcome="failed",
                decision_signal="deny",
                reason_code="delegation_chain_broken",
                hard_authority_failure=True,
                summary="Delegation chain is broken.",
                details={"chain_status": "broken"},
            )
            return result, fragment
        envelope = parse_delegation(raw)
        chain.append(envelope)
        current_id = envelope.parent_delegation_id

    chain_root_first = list(reversed(chain))
    path = _path_labels(chain, display, include_tool=True)

    for node in chain_root_first:
        if node.status == "revoked":
            result = DelegationResult(
                chain_status="revoked",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                effective_purposes=[],
                violated_constraint="parent_delegation_revoked",
                chain_version=_chain_version(chain),
                reason_code="parent_delegation_revoked",
            )
            fragment = EvaluationFragment(
                stage="delegation",
                outcome="failed",
                decision_signal="deny",
                reason_code="parent_delegation_revoked",
                hard_authority_failure=True,
                summary="A parent delegation was revoked; downstream authority is invalid.",
                details={"chain_status": "revoked"},
            )
            return result, fragment
        if node.status == "expired":
            result = DelegationResult(
                chain_status="expired",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                effective_purposes=[],
                violated_constraint="parent_delegation_expired",
                chain_version=_chain_version(chain),
                reason_code="parent_delegation_expired",
            )
            fragment = EvaluationFragment(
                stage="delegation",
                outcome="failed",
                decision_signal="deny",
                reason_code="parent_delegation_expired",
                hard_authority_failure=True,
                summary="A parent delegation expired; downstream authority is invalid.",
                details={"chain_status": "expired"},
            )
            return result, fragment

    for parent, child in zip(chain_root_first, chain_root_first[1:]):
        violation = _parent_child_violation(parent, child)
        if violation:
            code, constraint = violation
            result = DelegationResult(
                chain_status="constraint_violation",
                chain_path=path,
                effective_capabilities=[],
                effective_resources=[],
                effective_purposes=[],
                violated_constraint=constraint,
                chain_version=_chain_version(chain),
                reason_code=code,
            )
            fragment = EvaluationFragment(
                stage="delegation",
                outcome="failed",
                decision_signal="deny",
                reason_code=code,
                hard_authority_failure=True,
                summary="Parent/child delegation constraints were violated.",
                details={"violated_constraint": constraint},
            )
            return result, fragment

    leaf = chain[0]
    if leaf.delegate_id != request.agent_id:
        result = DelegationResult(
            chain_status="broken",
            chain_path=path,
            effective_capabilities=[],
            effective_resources=[],
            effective_purposes=[],
            violated_constraint="delegation_chain_broken",
            chain_version=_chain_version(chain),
            reason_code="delegation_chain_broken",
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="failed",
            decision_signal="deny",
            reason_code="delegation_chain_broken",
            hard_authority_failure=True,
            summary="Delegation leaf does not bind to the requesting agent.",
            details={"chain_status": "broken"},
        )
        return result, fragment

    effective_caps = set(leaf.capabilities)
    effective_resources = set(leaf.resources)
    effective_purposes = set(leaf.permitted_purposes)
    effective_class = leaf.maximum_data_classification
    effective_limit = leaf.maximum_amount
    effective_expiry = leaf.valid_until
    redelegation = leaf.may_redelegate
    for node in chain_root_first:
        effective_caps &= set(node.capabilities)
        effective_resources &= set(node.resources)
        effective_purposes &= set(node.permitted_purposes)
        if _class_rank(node.maximum_data_classification) < _class_rank(effective_class):
            effective_class = node.maximum_data_classification
        effective_limit = min(effective_limit, node.maximum_amount)
        if node.valid_until < effective_expiry:
            effective_expiry = node.valid_until
        redelegation = redelegation and node.may_redelegate

    action_capability = request.requested_action
    if action_capability not in effective_caps:
        result = DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_purposes=sorted(effective_purposes),
            effective_data_classification=effective_class,
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_action_not_in_effective_capabilities",
            chain_version=_chain_version(chain),
            reason_code="capability_not_delegated",
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="failed",
            decision_signal="deny",
            reason_code="capability_not_delegated",
            hard_authority_failure=True,
            summary="Requested action is not within effective delegated capabilities.",
            details={"requested_action": action_capability, "effective_capabilities": sorted(effective_caps)},
        )
        return result, fragment

    if request.requested_resource not in effective_resources:
        result = DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_purposes=sorted(effective_purposes),
            effective_data_classification=effective_class,
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_resource_not_in_effective_resources",
            chain_version=_chain_version(chain),
            reason_code="capability_not_delegated",
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="failed",
            decision_signal="deny",
            reason_code="capability_not_delegated",
            hard_authority_failure=True,
            summary="Requested resource is not within effective delegated resources.",
            details={"requested_resource": request.requested_resource},
        )
        return result, fragment

    amount = as_decimal(request.requested_amount)
    if amount > effective_limit:
        result = DelegationResult(
            chain_status="constraint_violation",
            chain_path=path,
            effective_capabilities=sorted(effective_caps),
            effective_resources=sorted(effective_resources),
            effective_purposes=sorted(effective_purposes),
            effective_data_classification=effective_class,
            effective_limit=str(effective_limit),
            effective_expiry=effective_expiry,
            redelegation_allowed=redelegation,
            violated_constraint="requested_amount_exceeds_effective_limit",
            chain_version=_chain_version(chain),
            reason_code="capability_not_delegated",
        )
        fragment = EvaluationFragment(
            stage="delegation",
            outcome="failed",
            decision_signal="deny",
            reason_code="capability_not_delegated",
            hard_authority_failure=True,
            summary="Requested amount exceeds effective delegated limit.",
            details={"requested_amount": str(amount), "effective_limit": str(effective_limit)},
        )
        return result, fragment

    result = DelegationResult(
        chain_status="valid",
        chain_path=path,
        effective_capabilities=sorted(effective_caps),
        effective_resources=sorted(effective_resources),
        effective_purposes=sorted(effective_purposes),
        effective_data_classification=effective_class,
        effective_limit=str(effective_limit),
        effective_expiry=effective_expiry,
        redelegation_allowed=redelegation,
        chain_version=_chain_version(chain),
        reason_code=None,
    )
    fragment = EvaluationFragment(
        stage="delegation",
        outcome="satisfied",
        summary="Delegation chain is valid for Cedar Quill Markets authority.",
        details={"chain_status": "valid", "chain_path": path},
    )
    return result, fragment


def _class_rank(label: str) -> int:
    order = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
    return order.get(label.lower(), 99)


def _parent_child_violation(
    parent: DelegationEnvelope, child: DelegationEnvelope
) -> Optional[Tuple[str, str]]:
    if not set(child.capabilities).issubset(set(parent.capabilities)):
        return ("capability_not_delegated", "child_capability_exceeds_parent")
    if not set(child.resources).issubset(set(parent.resources)):
        return ("capability_not_delegated", "child_resource_exceeds_parent")
    if child.maximum_amount > parent.maximum_amount:
        return ("capability_not_delegated", "child_limit_exceeds_parent")
    if child.valid_until > parent.valid_until:
        return ("capability_not_delegated", "child_expiry_exceeds_parent")
    if not parent.may_redelegate:
        return ("capability_not_delegated", "redelegation_prohibited")
    if parent.remaining_depth <= 0:
        return ("capability_not_delegated", "delegation_depth_exceeded")
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
