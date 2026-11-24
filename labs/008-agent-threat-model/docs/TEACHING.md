# Lab 008 teaching notes

## Core thesis

The model is only one component. Threat modeling must follow the full agentic system and lifecycle—even when identity, authority, and original instructions were valid.

## Storyline

Labs 001–007 each answered one control question. Lab 008 connects them:

1. Who is acting?
2. What authority was handed over, and how should it narrow?
3. May the agent act under current policy and posture?
4. Even if authorized, should it continue alone?
5. Can we reconstruct and verify what it did?
6. What happens when it refuses, ignores a stop, or evades?
7. What evidence shows containment worked?
8. What could go wrong across the whole system before, during, and after execution?

## Surfaces and dimensions

Keep the seven primary surfaces stable. Use cross-cutting dimensions to annotate drift, public-model exposure, and infrastructure impact.

## Distinctions to teach

- Behavioral drift ≠ model-weight drift
- Memory/context updates ≠ retraining
- Approved external models ≠ uncontrolled public-model exposure
- Availability/cost impact ≠ security compromise
- Attempted control ≠ independently verified control

## Evidence

Agent self-report may be preserved but never counts as independent verification. Incomplete telemetry yields `UNVERIFIED` / `UNKNOWN`.

## Safety

Educational prototype only. Every evaluation returns `execution: not_performed`.
