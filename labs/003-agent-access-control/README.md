# Lab 003 — Agent Access Control

Educational simulation for live agent access control at Cedar Quill Markets.

## What it demonstrates

- **Agent Management Plane** — registration, inventory, and profile state
- **Live authority evaluation** — canonical per-request events from actor through decision
- **Resource and purpose boundaries** — data classification and stated purpose checks
- **Posture and context** — APSE evidence freshness and material context change
- **Restricted recovery** — separate onboarding path without executing protected actions

Policy evaluation never executes a tool action. Every result reports `execution: not_performed`.

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/labs/003/scenarios` | List 14 fictional scenario presets |
| POST | `/api/labs/003/evaluate` | Evaluate `{ "scenario_id": "..." }` |

## Interactive page

```
/labs/agent-access-control
```

Static assets are served from `/static/labs/003/` (see `static/` and `docs/ASSETS.md`).

## Run tests

```bash
pytest labs/003-agent-access-control/tests website/tests/test_site.py website/tests/test_runtime_resources.py -q
```
