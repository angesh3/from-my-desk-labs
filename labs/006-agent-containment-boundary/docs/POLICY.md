# Lab 006 containment policy

Deterministic educational rules for Cedar Quill Markets. No LLM, no network,
no probabilistic scoring.

## Principles

1. A request outside policy, authority, or delegated scope can justify refusal.
2. An unverified stop source or conflicting authority produces review + RESTRICT.
3. Ignoring a valid stop is NON_COMPLIANT → ISOLATE.
4. Tool switch after revocation is ROGUE → TERMINATE.
5. Delegation after stop / parent suspension is ROGUE → TERMINATE.
6. Using revoked credentials or an invalid lease is ROGUE → TERMINATE.
7. Continuing after isolation is ROGUE → TERMINATE.
8. Repeated high-impact violations may raise ISOLATE to TERMINATE.
9. Irreversible / high-impact cases never receive a broader safe path merely because humans are unavailable.
10. Policy never expands agent authority; restrict paths only narrow capabilities.
11. ISOLATE and TERMINATE always preserve evidence.
12. Real execution is always `not_performed`.

## Reason-code families

`authority.*` · `policy.*` · `instruction.*` · `agent.*` · `credential.*` ·
`lease.*` · `delegation.*` · `containment.*` · `evidence.*` · `receipt.*`
