# From My Desk Labs

From My Desk is a publication of perspectives shaped by experience — across leadership, artificial intelligence, technology, innovation, digital trust, and continuous learning.

This repository hosts the public companion site and any editions that include a working lab, visual explanation, or technical spike. Not every edition is technical, and not every edition includes a demo. Lab 001, Know Your Agent, is the first published interactive edition.

```
from-my-desk-labs/
├── pyproject.toml          # installs the know_your_agent package
├── Dockerfile
├── docker-compose.yml
├── website/
│   ├── app/                # FastAPI pages, templates, public static assets
│   ├── assets/source/      # non-public master brand files
│   └── catalog/            # labs.yaml is the source of truth for discovery
└── labs/
    └── 001-know-your-agent/
        ├── src/know_your_agent/   # uniquely named Python package
        ├── policies/
        ├── examples/
        ├── tests/
        ├── diagrams/
        └── static/         # lab GIF, architecture SVG, lab.js
```

## Why the Python layout looks this way

There is **one FastAPI application** and **one Docker container**.

- Global HTTP pages, templates, catalog, and brand assets live under `website/app/`.
- Lab 001 domain code lives in the importable package `know_your_agent` at `labs/001-know-your-agent/src/know_your_agent/`.
- The numbered editorial directory cannot itself be a Python package (it contains a hyphen).
- The website imports the lab with `from know_your_agent.gateway import ...`.
- Packages are installed from `pyproject.toml`. Local development may use `pip install -e .`. The production image uses a non-editable `pip install .`.
- No multi-directory `PYTHONPATH` and no `sys.path` mutation.
- Uvicorn starts as `uvicorn from_my_desk.main:app`.

The high-resolution logo source is not a public static file. Pages use `/static/brand/from-my-desk-logo.webp` and `/static/brand/favicon.png`.

## Labs

Discovery is data-driven. Edit `website/catalog/labs.yaml`; do not hard-code editions into the home page.

| Lab | Title | What it demonstrates |
| --- | --- | --- |
| [001-know-your-agent](labs/001-know-your-agent) | Know Your Agent | Identity versus delegated authority. Four-way policy gate: ALLOW, CONFIRM, STEP_UP, DENY. Fictional paper-order simulation only. |

## Local setup

Python **3.11 or 3.12**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port 8080
```

`requirements-dev.txt` installs the `know_your_agent` package in editable mode. Do not set a multi-directory `PYTHONPATH`.

Open:

- http://127.0.0.1:8080/
- http://127.0.0.1:8080/labs
- http://127.0.0.1:8080/labs/know-your-agent
- http://127.0.0.1:8080/health

## Tests

```bash
pytest -q
```

## Docker

From the repository root:

```bash
docker compose up --build
```

Production image: non-root user `appuser` (uid 10001), non-editable `pip install .`, `uvicorn from_my_desk.main:app` with no `--reload`, health check on `GET /health`, `POSTHOG_ENABLED=false` by default. Bind `PORT` (Render sets this). Do not copy a `.env` with secrets into the image.

## Analytics (PostHog)

Product analytics are **off by default**. Localhost, `127.0.0.1`, and test hosts never load the PostHog browser SDK.

`POSTHOG_KEY` is a **public client project token** (`phc_…`) used by the browser SDK. It is **not** a Personal API key. Do not put a Personal API key in this repository, Docker image, or Render service.

### Configuration

Copy `.env.example` to `.env` for local development. Keep analytics disabled locally:

```
POSTHOG_ENABLED=false
POSTHOG_KEY=
POSTHOG_HOST=https://us.i.posthog.com
```

On Render (do not apply from this change), add the same names as **environment variables** on the Web Service. To collect production analytics after privacy review:

1. Create a PostHog project and copy the **Project API Key** shown for client-side use (`phc_…`).
2. Set `POSTHOG_ENABLED=true`.
3. Set `POSTHOG_KEY` to that public project token.
4. Set `POSTHOG_HOST=https://us.i.posthog.com` unless you use a different PostHog region or proxy.
5. Redeploy the Render service so the new env vars are available to the container.

Leave `POSTHOG_ENABLED=false` and `POSTHOG_KEY` empty until you intend to collect production analytics.

### Runtime behavior

`site.js` installs the official PostHog snippet (https://posthog.com/docs/libraries/js) and then calls `posthog.init` once. There is no second SDK `<script>` tag in HTML. The snippet injects `array.js` from the PostHog assets host only when all of the following are true:

- `POSTHOG_ENABLED` is true
- `POSTHOG_KEY` is non-empty
- the request hostname is not `localhost`, `127.0.0.1`, `::1`, or a test host

Initialization uses a single `posthog.init` with `defaults: '2026-05-30'`, `capture_pageview: false`, and `capture_pageleave: true`. After init succeeds, the `loaded` callback captures exactly one `$pageview` (`$current_url`, `$pathname`, `page_title` only). Autocapture and session recording stay off (`person_profiles: identified_only`, `persistence: localStorage+cookie`, `respect_dnt: true`). The site never calls `posthog.identify()`. Visitors remain anonymous.

When telemetry is enabled, Content-Security-Policy allowlists `https://*.i.posthog.com` and `https://*.posthog.com` on `script-src` and `connect-src`, plus `worker-src 'self' blob: data:`. A narrow host list can look installed while ingest stays empty.

Analytics failures are non-blocking. Pages, Lab 001, and `POST /api/evaluate` do not depend on PostHog. Visitors are never shown analytics errors.

### Events

Custom events are privacy-safe. They never include principal, agent, or account IDs; tickers; quantities; prices or notionals; audit IDs; request or response JSON; form values; credentials; explicit IP addresses; newsletter subscriber information; or raw href URLs.

| Event | Properties |
| --- | --- |
| `$pageview` | `$current_url`, `$pathname`, `page_title` only. Captured once after init. |
| `lab_preset_selected` | `lab_id` (`001`), `preset_category` (`allow`, `confirm`, `step_up`, or `deny`) |
| `policy_evaluation_completed` | `lab_id` (`001`), `decision` (`allow`, `confirm`, `step_up`, or `deny`), `reason_category` (generalized only: `ok`, `confirmation_required`, `step_up_required`, `amount_limit`, `identity`, `authority`, `scope`, `invalid_request`, or `other`) |
| `outbound_link_clicked` | `destination` (`github`, `linkedin_newsletter`, or `architecture`), `page_type` (`home`, `labs_index`, or `lab`) |

## Adding Lab 002

1. Create `labs/002-short-name/` with a uniquely named package such as `labs/002-short-name/src/short_name/` (not `models.py` or `gateway.py` at the top level).
2. Add that `src` directory to `[tool.setuptools.packages.find] where` in `pyproject.toml`, or add a second package mapping. Lab 002 must not reuse the `know_your_agent` package name.
3. Add domain code, tests, and lab-specific static assets.
4. Add one entry to `website/catalog/labs.yaml`.
5. Import its router in `website/app/main.py` with `from short_name.gateway import ...`.
6. Mount lab-specific static files under a stable URL such as `/static/labs/002/`.
7. Add tests for the catalog entry, page, and lab behavior.

Do not copy global templates, CSS, or the From My Desk logo into the lab directory.

## Render configuration (do not apply from this change)

Configure a **Web Service** that builds this repository with Docker:

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/angesh3/from-my-desk-labs` |
| Branch | the branch you intend to deploy (not applied by this change) |
| Root directory | repository root (empty / `.`) |
| Dockerfile path | `Dockerfile` |
| Build context | repository root |
| Health check | `GET /health` |
| Start command | image `CMD` (uvicorn, no `--reload`) |
| Environment | `PORT` from the platform; `POSTHOG_ENABLED=false`; `POSTHOG_HOST=https://us.i.posthog.com`; leave `POSTHOG_KEY` empty until a privacy review. `POSTHOG_KEY` is a public client project token, not a Personal API key. |

Optional public links: `PUBLIC_GITHUB_URL`, `PUBLIC_NEWSLETTER_URL`. Do not put production secrets in the image.

This change does **not** deploy, open a pull request, or modify DNS.

## Disclaimer

Interactive labs in this repository may use **fictional** companies, agents, accounts, tickers, and thresholds to make an idea concrete. Nothing here is investment advice, a trading system, a broker, or a representation of any real firm. No lab executes a financial transaction.
