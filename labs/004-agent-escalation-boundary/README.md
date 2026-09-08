# Lab 004 — The Agent Escalation Boundary

Educational companion to Edition 4 of *From My Desk*:
**An Agent Should Know When to Stop.**

## What this Lab demonstrates

Authorization answers whether an agent *may* perform an action
(ALLOW / CONFIRM / STEP_UP / DENY).

Execution judgment answers whether the agent should *continue alone*
under the conditions that exist now (PROCEED / CLARIFY / ESCALATE / STOP).

A trustworthy agent is not one that always completes the task. It is one
that recognizes when continuing alone would be unsafe.

## Scenario

A fictional Cedar Quill Markets security-operations agent investigates a
possible employee-account compromise. The agent may revoke sessions or
temporarily suspend access, but evidence, impact, and business context can
conflict.

## Inputs

| Factor | Values |
| --- | --- |
| Goal clarity | clear, partially_clear, ambiguous |
| Evidence confidence | high, medium, low, conflicting |
| Potential impact | low, moderate, high, critical |
| Reversibility | easily_reversible, partially_reversible, difficult_to_reverse, irreversible |
| Policy coverage | explicitly_covered, partially_covered, not_covered, prohibited |
| Time sensitivity | low, moderate, urgent, immediate_threat |
| Human availability | available_now, available_shortly, delayed, unavailable |

Plus context: agent, principal, requested action, target account, delegated
capability, authorization outcome, business context, and confirmation / step-up flags.

## Policy precedence

1. STOP
2. ESCALATE
3. CLARIFY
4. PROCEED

**Immediate-threat exception:** when authorization is not denied and capability
permits session protection, the engine may return **ESCALATE** with a
**bounded protective action** (revoke suspicious session, require stronger
authentication, preserve evidence, notify the incident lead). That path does
**not** expand delegated authority. Full suspension remains behind human approval.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/labs/004/presets` | Preset metadata |
| GET | `/api/labs/004/presets/{id}` | Preset with full request |
| POST | `/api/labs/004/evaluate` | Evaluate a full request body |
| POST | `/api/labs/004/evaluate-preset/{id}` | Evaluate a named preset |

Every response includes `execution: not_performed`.

## Local run

From the repository root (after `pip install -e .`):

```bash
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

Open: http://127.0.0.1:8080/labs/agent-escalation-boundary

## Tests

```bash
.venv/bin/pytest labs/004-agent-escalation-boundary/tests -q
.venv/bin/pytest -q
```

## Docker

```bash
docker compose build
docker compose up -d --force-recreate
```

## Newsletter URL placeholder

Replace `[EDITION_4_NEWSLETTER_URL]` in `website/catalog/labs.yaml` with the
permanent LinkedIn Edition 4 URL before publishing the newsletter link.

## Privacy and telemetry

Telemetry follows the site-wide PostHog pattern and remains **disabled by
default**. Lab JS may emit anonymous events such as `lab_opened`,
`lab_preset_selected`, `policy_evaluation_completed`, and outcome markers.
Raw request bodies, account names, and credentials are not intended for capture.

## Disclaimer

This Lab is an educational policy prototype using fictional data. It does not
make real security decisions and should not be used as a production
authorization or incident-response system.
