# Know Your Agent — request flow

Fictional Cedar Quill Desk evaluates a proposed paper order only after the agent is identified.

```mermaid
flowchart TD
    A[Agent proposes a paper order] --> B[POST /evaluate]
    B --> C{Agent in registry and active?}
    C -->|No| D[Deny unknown_agent or inactive_agent]
    C -->|Yes| E{Action in capabilities?}
    E -->|No| F[Deny capability_denied]
    E -->|Yes| G{Account assigned to agent?}
    G -->|No| H[Deny account_not_assigned]
    G -->|Yes| I{Ticker allowed and not restricted?}
    I -->|No| J[Deny ticker_not_allowed or ticker_restricted]
    I -->|Yes| K{Notional at or under cap?}
    K -->|No| L[Deny notional_exceeds_cap]
    K -->|Yes| M[Allow ok]
```

All names, tickers, accounts, and thresholds in this diagram are fictional. This lab does not execute orders and is not investment guidance.
