# Lab 003 Implementation Progress

## Baseline

- Branch: feat/002-delegated-authority
- Initial git status: clean working tree
- Baseline test command: `.venv/bin/pytest -q`
- Baseline test result: 124 passed, 2 skipped
- Baseline test count: 124 passed, 2 skipped
- Local health result: not run at baseline (Docker optional)

## Phase 0 — Repository inspection

- [x] Repository instructions reviewed
- [x] Existing architecture mapped
- [x] Labs 001 and 002 patterns documented
- [x] Reusable components identified
- [x] Baseline tests passed
- [x] Implementation approach selected

**Progressive delivery:** deterministic client-side replay of canonical `events` returned by `POST /api/labs/003/evaluate`. Guided mode animates the same list (~650 ms per step); Instant mode renders it immediately. `prefers-reduced-motion` skips animation delays. No SSE; policy behavior is server-authoritative.

## Phase 1 — Policy and schemas

- [x] Scenario schema
- [x] Request schema
- [x] Event schema
- [x] Result and audit schema
- [x] Reason-code registry
- [x] Policy invariants
- [x] Schema and policy tests

## Phase 2 — Evaluation engine

- [x] Agent Management Plane registry
- [x] Agent state evaluation
- [x] APE profiling
- [x] APSE posture
- [x] Action evaluation
- [x] Tool evaluation
- [x] Resource and data evaluation
- [x] Purpose evaluation
- [x] Limit evaluation
- [x] Delegation evaluation
- [x] Context evaluation
- [x] Decision precedence
- [x] Restricted Agent Mode
- [x] Audit evidence

## Phase 3 — Progressive evaluation

- [x] Ordered evaluation events
- [x] Guided mode
- [x] Instant mode
- [x] Pause
- [x] Next
- [x] Resume
- [x] Replay
- [x] Reset
- [x] Skipped-event explanations
- [x] Reduced-motion behavior

## Phase 4 — Lab interface

- [x] Lab catalog entry
- [x] Lab route
- [x] Scenario selector
- [x] Agent-state summary
- [x] Request summary
- [x] Advanced controls
- [x] Live Authority Evaluation
- [x] Decision card
- [x] Evidence drawer
- [x] Audit panel
- [x] Restricted recovery panel
- [x] Responsive layout
- [x] Accessibility

## Phase 5 — Visuals and content

- [x] NAC-to-Agent-Access comparison
- [x] Live Authority Evaluation diagram
- [x] Agent Management Plane diagram
- [x] Unknown Agent Restricted Mode diagram
- [x] SVG accessibility
- [x] PNG export instructions
- [x] Educational disclaimer

## Phase 6 — Verification

- [x] Focused Lab 003 tests
- [x] Policy invariant tests
- [x] Full regression suite
- [x] Local application
- [x] Docker build and run
- [x] Health endpoint
- [x] Static asset routes
- [x] Manual scenario checks
- [x] Labs 001 and 002 regression checks
- [x] Security and privacy review
- [x] Final git diff review

## Final results

- Final test command: `.venv/bin/pytest -q`
- Final test result: 141 passed, 2 skipped
- Final test count: 141 passed, 2 skipped
- Docker result: `docker compose build` + `docker compose up -d --force-recreate` succeeded; health 200; Lab 003 page and all static SVGs 200; 14 scenarios via API all OK
- Local Lab URL: http://127.0.0.1:8080/labs/agent-access-control (Docker Compose on port 8080)
- Files added:
  - `LAB_003_PROGRESS.md`
  - `labs/003-agent-access-control/` (package, policies, examples, tests, static SVGs, docs, README)
  - `website/app/templates/lab003.html`
  - `labs/001-know-your-agent/tests/conftest.py` (importlib test path helper)
- Files modified:
  - `README.md`
  - `Dockerfile`
  - `docker-compose.yml`
  - `pyproject.toml`
  - `pytest.ini`
  - `website/app/config.py`
  - `website/app/main.py`
  - `website/app/static/css/styles.css`
  - `website/app/static/js/site.js`
  - `website/catalog/labs.yaml`
  - `website/tests/test_catalog.py`
  - `website/tests/test_installed_layout.py`
  - `website/tests/test_live_docker.py`
  - `website/tests/test_runtime_resources.py`
  - `website/tests/test_site.py`
- Known limitations:
  - Guided/Instant equivalence is enforced at the canonical API layer; no browser automation tests for pause/next/replay UI timing
  - PNG diagram exports are manual (Inkscape); see `labs/003-agent-access-control/docs/ASSETS.md`
  - Lab 003 telemetry events follow Lab 002 patterns; full PostHog property allowlist not extended for every Lab 003 interaction
  - Scenario-driven evaluation only (no free-form request editor like Lab 001)
- Recommended next steps:
  - Create branch `feat/003-agent-access-control` before commit (currently on `feat/002-delegated-authority`)
  - Commit on dedicated branch when ready
  - Optional browser/visual regression tests for Live Authority Evaluation stepper
  - Newsletter PNG export via documented Inkscape commands
  - Extend `site.js` telemetry allowlist for Lab 003-specific events if analytics review requires it

## Final polish (pre-commit)

- Branch: `feat/003-agent-access-control`
- Guided Evaluating state: two-phase guided step (220 ms Evaluating + 430 ms final per event, 650 ms total); `is-evaluating` highlight; Instant/reduced-motion unchanged
- Accessible announcements: `#guided-live-status` with `aria-live="polite"`; removed `aria-live` from event list
- Conceptual framing: NAC section note on emerging Agent Authority Model (not an industry standard)
- Focused tests: `labs/003-agent-access-control/tests` — 16 passed; `test_lab003_javascript_guided_evaluating_state` added
- Full suite: `.venv/bin/pytest -q` — 143 passed, 2 skipped
- Docker: rebuild + recreate succeeded; health, Lab 003 page, lab.js, 5 SVGs, ALLOW/STEP_UP/DENY API scenarios verified
- Manual Guided verification: documented below (browser automation unavailable in review environment)
- Instant mode: shows all final states immediately (no Evaluating phase)

### Manual Guided-mode checklist

1. Select scenario → Run evaluation → first event shows **Evaluating** then **Passed/Failed/Attention/Skipped**
2. Pause during Evaluating → progression stops; Resume continues
3. Next while paused → finalizes current event and advances
4. Replay → stepper resets and replays with Evaluating phases
5. Reset → clears stepper and live status
6. Screen reader: `#guided-live-status` announces concise step updates (not full evidence)

## Run Evaluation navigation fix

- **Root cause:** After a successful API response, `evaluate()` called `selected.scrollIntoView({ block: "nearest", behavior: "smooth" })` on the selected preset card (pattern copied from Lab 002), scrolling the page back to the scenario group (e.g. Delegation failures).
- **Fix:** Removed preset-card scroll; added `#live-authority-evaluation` section target, `scrollToLiveAuthorityEvaluation()` (once per Run), heading focus with `preventScroll: true`, `scroll-margin-top` on live eval panel.
- **Files changed:** `lab003.html`, `lab.js`, `styles.css`, `test_site.py`
- **Automated tests:** `test_lab003_javascript_run_evaluation_navigation`; page asserts unique `live-authority-evaluation` id
- **Full suite:** 143 passed, 2 skipped
- **Docker:** rebuild + recreate verified; deployed `lab.js` has `scrollToLiveAuthorityEvaluation`, no `selected.scrollIntoView`
- **Manual combinations:** Run Evaluation should land at Live Authority Evaluation for all Guided/Instant scenario pairs (verify locally in browser)

## Diagram rendering fix

- **Root cause:** `live-authority-evaluation.svg` and `restricted-mode.svg` contained invalid UTF-8 byte `0xb7` (corrupted separator bytes). URLs returned HTTP 200 with `image/svg+xml`, but browsers could not decode or render the SVG, showing broken-image icons and alt text.
- **Fix:** Replaced invalid bytes with UTF-8 em dashes (`—`) in subtitle and label text; no template URL or static-mount changes required.
- **Diagram files (canonical):** `nac-comparison.svg`, `live-authority-evaluation.svg`, `management-plane.svg`, `restricted-mode.svg`, `reevaluation-change.svg`
- **Rendered routes:** `/static/labs/003/nac-comparison.svg`, `/static/labs/003/live-authority-evaluation.svg`, `/static/labs/003/management-plane.svg`, `/static/labs/003/restricted-mode.svg`, `/static/labs/003/reevaluation-change.svg`
- **Tests added:** `test_lab003_diagram_urls_from_rendered_html`, `test_lab003_source_svgs_are_valid_utf8_xml`
- **Full suite:** 145 passed, 2 skipped
- **Docker:** rebuild + recreate; all five rendered diagram URLs return valid parseable UTF-8 SVG

- Review date: 2026-08-29
- Branch at review: `feat/002-delegated-authority` (expected `feat/003-agent-access-control` — commit blocked until branch created)
- Review fixes applied:
  - Corrected undeclared-tool preset learn text in `lab003.html`
  - Fixed corrupted control characters in `nac-comparison.svg` and `management-plane.svg`
  - Event stepper status labels now show Passed / Attention / Failed / Skipped (not generic Completed on failures)
- Lab 001 `conftest.py`: required with `--import-mode=importlib` (isolates duplicate `test_api.py` modules; enables Lab 001 sibling imports)
- Post-fix tests: `.venv/bin/pytest -q` → 141 passed, 2 skipped
- Post-fix Docker: build + recreate OK; health, Labs 001–003, Lab 003 static assets, evaluate API verified
- Browser review: desktop and 390px mobile layouts OK; Guided ALLOW and Instant DENY with restricted recovery verified
- Diagram zoom: not implemented in repository (static figures only; consistent with Labs 001/002)

## Final experience review (2026-08-29)

- Branch: `feat/003-agent-access-control`
- Status: PASS

### Diagram corrections

- **Incoming request:** Forked arrows to Actor and Request with visible arrowheads on each branch.
- **Actor and Request:** Sub-lines `Agent + Principal` and `Action + Tool + Data + Purpose`; parallel layout preserved.
- **Authority:** Converging arrows from both branches into `Limits + Delegation`.
- **Decision and Audit:** Solid arrow to Audit record with “Always recorded” label.
- **Restricted path:** Dashed gold arrow labeled “If recovery is permitted” with “Optional new path”; not mutually exclusive with audit.
- **Other diagrams:** Management plane — three separate arrows from Registry, Inventory, Profiles into gateway; NAC comparison — dashed optional arrow to restricted recovery with “if eligible” label.

### Follow progress

- Checkbox near Guided/Instant controls; default enabled; hidden in Instant mode.
- Scrolls active phase group only when group changes and element is outside comfortable viewport (`block: center`).
- No scroll on Evaluating→final within same phase, Pause, Reset, or evidence expansion.
- Replay scrolls once to Live Authority Evaluation; Run evaluation retains one-time navigation.
- Reduced motion uses `behavior: auto`; polite live announcements preserved.

### Human editorial pass

- Intro, NAC framing, how-to, diagram captions, teaching notes, scenario cards (`Notice:` pattern).
- Catalog summary rewritten; scenario IDs, API fields, reason codes, `execution: not_performed` unchanged.

### Verification

- Focused Lab 003 tests: 16 passed
- Site tests: 16 passed (includes follow-progress control + diagram UTF-8 checks)
- Full suite: 146 passed, 2 skipped
- Docker: rebuild + recreate OK; page, lab.js, five SVGs HTTP 200; evaluate returns `execution: not_performed`
- Visual: live-authority fork/converge/split arrows verified in browser

- No commit, push, merge, or deployment performed.
