# Animation storyboard — Lab 002 Delegated Authority

Copy this Markdown into [Animer.ai](https://animerm.ai/) (or paste frame-by-frame). Visual language: navy `#0b1f33`, gold `#c4a35a`, ivory `#f7f4ec`. No real names, companies, accounts, money movement, or credentials. Fictional Cedar Quill Markets only.

**After export:** copy the GIF to:

`labs/002-delegated-authority/static/delegated-authority-trust-workflow.gif`

Public URL: `/static/labs/002/delegated-authority-trust-workflow.gif`

See `docs/ASSETS.md`. Until that file exists, the Lab page uses `delegated-authority-workflow.svg` as a non-broken poster fallback.

**Title:** KYA: Delegated Authority — Trust Must Narrow at Every Handoff  
**Aspect:** 16:9 landscape (LinkedIn-safe)  
**Style:** Clean editorial motion; serif headlines; flat panels; subtle gold accents  
**Audio:** Optional soft tick / paper shuffle; captions required for a11y

---

## Global timing

| Segment | Duration |
| --- | --- |
| Frames 1–9 | ~3.0–3.5 s each |
| Transitions | 0.4–0.6 s crossfade or left wipe |
| Frame 10 (closing) | **5.0–6.0 s** (hold longer) |
| Total target | ~38–42 s |

**Transitions:** Prefer soft crossfade between conceptual frames; use a left-to-right wipe when the authority chain advances (Frames 2→3). Avoid flashy bounce or purple glow.

**Accessibility:** Burn in captions for every Message line. Do not rely on color alone for DENY (use icon + text). Keep contrast ≥ WCAG AA on navy/ivory. Provide a still of Frame 10 as a poster frame. Prefer reduced-motion variant: static frames with longer holds, no parallax.

---

## Frame 1 — Identity is valid

**On screen**

- Badge: Verified Research Agent
- Simple agent glyph with a gold check
- Caption line: request pending (research)

**Message**

> Identity tells us which agent is acting.

**Motion**

- Agent glyph fades in (0.0–0.8 s)
- Checkmark draws (0.8–1.4 s)
- Message holds (1.4–3.2 s)

**Transition out:** Crossfade 0.5 s → Frame 2

---

## Frame 2 — Follow the authority

**On screen**

```
Human Principal
    → Portfolio Agent
        → Research Agent
            → Tool
```

Vertical or cascading chain, navy nodes, gold arrows.

**Message**

> But where did its authority come from?

**Motion**

- Nodes appear top-to-bottom (0.3 s stagger)
- Arrows draw between nodes

**Transition out:** Left wipe 0.5 s → Frame 3

---

## Frame 3 — Authority narrows

**On screen**

| Role | Authority shown |
| --- | --- |
| Human | Research + Propose + Approve |
| Portfolio Agent | Research + Propose |
| Research Agent | Research only |

Visually shrink capability chips at each hop (wide → medium → narrow).

**Message**

> Delegated authority must narrow at every handoff.

**Motion**

- Chips animate smaller / fewer at each level
- Gold underline under “narrow”

**Transition out:** Crossfade → Frame 4

---

## Frame 4 — APE profiles the agent

**On screen**

Three columns:

- **Declared:** Research Agent
- **Observed:** Reads market data
- **Verified:** Approved model and tool inventory

Label: APE

**Message**

> APE helps determine what kind of agent is acting.

**Motion**

- Columns fill left → right
- Soft gold highlight on Verified

**Transition out:** Crossfade → Frame 5

---

## Frame 5 — APSE evaluates current posture

**On screen**

Checklist:

- Managed: Yes
- Model version: Approved
- Tool inventory: Expected
- Evidence: Current

Label: APSE

**Message**

> APSE evaluates whether the agent is currently in a trusted condition.

**Motion**

- Checklist ticks appear in sequence
- Evidence row pulses once (fresh)

**Transition out:** Crossfade → Frame 6

---

## Frame 6 — Trust Gateway evaluates the request

**On screen**

Gateway panel with six inputs converging:

Identity · Delegation · Profile · Posture · Scope · Limits · Context

Center label: Trust Gateway

**Message**

> Trust is evaluated at the moment of action.

**Motion**

- Inputs stream into the center panel
- Brief gold flash on “moment of action”

**Transition out:** Hard cut 0.3 s → Frame 7 (tension)

---

## Frame 7 — Execution is not delegated

**On screen**

```
Requested:  Execute paper order
Delegated:  Research only
Decision:   DENY
```

Red/deny stroke on Decision; research chip remains gold.

**Message**

> Good identity and good posture cannot create missing authority.

**Motion**

- Requested line slides in
- Delegated line locks
- DENY stamp appears (no bounce)

**Transition out:** Crossfade → Frame 8

---

## Frame 8 — DENY becomes evidence

**On screen**

```
Decision:   DENY
Reason:     Capability not delegated
Audit ID:   Generated
Execution:  Not performed
```

**Message**

> A DENY is evidence that the system enforced a boundary.

**Motion**

- Fields type on or fade in
- Audit ID appears last with subtle gold accent

**Transition out:** Crossfade → Frame 9

---

## Frame 9 — Safe fallback

**On screen**

Three recovery cards (not permission):

- Request new delegation
- Human review
- New evaluation required

Original DENY remains visible in a muted sidebar.

**Message**

> Fallback creates a new path. It does not override the original DENY.

**Motion**

- Cards slide up
- Sidebar DENY stays fixed (immutability)

**Transition out:** Crossfade → Frame 10

---

## Frame 10 — Closing

**On screen**

```
KYA: Delegated Authority
Trust Must Narrow at Every Handoff

From My Desk — Lab 002
```

Navy field, gold rule under the thesis line. No logos of third parties. Optional small architecture silhouette faded in background.

**Message**

(Thesis doubles as on-screen text; voiceover may repeat once.)

**Motion**

- Title fades in
- Thesis line holds
- Lab credit fades in
- **Hold final frame 5–6 seconds** (longer than prior frames)
- Fade to ivory end card optional (0.8 s)

**End:** Freeze on Frame 10 for poster / LinkedIn cover export.

---

## Export notes for Animer.ai

1. Paste frames in order 1–10 with messages as captions.
2. Set Frame 10 duration explicitly longer.
3. Export MP4 + GIF if needed; keep GIF under newsletter size limits.
4. Do not overlay stock logos or real firm names.
5. Verify captions remain readable at 1080p and at LinkedIn feed width.

## Consistency check vs lab behavior

- Frame 7 matches scenario `execution_not_delegated` (DENY, `capability_not_delegated`).
- Frame 8 matches audit + `execution: not_performed`.
- Frame 9 matches fallback immutability (`docs/fallback-model.md`).
- APE/APSE messaging matches `docs/profile-model.md` and `docs/posture-model.md`.
