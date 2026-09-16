"""Canonicalization, hashing, and verification for action receipts."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Dict, Mapping, Optional

from .models import ActionReceipt, IntegrityStatus, VerificationResult

HASH_EXCLUDED_FIELDS = frozenset({"receipt_hash", "integrity_status"})


def _as_mapping(receipt: ActionReceipt | Mapping[str, Any]) -> Dict[str, Any]:
    if isinstance(receipt, ActionReceipt):
        return receipt.model_dump(mode="json")
    return dict(receipt)


def canonicalize_receipt(receipt: ActionReceipt | Mapping[str, Any]) -> str:
    """Return stable JSON for hashing (excludes receipt_hash and integrity_status)."""
    data = _as_mapping(receipt)
    payload = {key: data[key] for key in sorted(data) if key not in HASH_EXCLUDED_FIELDS}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def calculate_receipt_hash(receipt: ActionReceipt | Mapping[str, Any]) -> str:
    canonical = canonicalize_receipt(receipt)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_receipt(
    receipt: ActionReceipt | Mapping[str, Any],
    previous_receipt: Optional[ActionReceipt | Mapping[str, Any]] = None,
) -> VerificationResult:
    """Recalculate the hash and optionally check previous-receipt linkage."""
    data = _as_mapping(receipt)
    stored_hash = str(data.get("receipt_hash") or "")
    expected_hash = calculate_receipt_hash(data)
    content_match = bool(stored_hash) and hmac.compare_digest(stored_hash, expected_hash)

    failures: list[str] = []
    if not stored_hash:
        failures.append("Stored receipt_hash is missing.")
    elif not content_match:
        failures.append(
            "Recalculated SHA-256 does not match the stored receipt_hash. "
            "A material field changed after the receipt hash was computed."
        )

    previous_hash = str(data.get("previous_receipt_hash") or "")
    chain_match = True
    if previous_receipt is not None:
        prior = _as_mapping(previous_receipt)
        prior_hash = str(prior.get("receipt_hash") or "")
        if not previous_hash:
            chain_match = False
            failures.append("Current receipt does not declare a previous_receipt_hash.")
        elif not prior_hash:
            chain_match = False
            failures.append("Prior receipt is missing receipt_hash.")
        elif not hmac.compare_digest(previous_hash, prior_hash):
            chain_match = False
            failures.append(
                "previous_receipt_hash does not match the supplied prior receipt. "
                "The chain is broken."
            )
    elif previous_hash:
        # Declared linkage without a prior receipt to check: content may still verify.
        chain_match = True

    if not content_match:
        status = IntegrityStatus.tampered
        explanation = (
            "Verification failed: the receipt content no longer matches its receipt hash. "
            "Integrity is not the same as decision correctness—this only means the "
            "recorded fields changed relative to the trusted hash."
        )
    elif not chain_match:
        status = IntegrityStatus.chain_broken
        explanation = (
            "Receipt content matches its own hash, but the previous-receipt linkage "
            "does not verify against the supplied prior receipt."
        )
    else:
        status = IntegrityStatus.verified
        explanation = (
            "Receipt content matches its SHA-256 receipt hash"
            + (
                " and previous-receipt linkage verifies."
                if previous_receipt is not None and previous_hash
                else "."
            )
            + " A matching hash shows the content has not changed relative to a trusted "
            "reference; it does not by itself prove who created the receipt."
        )

    return VerificationResult(
        integrity_status=status,
        content_match=content_match,
        chain_match=chain_match,
        expected_hash=expected_hash,
        stored_hash=stored_hash,
        failures=failures,
        explanation=explanation,
    )
