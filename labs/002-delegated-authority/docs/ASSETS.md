# Lab 002 visual assets

## Five unique teaching diagrams

These are different layers of the design. Do not substitute one for another.

| Diagram | Teaches | Repo path | Public URL |
| --- | --- | --- | --- |
| End-to-end workflow | Human → Agent → Sub-agent → Tool → Trust Gateway → Decision → Audit/Fallback | `static/delegated-authority-workflow.svg` (source: `diagrams/delegated-authority-workflow.svg`) | `/static/labs/002/delegated-authority-workflow.svg` |
| System architecture | Internal Trust Gateway inputs, decisions, audit, separate executor | `static/system-architecture.svg` | `/static/labs/002/system-architecture.svg` |
| Evaluation flow | Ordered policy evaluation and decision precedence | `static/evaluation-flow.svg` | `/static/labs/002/evaluation-flow.svg` |
| Fallback flow | Restricted fallback and new evaluation | `static/fallback-flow.svg` | `/static/labs/002/fallback-flow.svg` |
| Revocation flow | Downstream revocation / expiry propagation | `static/revocation-flow.svg` | `/static/labs/002/revocation-flow.svg` |

Editable Mermaid sources live next to the SVGs under `diagrams/*.mmd` (including `delegated-authority-workflow.mmd` and `lab-runtime.mmd` for the hosting path).

### Naming note — workflow export

The Animer / Mermaid export originally named:

```
Solution without Cloud storage-2026-08-23-213307.svg
```

must be stored in the repo as:

```
labs/002-delegated-authority/diagrams/delegated-authority-workflow.svg
```

and copied to `static/delegated-authority-workflow.svg` for serving. That rename is already applied in this tree.

### Duplicate removed — `architecture.svg`

`static/architecture.svg` and `diagrams/architecture.svg` were byte-identical to `system-architecture.svg` (MD5 `99e92baecbb68a5a6321b1b774018c81`). They were removed so the Lab does not present the same diagram under two names. Use `system-architecture.svg` for the internal Trust Gateway view.

## Other runtime static files

| File | Public URL |
| --- | --- |
| `static/lab.js` | `/static/labs/002/lab.js` |

## Animated workflow GIF (Lab 001 pattern)

Expected file (not yet generated):

```
labs/002-delegated-authority/static/delegated-authority-trust-workflow.gif
```

Expected public URL:

```
/static/labs/002/delegated-authority-trust-workflow.gif
```

### How to add the Animer GIF

1. Generate the animation from `docs/animation-storyboard.md` in Animer.ai.
2. Export a GIF at approximately 800x600.
3. Copy it to `labs/002-delegated-authority/static/delegated-authority-trust-workflow.gif`.
4. Rebuild the Docker image so `Dockerfile` copies `labs/002-delegated-authority/static`.
5. Confirm `GET /static/labs/002/delegated-authority-trust-workflow.gif` returns 200 with `image/gif`.

Until the GIF exists, the Lab page shows the local **end-to-end workflow SVG** as the poster and does **not** render a broken `<img>` for the GIF.

Do not commit fake GIF bytes. Do not hotlink an external GIF.
