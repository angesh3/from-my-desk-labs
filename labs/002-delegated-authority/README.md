# Lab 002 — Delegated Authority

**Trust Must Narrow at Every Handoff**

This lab is an educational policy-evaluation spike in the Know Your Agent series. A fictional organization, **Cedar Quill Markets**, shows how authority moves and narrows across:

**Human Principal → Portfolio Agent → Research Agent → Tool**

Identity can be valid while authority is missing, expired, revoked, or too broad for a child. Profiling and posture can inform trust; they cannot invent permission. **No tool action runs. No order executes. No money moves.**

Package name: `delegated_authority`.

Public demo routes (when the website is deployed):

- https://from-my-desk.com/
- https://from-my-desk.com/labs
- https://from-my-desk.com/labs/delegated-authority
- https://from-my-desk.com/health

Lab-specific assets are served from `/static/labs/002/`. The From My Desk logo is a global brand asset, not a Lab 002 file.

| Asset | URL |
| --- | --- |
| End-to-end workflow SVG | `/static/labs/002/delegated-authority-workflow.svg` |
| System architecture SVG | `/static/labs/002/system-architecture.svg` |
| Evaluation flow SVG | `/static/labs/002/evaluation-flow.svg` |
| Fallback flow SVG | `/static/labs/002/fallback-flow.svg` |
| Revocation flow SVG | `/static/labs/002/revocation-flow.svg` |
| Lab UI script | `/static/labs/002/lab.js` |
| Animated workflow GIF (optional) | `/static/labs/002/delegated-authority-trust-workflow.gif` |

Until the Animer GIF is copied into `static/`, the page shows the end-to-end workflow SVG as a poster fallback and never renders a broken GIF image. See `docs/ASSETS.md` and `docs/demo-guide.md`.

## Thesis

Child authority must be a subset of parent authority. At every handoff, capabilities, resources, limits, and time windows may stay the same or shrink — never grow. APE (Agent Profiling Engine) and APSE (Agent Posture and Security Engine) constrain how existing authority may be used. They do not manufacture new authority.

## Four decisions

| Decision | Meaning |
| --- | --- |
| ALLOW | Identity, delegation, profile, posture, scope, limits, and context are satisfied. Policy permits the request. Nothing is executed. |
| CONFIRM | Authority is valid, but business confirmation is required (amount threshold or unusual context). |
| STEP_UP | Stronger assurance or fresher evidence is required (stale posture, version noncompliance, profile mismatch). |
| DENY | The request is outside effective authority or fails a hard control. Evidence is recorded. |

Precedence: **DENY > STEP_UP > CONFIRM > ALLOW**. Confirmation and step-up never override hard authorization failures.

## Quick start

Run the **repository-root** website. Lab 002 is a module inside that process, not a second server.

Python **3.11 or 3.12**.

```bash
# from the repository root
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Do not set `PYTHONPATH`. The `delegated_authority` package is installed from the repository `pyproject.toml`.

Open:

- http://127.0.0.1:8080/
- http://127.0.0.1:8080/labs
- http://127.0.0.1:8080/labs/delegated-authority
- http://127.0.0.1:8080/health

## Routes

| Route | Purpose |
| --- | --- |
| `/labs/delegated-authority` | Lab page and interactive scenario journey |
| `GET /api/labs/002/scenarios` | Scenario catalog (id, title, short description, category, expected decision) |
| `POST /api/labs/002/evaluate` | Evaluate a scenario by `scenario_id` |

Example evaluation:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/labs/002/evaluate \
  -H 'Content-Type: application/json' \
  --data '{"scenario_id":"valid_narrow_delegation"}'
```

Unknown `scenario_id` returns a safe 4xx with `reason_code: invalid_request` and `execution: not_performed`. Malformed bodies return HTTP 422 without stack traces.

## Scenario catalog (15)

| ID | Title | Expected | Reason code (typical) |
| --- | --- | --- | --- |
| `valid_narrow_delegation` | Valid narrow delegation | ALLOW | `policy_satisfied` |
| `confirmation_required` | Human confirmation required | CONFIRM | `confirmation_threshold` |
| `stale_posture` | Stale posture evidence | STEP_UP | `posture_evidence_stale` |
| `unusual_context` | Unusual but permitted context | CONFIRM | `unusual_context` |
| `execution_not_delegated` | Execution not delegated | DENY | `capability_not_delegated` |
| `child_capability_exceeds_parent` | Child capability exceeds parent | DENY | `child_capability_exceeds_parent` |
| `child_limit_exceeds_parent` | Child limit exceeds parent | DENY | `child_limit_exceeds_parent` |
| `child_expiry_exceeds_parent` | Child expiry exceeds parent | DENY | `child_expiry_exceeds_parent` |
| `delegation_depth_exceeded` | Delegation depth exceeded | DENY | `delegation_depth_exceeded` |
| `parent_expired` | Parent expired | DENY | `parent_expired` |
| `parent_revoked` | Parent revoked | DENY | `parent_revoked` |
| `unknown_agent` | Unknown agent | DENY | `agent_unknown` |
| `profile_mismatch` | Profile mismatch | STEP_UP | `profile_mismatch` |
| `noncompliant_model_version` | Noncompliant model version | STEP_UP | `model_version_noncompliant` |
| `tool_inventory_changed` | Tool inventory changed | DENY | `tool_inventory_changed` |

Scenario definitions live in `examples/scenarios.yaml`. Policies live in `policies/`.

## Architecture summary

Reader → Lab page → `GET` scenarios / `POST` evaluate → Trust Gateway → four-way decision → explanation, audit ID, optional restricted fallback.

Inside the Trust Gateway:

1. **Identity** — who is acting, principal binding, lifecycle
2. **Delegation** — parent–child envelopes, effective authority
3. **APE** — declared / observed / verified profile
4. **APSE** — posture, evidence freshness, tool inventory
5. **Policy** — scope, limits, context, decision precedence
6. **Audit** — evidence record (response-scoped in this spike)
7. **Fallback** — recovery path that never overrides DENY

**Execution** sits outside this lab. Every response reports `execution: not_performed`.

See `docs/architecture.md`, `diagrams/`, and `docs/ASSETS.md`.

## Core invariants

1. Child authority cannot exceed parent authority.
2. Profiling cannot create authority.
3. Posture cannot expand authority.
4. Hard failures cannot be repaired by CONFIRM or STEP_UP.
5. Parent expiry or revocation invalidates downstream delegations.
6. DENY produces an evidence record.
7. Fallback does not override the original decision.
8. Remediation requires a new evaluation.
9. ALLOW is short-lived and bound to the evaluated request.
10. Policy evaluation and execution remain separate.

## Privacy

No real personal data should be entered. Demo agents, principals, and amounts are fictional. The spike does not persist submissions in a durable store. Decision audit and optional product telemetry are separate concerns. Telemetry, when enabled at the website layer, must not include principal, agent, delegation, amounts, audit IDs, or raw request/response bodies. This lab documentation does not embed analytics tokens.

## Limitations

This spike does not prove production identity, cryptographic delegation, durable tamper-evident audit, real attestation, or tool execution. See `docs/limitations-and-evolution.md` for deferred work and the planned topic **KYA: From Network Access Control to Agent Access Control**.

## Tests

From the repository root:

```bash
pytest -q
```

Lab 002 package tests import `delegated_authority` and do not depend on website templates. Website integration tests cover `/labs/delegated-authority` and `/api/labs/002/*` when present.

## Documentation map

| Doc | Topic |
| --- | --- |
| `docs/architecture.md` | End-to-end components and boundaries |
| `docs/demo-guide.md` | One-minute and 3–5 minute demo script |
| `docs/ASSETS.md` | SVG/GIF paths and how to install the Animer GIF |
| `docs/animation-storyboard.md` | Animer.ai storyboard |
| `diagrams/delegated-authority-workflow.mmd` / `.svg` | End-to-end handoff → gateway → decision |
| `diagrams/system-architecture.mmd` / `.svg` | Internal Trust Gateway design |
| `diagrams/evaluation-flow.mmd` / `.svg` | Ordered evaluation and precedence |
| `diagrams/fallback-flow.mmd` / `.svg` | Restricted fallback |
| `diagrams/revocation-flow.mmd` / `.svg` | Downstream revocation |
| `docs/component-contracts.md` | Inputs and outputs per component |
| `docs/evaluation-sequence.md` | Ordered evaluation and precedence |
| `docs/delegation-model.md` | Envelopes, depth, revocation |
| `docs/profile-model.md` | APE attributes and limits |
| `docs/posture-model.md` | APSE signals and limits |
| `docs/decision-semantics.md` | ALLOW / CONFIRM / STEP_UP / DENY |
| `docs/fallback-model.md` | Restricted recovery paths |
| `docs/audit-evidence.md` | Why DENY is evidence |
| `docs/security-and-privacy.md` | Fictional data and telemetry bounds |
| `docs/limitations-and-evolution.md` | Deferred work and future KYA topic |
| `docs/animation-storyboard.md` | Animer.ai-ready frames |

## Disclaimer

Cedar Quill Markets, `principal-demo-001`, `research-agent-001`, `portfolio-agent-001`, paper desk identifiers, and example amounts are fictional. This lab is not a broker, not a production authorization system, and not financial advice.
