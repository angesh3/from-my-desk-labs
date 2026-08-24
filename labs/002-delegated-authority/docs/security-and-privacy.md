# Security and privacy — Lab 002

## Fictional data only

Cedar Quill Markets, demo principals, agents, desks, resources, and amounts are fictional. Do not enter real customer identities, real account numbers, real credentials, or real market orders into the lab.

## What this spike does not handle

- No real identity provider or SSO
- No real accounts or brokerage positions
- No credentials, API keys, or secrets in lab YAML
- No real runtime attestation or hardware roots of trust
- No execution of tools, orders, or money movement
- No durable PII store

## Application security posture (website-hosted)

Lab 002 rides the existing From My Desk website controls:

- Same-origin UI and API patterns; no wildcard CORS introduced by this lab
- Input validation via Pydantic models and an explicit scenario allowlist
- Safe error bodies without stack traces
- No `eval`, no dynamic imports from user input, no HTML injection of raw policy output
- Evaluation payloads are not logged as raw bodies by the lab package

## Analytics allowlist (website layer)

If product telemetry is enabled at the portal, only allowlisted events and coarse properties may be sent. Lab 002 documentation does **not** embed PostHog project tokens or personal API keys.

Expected event names (when the portal enables them):

- `lab_opened`
- `lab_preset_selected`
- `policy_evaluation_completed`
- `fallback_previewed`
- `architecture_viewed`
- `outbound_link_clicked`

### Restricted telemetry fields (never send)

- `principal_id`, `agent_id`, `delegation_id`
- Account, ticker, or exact amount
- Raw request or response JSON
- `audit_id`
- Model/runtime evidence, credential material, attestation material
- Arbitrary free-text user input

Analytics failures must remain non-blocking. Telemetry stays off on localhost / tests per portal rules. No `identify`, no session recording, no broad autocapture as part of this lab’s design intent.

## Threat and limitation notes

| Concern | Lab stance |
| --- | --- |
| Client-side UI spoofing | Direct API uses the same engine; scenarios are allowlisted |
| Authority inflation via profile | Explicitly denied by policy invariants |
| Posture as capability grant | Explicitly denied |
| Fallback as silent allow | Prohibited by fallback model |
| Secret leakage in docs/examples | Fictional ids only; no tokens in this tree |
| Supply-chain / attestation forgery | Deferred; placeholders only |

## Operator guidance

- Do not commit `.env` files with secrets into the lab directory
- Do not paste real PostHog tokens into Markdown
- Prefer repository-root configuration for any analytics enablement
