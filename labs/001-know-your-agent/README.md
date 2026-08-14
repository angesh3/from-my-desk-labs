# Lab 001 — Know Your Agent

**Identity tells us which agent is acting. Identity alone does not authorize the action.**

This lab is an educational policy-gate simulation for a fictional organization, **Cedar Quill Markets**. A fictional agent may propose a paper order. A trust gateway returns one of four decisions. **No order is executed. No money moves. This is not investment advice.**

Public demo routes (when the website is deployed):

- https://from-my-desk.com/
- https://from-my-desk.com/labs
- https://from-my-desk.com/labs/know-your-agent
- https://from-my-desk.com/health

The website also works locally without that domain. Lab-specific assets are served from `/static/labs/001/`. The From My Desk logo is a global brand asset, not a Lab 001 file.

## Four decisions

| Decision | Meaning |
| --- | --- |
| ALLOW | Hard authorization passed and the amount is within policy, including any required confirmation or MFA flags. |
| CONFIRM | Explicit customer confirmation is required. |
| STEP_UP | Stronger authentication (MFA) is required, typically with confirmation. |
| DENY | The request is outside authority or above the absolute maximum. |

Confirmation and MFA **never** override a failed hard-authorization rule.

## Policy rules (fictional)

Hard checks, in order. Any failure is DENY:

1. Agent exists
2. Agent status is active
3. Authority is not expired
4. Authority is not revoked
5. Request principal matches the delegating principal
6. Action is an allowed capability
7. Account is assigned
8. Ticker is allowed
9. Ticker is not restricted (`MAPLE` is restricted)

Then amount bands, using `Decimal` arithmetic:

| Notional | Result |
| --- | --- |
| ≤ 5,000 | ALLOW |
| 5,000.01 through 10,000 | CONFIRM, unless `customer_confirmed` |
| 10,000.01 through 15,000 | STEP_UP, unless confirmed **and** MFA |
| > 15,000 | DENY (`amount_exceeds_limit`) |

Exact boundaries: 5,000 ALLOW; 10,000 CONFIRM unless confirmed; 15,000 STEP_UP unless both flags; any amount greater than 15,000 DENY.

`side` (`buy`/`sell`) is validated and shown in the UI only. It does not change the decision in this spike.

Policy thresholds live in `policies/desk-policy.yaml` (`policy_id: cedar-quill-desk-v2`). They are not copied into multiple Python modules.

## Architecture

Reader → Interactive scenario builder → Evaluation API → Trust gateway → Policy decision → Explanation and audit.

The trust gateway combines:

- Identity registry
- Delegated authority
- Policy rules
- Request context (confirmation, MFA)

**Authentication** answers who the agent is. **Authorization** answers what it may do. **Policy evaluation** applies both plus amount. **Execution** would be a later system; this lab never calls a broker. **Audit** is a response `audit_id` plus check explanations. **Product telemetry** (optional PostHog) is a separate visitor-analytics concern and must not include audit or identity fields.

See `diagrams/know-your-agent.md`, `static/architecture.svg`, and `static/know-your-agent-trust-workflow.gif`.

## What this spike does not prove

- No production identity provider
- No real delegation protocol
- No durable, tamper-evident audit store
- No brokerage integration
- No production authorization standard
- No real financial transaction
- Not a claim that the example is production-ready

A production audit system would need durable storage, access control, and tamper evidence. This educational version returns `audit_id` in the HTTP response only and does not persist requests.

## Try these scenarios

| Preset | Expected |
| --- | --- |
| 100 × 40.00 = 4,000 | ALLOW |
| 200 × 40.00 = 8,000 unconfirmed | CONFIRM |
| 8,000 with confirmation | ALLOW |
| 300 × 40.00 = 12,000 | STEP_UP |
| 12,000 with confirmation and MFA | ALLOW |
| 450 × 40.00 = 18,000 | DENY |
| Unknown / revoked / expired / wrong principal / MAPLE / unassigned account | DENY |

Example JSON files are in `examples/`.

## Local setup

Run the **repository-root** website. Lab 001 is a module inside that process, not a second server.

Python **3.11 or 3.12**.

```bash
# from the repository root
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Do not set `PYTHONPATH`. The `know_your_agent` package is installed from the repository `pyproject.toml`.

Or: `bash labs/001-know-your-agent/scripts/run-demo.sh` after installing dependencies.

Open:

- http://127.0.0.1:8080/
- http://127.0.0.1:8080/labs
- http://127.0.0.1:8080/labs/know-your-agent
- http://127.0.0.1:8080/health

## Tests

From the repository root:

```bash
pytest -q
```

Policy-engine tests import `know_your_agent` and do not depend on website templates.

## API

Canonical evaluation endpoint: `POST /api/evaluate`. `POST /evaluate` is kept as an alias.

`GET /registry` returns a **sanitized** demo view (no principals, validity windows, or revocation flags). Set `REGISTRY_PUBLIC=disabled` to return 404.

`GET /health` returns `{status, version, service}`.

```bash
curl -sS -X POST http://127.0.0.1:8080/api/evaluate \
  -H 'Content-Type: application/json' \
  --data @examples/01-allow-4000.json
```

Stable reason codes include: `ok`, `confirmation_required`, `step_up_required`, `unknown_agent`, `inactive_agent`, `authority_expired`, `authority_revoked`, `principal_mismatch`, `capability_denied`, `account_not_assigned`, `ticker_not_allowed`, `ticker_restricted`, `amount_exceeds_limit`, `invalid_request`.

Malformed bodies return HTTP 422 with `reason_code: invalid_request` and no stack traces.

## Environment variables

See the repository-root `.env.example`. Copy to `.env` locally; `.env` is gitignored.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | 8080 | Listen port |
| `POLICY_DIR` | `policies` | YAML directory |
| `REGISTRY_PUBLIC` | `sanitized` | `sanitized` or `disabled` |
| `PUBLIC_GITHUB_URL` | this GitHub repo | Footer / home link |
| `PUBLIC_NEWSLETTER_URL` | [From My Desk on LinkedIn](https://www.linkedin.com/newsletters/from-my-desk-7492634647890341890/) | Override if the newsletter URL changes |
| `POSTHOG_ENABLED` | false | Product telemetry off unless true |
| `POSTHOG_PROJECT_TOKEN` | empty | Public ingestion token only |
| `POSTHOG_HOST` | `https://us.i.posthog.com` | Analytics host |
| `RATE_LIMIT_PER_MINUTE` | 60 | In-memory POST /evaluate limit |

Telemetry is **off** unless explicitly enabled, and it stays off on localhost and during pytest. It never sends request/response JSON, principal, agent, account, or audit IDs. Analytics failure must not block evaluation. There is no custom `/admin` app; use the authenticated PostHog dashboard if you enable analytics.

Recommended PostHog dashboard (private): unique visitors, lab opens, evaluations submitted, visitor-to-evaluation conversion, decision distribution, most-used scenarios, architecture views, GitHub clicks, newsletter clicks, referrer/UTM, country/device summaries from the platform, evaluation errors, coarse response-time buckets.

A custom admin UI would add authn, authz, sessions, storage, privacy obligations, and attack surface. It is intentionally out of this spike.

## Docker

Build from the **repository root**. The former lab-only image is replaced by the website image.

```bash
# from the repository root
docker compose up --build
```

Production image: non-root user, no `--reload`, lab policies mounted via `POLICY_DIR`, health check on `/health`. Bind `PORT` (Render sets this). Do not copy `.env` with secrets into the image.

See the root README for Render settings. This lab change does not deploy or modify DNS.

## Security notes

- Same-origin UI and API; no wildcard CORS.
- Security headers on responses.
- 16 KB body cap and basic per-IP rate limit on evaluate.
- Direct API calls use the same engine as the UI; client-side flags cannot bypass hard denials.
- Policy YAML is read-only in Docker. Missing or inconsistent YAML refuses startup.
- Do not log raw bodies (the app does not).
- ALLOW does not execute anything (`execution: not_performed`).

## Privacy

No real personal data should be entered. The demo does not persist submissions. Decision audit and product telemetry are separate.

## Disclaimer

Cedar Quill Markets, `kya-agent-001`, `principal-demo-001`, `paper-desk-alpha`, and tickers BRICK, WILLO, AURORA, and MAPLE are fictional. This lab is not a broker, not a production authorization system, and not financial advice.
