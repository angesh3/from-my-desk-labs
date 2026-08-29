from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB003_STATIC = REPO_ROOT / "labs" / "003-agent-access-control" / "static"

PAGES = ("/", "/labs", "/labs/know-your-agent", "/labs/delegated-authority", "/labs/agent-access-control")
FORBIDDEN_SNIPPETS = (
    "r2.dev",
    "r2.cloudflarestorage",
    "file://",
    "/Users/",
    "/static/architecture.svg",
    "from-my-desk-logo-source.png",
)


def test_main_pages_ok():
    for path in PAGES:
        response = client.get(path)
        assert response.status_code == 200, path


def test_global_branding_and_navigation():
    for path in PAGES:
        html = client.get(path).text
        assert "/static/brand/from-my-desk-logo.webp" in html
        assert "/static/brand/favicon.png" in html
        assert 'aria-label="From My Desk home"' in html
        assert 'href="/"' in html
        assert 'href="/labs"' in html
        assert "Know Your Agent" in html
        assert "GitHub" in html
        assert "Newsletter" in html
        assert "Perspectives shaped by experience" in html or path != "/"


def test_home_copy_is_publication_wide():
    html = client.get("/").text
    lowered = html.lower()
    assert "Perspectives shaped by experience" in html
    assert "leadership" in lowered
    assert "artificial intelligence" in lowered
    assert "technology" in lowered
    assert "innovation" in lowered
    assert "digital trust" in lowered
    assert "continuous learning" in lowered
    assert "Angesh Vikram" in html
    assert "control plane around AI agents" not in html
    assert "control plane around AI agents" not in lowered
    assert "Each edition is educational" not in html
    assert "Nothing here executes a financial transaction" not in html


def test_catalog_renders_lab_cards():
    home = client.get("/").text
    labs = client.get("/labs").text
    for html in (home, labs):
        assert "Know Your Agent: Identity Is Only the Beginning" in html
        assert "Delegated Authority" in html
        assert "Agent Access Control" in html
        assert "Explore the interactive lab" in html or "Explore lab" in html
        assert "AI Agents" in html
        assert "Interactive demo" in html
        assert "/labs/know-your-agent" in html
        assert "/labs/delegated-authority" in html
        assert "/labs/agent-access-control" in html
        assert "Not investment advice" in html or "No real accounts" in html


def test_lab002_page_basics():
    html = client.get("/labs/delegated-authority").text
    assert "Delegated Authority" in html
    assert "Evaluate delegated authority" in html
    assert 'data-scenario="execution_not_delegated"' in html
    assert "/static/labs/002/delegated-authority-workflow.svg" in html
    assert "/static/labs/002/system-architecture.svg" in html
    assert "/static/labs/002/evaluation-flow.svg" in html
    assert "/static/labs/002/fallback-flow.svg" in html
    assert "/static/labs/002/revocation-flow.svg" in html
    assert "/static/labs/002/architecture.svg" not in html
    assert "/static/labs/002/lab.js" in html
    assert "Open Lab 001" in html
    assert "authority-chain" in html
    assert "journey-stepper" in html
    assert "How to use this Lab" in html
    assert "preset-card" in html
    assert "not_performed" in html


def test_lab003_page_basics():
    html = client.get("/labs/agent-access-control").text
    assert "Agent Access Control" in html
    assert "Run evaluation" in html
    assert 'data-scenario="undelegated_capability"' in html
    assert 'data-scenario="unknown_agent_registration"' in html
    assert "/static/labs/003/nac-comparison.svg" in html
    assert "/static/labs/003/live-authority-evaluation.svg" in html
    assert "/static/labs/003/management-plane.svg" in html
    assert "/static/labs/003/restricted-mode.svg" in html
    assert "/static/labs/003/reevaluation-change.svg" in html
    assert "/static/labs/003/lab.js" in html
    assert "Open Lab 001" in html
    assert "Open Lab 002" in html
    assert "live-eval-stepper" in html
    assert "How to use this Lab" in html
    assert "preset-card" in html
    assert "eval-mode" in html
    assert "not_performed" in html
    assert "guided-live-status" in html
    assert "aria-live=\"polite\"" in html
    assert "emerging Agent Authority Model" in html
    assert "not presented as an established industry standard" in html
    assert 'id="live-authority-evaluation"' in html
    assert html.count('id="live-authority-evaluation"') == 1
    assert 'id="live-eval-heading"' in html
    assert 'tabindex="-1"' in html


def test_lab_page_order_and_copy():
    html = client.get("/labs/know-your-agent").text
    title_at = html.find("Identity Is Only the Beginning")
    gif_at = html.find("/static/labs/001/know-your-agent-trust-workflow.gif")
    presets_at = html.find("Scenario presets")
    arch_at = html.find('id="architecture"')
    assert 0 < title_at < gif_at < presets_at < arch_at
    assert "From identity to decision" in html
    assert "The agent trust flow: identity establishes who is acting." in html
    assert 'id="evaluate-form"' in html
    assert "<label>Principal" in html
    assert 'id="customer_confirmed"' in html
    assert 'data-preset="allow-4k"' in html
    assert "not investment advice" in html.lower()
    assert "/static/labs/001/architecture.svg" in html
    assert '"enabled": false' in html
    assert 'id="result"' in html
    assert "This lab separates four responsibilities that are often treated as one." in html
    assert "audit record" in html
    assert "audit ID" in html
    assert "1. Reader2" not in html
    assert "Reader2. Interactive" not in html
    assert "Up to 5,000" in html
    assert "Above 15,000" in html


def test_forbidden_urls_absent_from_html():
    for path in PAGES:
        html = client.get(path).text
        for snippet in FORBIDDEN_SNIPPETS:
            assert snippet not in html, (path, snippet)


def test_static_assets():
    assets = [
        ("/static/brand/from-my-desk-logo.webp", "image/webp"),
        ("/static/brand/favicon.png", "image/png"),
        ("/static/css/styles.css", "text/css"),
        ("/static/js/site.js", "javascript"),
        ("/static/labs/001/know-your-agent-trust-workflow.gif", "image/gif"),
        ("/static/labs/001/architecture.svg", "image/svg+xml"),
        ("/static/labs/001/lab.js", "javascript"),
        ("/static/labs/002/delegated-authority-workflow.svg", "image/svg+xml"),
        ("/static/labs/002/system-architecture.svg", "image/svg+xml"),
        ("/static/labs/002/evaluation-flow.svg", "image/svg+xml"),
        ("/static/labs/002/fallback-flow.svg", "image/svg+xml"),
        ("/static/labs/002/revocation-flow.svg", "image/svg+xml"),
        ("/static/labs/002/lab.js", "javascript"),
        ("/static/labs/003/nac-comparison.svg", "image/svg+xml"),
        ("/static/labs/003/live-authority-evaluation.svg", "image/svg+xml"),
        ("/static/labs/003/management-plane.svg", "image/svg+xml"),
        ("/static/labs/003/restricted-mode.svg", "image/svg+xml"),
        ("/static/labs/003/reevaluation-change.svg", "image/svg+xml"),
        ("/static/labs/003/lab.js", "javascript"),
    ]
    for url, content_type in assets:
        response = client.get(url)
        assert response.status_code == 200, url
        assert content_type in response.headers["content-type"], (url, response.headers["content-type"])


def test_source_logo_is_not_public():
    html = client.get("/").text
    assert "from-my-desk-logo-source.png" not in html
    source = client.get("/static/brand/from-my-desk-logo-source.png")
    assert source.status_code == 404


def test_lab_javascript_presets():
    js = client.get("/static/labs/001/lab.js").text
    assert "allow-4k" in js
    assert "quantity: 100" in js
    assert "unknown-bot" in js
    assert "kya-agent-revoked" in js
    assert "MAPLE" in js


def test_lab003_javascript_guided_evaluating_state():
    js = client.get("/static/labs/003/lab.js").text
    assert "isEvaluating" in js
    assert "EVALUATING_MS" in js
    assert "guided-live-status" in js
    assert "announceLive" in js


def test_lab003_javascript_run_evaluation_navigation():
    js = client.get("/static/labs/003/lab.js").text
    assert "scrollToLiveAuthorityEvaluation" in js
    assert "live-authority-evaluation" in js
    assert "selected.scrollIntoView" not in js
    assert "prefersReducedMotion" in js
    assert "followProgress" in js
    assert "followActivePhaseIfNeeded" in js
    assert "isElementComfortablyVisible" in js


def test_lab003_page_follow_progress_control():
    html = client.get("/labs/agent-access-control").text
    assert 'id="follow-progress"' in html
    assert "Follow progress" in html
    assert 'type="checkbox"' in html


def test_lab003_diagram_urls_from_rendered_html():
    html = client.get("/labs/agent-access-control").text
    srcs = re.findall(r'src="(/static/labs/003/[^"]+\.svg)"', html)
    assert len(srcs) == 5
    expected = {
        "/static/labs/003/nac-comparison.svg",
        "/static/labs/003/live-authority-evaluation.svg",
        "/static/labs/003/management-plane.svg",
        "/static/labs/003/restricted-mode.svg",
        "/static/labs/003/reevaluation-change.svg",
    }
    assert set(srcs) == expected
    for url in srcs:
        response = client.get(url)
        assert response.status_code == 200, url
        assert "image/svg+xml" in response.headers["content-type"], (
            url,
            response.headers["content-type"],
        )
        body = response.content
        assert len(body) > 100, url
        stripped = body.lstrip()
        assert stripped.startswith(b"<?xml") or stripped.startswith(b"<svg"), url
        body.decode("utf-8")
        ET.parse(io.BytesIO(body))
        filename = url.rsplit("/", 1)[-1]
        source = LAB003_STATIC / filename
        assert source.is_file(), filename
        assert source.read_bytes() == body, filename


def test_lab003_source_svgs_are_valid_utf8_xml():
    for path in sorted(LAB003_STATIC.glob("*.svg")):
        data = path.read_bytes()
        data.decode("utf-8")
        ET.parse(path)
        assert b"<title" in data
        assert b"<desc" in data
