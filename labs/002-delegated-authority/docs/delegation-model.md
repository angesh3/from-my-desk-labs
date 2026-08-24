# Delegation model — Lab 002

## Thesis in one line

**Trust Must Narrow at Every Handoff.** Child authority is never broader than parent authority.

## Delegation envelope

Each hop is a fictional envelope with:

| Field | Meaning |
| --- | --- |
| `delegation_id` | Unique id for this envelope |
| `parent_delegation_id` | Optional parent; null at the root hop |
| `principal_id` | Owning human principal |
| `delegator_id` | Who granted this hop |
| `delegate_id` | Who received this hop |
| `capabilities` | Allowed actions |
| `resources` | Allowed resources |
| `maximum_amount` | Decimal ceiling |
| `valid_from` / `valid_until` | Validity window |
| `may_redelegate` | Whether further hops are allowed |
| `remaining_depth` | How many redelegations remain |
| `required_assurance` | Assurance hint |
| `status` | `active` \| `expired` \| `revoked` |
| `version` | Envelope version stamp |

## Running example (fictional)

Human Principal holds Research + Propose + Approve on desk and market summaries.

Portfolio Agent receives Research + Propose (narrowed).

Research Agent receives Research only on market summaries with a lower amount and earlier expiry.

A tool request must sit inside the Research Agent’s effective authority. Requesting `execute` while only `research` was delegated yields DENY (`capability_not_delegated`).

## Parent–child invariants

At each hop the evaluator requires:

1. Child capabilities ⊆ parent capabilities
2. Child resources ⊆ parent resources
3. Child `maximum_amount` ≤ parent `maximum_amount`
4. Child `valid_until` ≤ parent `valid_until`
5. Child depth remains within parent remaining depth
6. Redelegation only if the parent permits it

Violations produce DENY with codes such as `child_capability_exceeds_parent`, `child_limit_exceeds_parent`, `child_expiry_exceeds_parent`, `redelegation_prohibited`, or `delegation_depth_exceeded`.

## Effective authority

Effective capabilities, resources, limit, and expiry are the **intersection / minimum** across the active chain from root to leaf. The requested action must be contained in that effective set. Amounts use Decimal arithmetic.

## Expiry

If any ancestor is expired at `request_time`, the chain is invalid (`parent_expired`). A child that claims a later expiry than its parent fails even if both appear active (`child_expiry_exceeds_parent`).

## Revocation propagation

If any ancestor is revoked, downstream authority is invalid (`parent_revoked`). Revocation is not automatically restored. Fallback may recommend human review and a **new** delegation id, never silent re-enablement of the revoked chain.

See `diagrams/revocation-flow.mmd`.

## Redelegation and depth

`may_redelegate: false` or `remaining_depth: 0` blocks further hops. Attempting to act as if a deeper hop exists yields `delegation_depth_exceeded` or related constraint failures. Recovery often points to a direct principal delegation.

## Chain integrity

Missing parents, inconsistent principal bindings, or incomplete paths yield `delegation_chain_broken`. Broken chains are DENY.

## What delegation is not

- Not a cryptographic proof in this spike
- Not a durable ledger of grants
- Not an execution grant — even a valid envelope only feeds policy evaluation
