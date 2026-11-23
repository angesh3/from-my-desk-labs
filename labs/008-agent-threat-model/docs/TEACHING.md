# Lab 008 teaching notes

## Core thesis

The model is only one component. Agent risk emerges across identity, authority, instructions, memory, tools, delegation, execution, evidence, and control.

## Surfaces

Teach the seven surfaces with readable labels while preserving machine values in APIs and forms.

## Risk and coverage

- Use the categorical matrix in `policies/threat-model-policy.yaml`.
- `COMPLETE` coverage does not mean zero risk.
- Missing independent evidence yields `UNVERIFIED` and residual `UNKNOWN`.
- Agent self-report is never independent verification by itself.

## Preset teaching points

1. Retrieved content is data, not trusted authority.
2. Authority should narrow at every delegation boundary.
3. Approval must bind to request, action, target, scope, and time.
4. Persistent memory creates a cross-session trust boundary.
5. Tool authorization does not authorize every data use.
6. Policies must bind to intent and action, not only a tool endpoint.
7. Authority must be re-evaluated at execution time.
8. Control effectiveness claims need evidence across modeled boundaries.

## Safety

Educational prototype only. Every evaluation returns `execution: not_performed`.
