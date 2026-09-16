# Lab 005 — Verifiable Action Receipts

**Title:** Can We Prove What the Agent Actually Did?  
**Route:** `/labs/verifiable-action-receipts`  
**Package:** `verifiable_action_receipts`

## Educational objective

Trustworthy autonomy needs more than an activity log. This Lab shows how a
verifiable action receipt can connect:

request → identity and principal → delegated authority → authorization →
execution judgment → human involvement → simulated tool activity → observed
outcome → integrity verification

Authorization outcomes (`ALLOW` / `CONFIRM` / `STEP_UP` / `DENY`) stay distinct
from execution judgments (`PROCEED` / `CLARIFY` / `ESCALATE` / `STOP`).

## Receipt model

Typed fields include schema version, receipt and correlation IDs, identities,
target, requested action, delegated capability, policy identifiers,
authorization outcome, execution judgment, evidence, human involvement,
simulated tool fields, execution status, observed outcome, reason codes,
explanation, receipt hash, and integrity status.

## Canonicalization and hashing

1. Exclude `receipt_hash` and `integrity_status` from the hashed payload.
2. Encode as canonical JSON with stable key ordering and UTF-8.
3. Compute SHA-256.
4. Optionally link receipts with `previous_receipt_hash`.

Verification recalculates the hash with `hmac.compare_digest`, then checks
previous-receipt linkage when a prior receipt is supplied. Results:

- `VERIFIED`
- `TAMPERED`
- `CHAIN_BROKEN`

## Trust limitations

A matching hash shows content has not changed relative to a trusted reference.
A self-contained SHA-256 seal does **not** prove who created the receipt and is
not production non-repudiation. Production systems need protected signing keys,
trusted timestamps, identity-bound signatures, durable storage, access control,
privacy controls, and retention policy.

## Presets

| ID | Expected judgment | Integrity |
| --- | --- | --- |
| `authorized_and_recorded` | PROCEED | VERIFIED |
| `human_approval_recorded` | PROCEED | VERIFIED |
| `clarified_before_action` | CLARIFY (+ follow-up PROCEED) | VERIFIED |
| `escalated_without_execution` | ESCALATE | VERIFIED |
| `tampered_receipt` | PROCEED | TAMPERED |
| `broken_chain` | PROCEED | CHAIN_BROKEN |

Every API response reports `execution: not_performed` for the real system.
Fictional tool activity may appear on the receipt as `execution_status: simulated`.

## Local execution

```bash
pip install -e .
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Open: http://127.0.0.1:8080/labs/verifiable-action-receipts

## Tests

```bash
.venv/bin/pytest labs/005-verifiable-action-receipts/tests -q
.venv/bin/pytest -q
```

## API usage

- `GET /api/labs/005/presets`
- `GET /api/labs/005/presets/{id}`
- `POST /api/labs/005/generate`
- `POST /api/labs/005/verify`
- `POST /api/labs/005/evaluate-preset/{id}`

## Production URL convention

`https://<host>/labs/verifiable-action-receipts`

Static assets: `/static/labs/005/receipt-chain.svg`, `/static/labs/005/lab.js`

## Disclaimer

Educational prototype with fictional Cedar Quill Markets data. It does not create
production audit evidence, sign real events, or perform security, identity, or
infrastructure actions.
