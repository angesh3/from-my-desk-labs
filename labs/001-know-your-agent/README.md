# Lab 001 — Know Your Agent

An AI agent should not get to act just because it can call a tool. This lab is a small policy gate: identify the agent, load the desk policy it is bound to, and **allow or deny** a proposed paper order before anything is sent onward.

The demo uses a fictional paper desk, fictional tickers, and fictional accounts. It is a control-plane spike, not a trading product.

## What you get

```
001-know-your-agent/
├── README.md
├── app/                 Policy engine and HTTP API
├── policies/            Agent registry + desk policy bundle
├── examples/            Sample allow and deny requests
├── tests/               Unit tests for the gate
├── diagrams/            Request flow
└── docker-compose.yml
```

The gate checks, in order:

1. The agent exists in the registry and is `active`
2. The requested action is in the agent's declared capabilities
3. The account is assigned to that agent
4. The ticker is on the desk allow-list and not restricted
5. Quantity is positive and notional (`quantity * limit_price`) is at or under the desk cap

Denied requests return a reason code. Nothing in this lab places an order.

## Run locally

Python 3.11 or 3.12 recommended.

```bash
cd labs/001-know-your-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
PYTHONPATH=app uvicorn main:app --reload --port 8080
```

Evaluate an allowed example:

```bash
curl -sS -X POST http://127.0.0.1:8080/evaluate \
  -H 'Content-Type: application/json' \
  --data @examples/allowed-order.json
```

## Run with Docker

```bash
cd labs/001-know-your-agent
docker compose up --build
```

## Tests

```bash
cd labs/001-know-your-agent
PYTHONPATH=app pytest tests -q
```

## Fictional world

| Name | Role |
| --- | --- |
| Cedar Quill Desk | Paper workshop that reviews agent-proposed orders |
| `kya-agent-001` | Registered research agent owned by the desk |
| `paper-desk-alpha` | Paper account the agent may use |
| `BRICK`, `WILLO`, `AURORA`, `MAPLE` | Fictional tickers |

## Disclaimer

This is a teaching spike. It is not investment guidance, not a broker, and not a model of any real company.
