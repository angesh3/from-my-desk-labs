# From My Desk Labs

Practical spikes and reference implementations accompanying the From My Desk newsletter.

This is a single reusable repository for technical editions. Each lab lives under `labs/` with a numbered prefix so later spikes can be added as `002`, `003`, and so on.

```
from-my-desk-labs/
├── README.md
└── labs/
    └── 001-know-your-agent/
```

## Labs

| Lab | Title | What it demonstrates |
| --- | --- | --- |
| [001-know-your-agent](labs/001-know-your-agent) | Know Your Agent | Register an agent, bind it to a policy bundle, and allow or deny a proposed action before anything is executed |

## Disclaimer

All companies, agents, accounts, tickers, trades, policies, and thresholds in this repository are **fictional**. They exist only to make the code readable. Nothing here is investment advice, a trading system, or a representation of any real firm.

## Adding a new lab

1. Create `labs/00N-short-name/` with `README.md`, plus whatever `app/`, `policies/`, `examples/`, `tests/`, and `diagrams/` the edition needs.
2. Link it from the table above.
3. Keep names, data, and narratives fictional.
