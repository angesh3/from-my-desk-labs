# Know Your Agent — request flow

Fictional Cedar Quill Markets evaluates a proposed paper order in a trust gateway. The lab does not execute orders.

```mermaid
flowchart TD
    A[Reader / agent client] --> B[Scenario builder or POST /api/evaluate]
    B --> C[Trust gateway]
    C --> D{Hard authorization}
    D -->|Fail| E[DENY]
    D -->|Pass| F{Amount band}
    F -->|<= 5000| G[ALLOW]
    F -->|<= 10000| H[CONFIRM unless confirmed]
    F -->|<= 15000| I[STEP_UP unless confirmed and MFA]
    F -->|> 15000| J[DENY amount_exceeds_limit]
    G --> K[Explanation + audit_id]
    H --> K
    I --> K
    E --> K
    J --> K
    K --> L[Execution out of scope]
```

Authentication is identity. Authorization is delegated scope. Policy evaluation applies both plus amount context. Audit is returned in the response and is not product telemetry.
