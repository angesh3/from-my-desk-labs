# Limitations and evolution — Lab 002

## What this lab proves

Lab 002 is an educational spike. It shows how identity, narrowing delegation, profiling, posture, four-way decisions, audit evidence, and restricted fallback can fit together conceptually. It does not claim production readiness.

## Deferred work

The following are intentionally out of scope and candidates for later KYA labs or product design:

| Topic | Why deferred |
| --- | --- |
| Cryptographic delegation proof | Envelopes are YAML, not signed capability tokens |
| Verifiable action receipts | No executor; nothing to receipt |
| Dynamic Change of Authorization | No live CoA channel to agents or PEP |
| Agent segmentation | No network or runtime isolation enforcement |
| Continuous behavioral risk | Profiles/posture are fixtures, not streaming risk scores |
| Cross-organization delegation | Single fictional organization |
| Real runtime attestation | Boolean placeholders only |
| Agent quarantine | No enforcement plane |
| Profile poisoning defenses | No adversarial registration model |
| Posture spoofing defenses | No attestation verification chain |
| Model supply-chain verification | Version strings are demo labels |
| Confidence decay | Confidence is static per fixture |
| Executor integration | Hard boundary: `execution: not_performed` |

## Evolution principles (carry forward)

1. Child authority cannot exceed parent authority.
2. Profiling cannot create authority.
3. Posture cannot expand authority.
4. Hard failures cannot be repaired by CONFIRM or STEP_UP.
5. Fallback never overrides DENY.
6. Evaluation and execution stay separate.

## Relationship to Lab 001

Lab 001 introduced identity versus delegated authority for a single paper-order proposal. Lab 002 expands the story to multi-hop narrowing, APE/APSE, revocation propagation, and recovery paths. Future labs should preserve Lab 001 and Lab 002 as durable teaching artifacts.

## Planned future KYA topic

**KYA: From Network Access Control to Agent Access Control**

Network access control asks which device or user may join a segment. Agent access control asks which autonomous software actor may exercise which capability, on which resource, under whose delegated authority, with what posture, at what moment — and how refusal becomes evidence. Bridging NAC mental models to agent authorization is a natural next chapter in the Know Your Agent series: sessions and posture for humans and endpoints become identity, delegation chains, APE, and APSE for agents.

## Honest disclaimer

Cedar Quill Markets remains fictional. Diagrams and storyboards are teaching aids. Do not treat ALLOW as permission to move real funds or invoke real tools.
