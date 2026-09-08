from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from from_my_desk.config import reset_settings_cache
from from_my_desk.main import app, reset_catalog

from .test_catalog import dump, valid_lab

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_catalog_for_test():
    reset_settings_cache()
    reset_catalog()
    yield
    reset_settings_cache()
    reset_catalog()

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB003_STATIC = REPO_ROOT / "labs" / "003-agent-access-control" / "static"
LAB004_STATIC = REPO_ROOT / "labs" / "004-agent-escalation-boundary" / "static"

PAGES = ("/", "/labs", "/labs/know-your-agent", "/labs/delegated-authority", "/labs/agent-access-control", "/labs/agent-escalation-boundary")
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
        assert "GitHub" in html
        assert "Newsletter" in html
        if path == "/":
            assert "Latest Lab" in html
            assert 'href="/labs/agent-escalation-boundary"' in html
        if path == "/labs/know-your-agent":
            assert "Know Your Agent" in html
        elif path == "/labs/agent-access-control":
            assert "Agent Access Control" in html
        elif path == "/labs/delegated-authority":
            assert "Delegated Authority" in html
        elif path == "/labs/agent-escalation-boundary":
            assert "Escalation Boundary" in html
        else:
            assert "From My Desk" in html or "Labs" in html


def test_home_copy_is_personal_and_current():
    html = client.get("/").text
    lowered = html.lower()
    assert "Ideas I'm working through" in html
    assert "intersection of ai, engineering, architecture, security" in lowered
    assert "Written and built by Angesh Vikram." in html
    assert "Perspectives shaped by experience" not in html
    assert "leadership, artificial intelligence" not in lowered
    assert "continuous learning" not in lowered
    assert "Articles, field notes, visual explanations" not in html
    assert "control plane around AI agents" not in lowered
    assert "Each edition is educational" not in html


def test_homepage_features_latest_lab():
    html = client.get("/").text
    assert "Latest Lab" in html
    assert "Current edition" not in html
    assert "CURRENT EDITION" not in html
    assert "The Agent Escalation Boundary" in html
    assert 'href="/labs/agent-escalation-boundary"' in html
    assert "Explore Lab 004" in html
    assert "Browse all Labs" in html
    assert "An agent can be authorized to act and still need to pause" in html


def test_homepage_earlier_labs_ordered_newest_first():
    html = client.get("/").text
    assert "Earlier Labs" in html
    earlier_block = html.split("Earlier Labs", 1)[1].split("Follow From My Desk", 1)[0]
    lab003_pos = earlier_block.find("/labs/agent-access-control")
    lab002_pos = earlier_block.find("/labs/delegated-authority")
    lab001_pos = earlier_block.find("/labs/know-your-agent")
    assert lab003_pos < lab002_pos < lab001_pos
    assert "Delegated Authority" in earlier_block
    assert "Agent Access Control" in earlier_block
    assert "KYA" not in earlier_block
    assert "/labs/agent-escalation-boundary" not in earlier_block


def test_homepage_bottom_structure_and_cta():
    html = client.get("/").text
    assert "On the desk" not in html
    assert "From the newsletter" not in html
    assert "Future work lands here" not in html
    assert "Follow From My Desk" in html
    assert "Follow on LinkedIn" in html
    assert "View the source" in html
    assert "Subscribe on LinkedIn" not in html
    assert "https://www.linkedin.com/newsletters/from-my-desk-7492634647890341890/" in html
    assert "https://github.com/angesh3/from-my-desk-labs" in html
    assert "Written and built by Angesh Vikram" in html
    assert html.count("Explore Lab 004") == 1


def test_homepage_latest_lab_excluded_from_earlier_labs():
    html = client.get("/").text
    earlier_block = html.split("Earlier Labs", 1)[1].split("Follow From My Desk", 1)[0]
    assert "The Agent Escalation Boundary" not in earlier_block


def test_homepage_single_published_lab_has_no_earlier_section(tmp_path, monkeypatch):
    catalog_path = tmp_path / "labs.yaml"
    dump(
        catalog_path,
        [
            valid_lab(id="003", edition_number=3, slug="agent-access-control", title="Agent Access Control", featured=False),
        ],
    )
    monkeypatch.setenv("CATALOG_PATH", str(catalog_path))
    reset_settings_cache()
    reset_catalog()
    html = client.get("/").text
    assert "Earlier Labs" not in html
    assert "Latest Lab" in html


def test_homepage_draft_labs_excluded_from_earlier(tmp_path, monkeypatch):
    catalog_path = tmp_path / "labs.yaml"
    dump(
        catalog_path,
        [
            valid_lab(id="001", edition_number=1, featured=False, reader_title="Know Your Agent"),
            valid_lab(
                id="003",
                edition_number=3,
                slug="agent-access-control",
                title="Agent Access Control",
                featured=False,
            ),
            valid_lab(
                id="004",
                edition_number=4,
                slug="future-lab",
                title="Future Lab",
                lab_url="/labs/future-lab",
                status="draft",
                featured=False,
            ),
        ],
    )
    monkeypatch.setenv("CATALOG_PATH", str(catalog_path))
    reset_settings_cache()
    reset_catalog()
    html = client.get("/").text
    assert "Earlier Labs" in html
    assert "Future Lab" not in html.split("Follow From My Desk", 1)[0]
    assert "Know Your Agent" in html


def test_homepage_latest_lab_selection_updates_with_catalog(tmp_path, monkeypatch):
    catalog_path = tmp_path / "labs.yaml"
    dump(
        catalog_path,
        [
            valid_lab(id="001", edition_number=1, featured=False),
            valid_lab(
                id="003",
                edition_number=3,
                slug="agent-access-control",
                title="Agent Access Control",
                featured=False,
            ),
            valid_lab(
                id="004",
                edition_number=4,
                slug="future-lab",
                title="Future Lab",
                lab_url="/labs/future-lab",
                featured=False,
            ),
        ],
    )
    monkeypatch.setenv("CATALOG_PATH", str(catalog_path))
    reset_settings_cache()
    reset_catalog()
    html = client.get("/").text
    assert "Future Lab" in html
    assert 'href="/labs/future-lab"' in html
    assert "Latest Lab · Lab 004" in html


def test_labs_index_ordered_newest_first():
    html = client.get("/labs").text
    lab004_pos = html.find("/labs/agent-escalation-boundary")
    lab003_pos = html.find("/labs/agent-access-control")
    lab002_pos = html.find("/labs/delegated-authority")
    lab001_pos = html.find("/labs/know-your-agent")
    assert lab004_pos < lab003_pos < lab002_pos < lab001_pos


def test_catalog_renders_lab_cards():
    home = client.get("/").text
    labs = client.get("/labs").text
    assert "The Agent Escalation Boundary" in home
    assert "/labs/agent-escalation-boundary" in home
    assert "Know Your Agent" in labs
    assert "Delegated Authority" in labs
    assert "Agent Access Control" in labs
    assert "The Agent Escalation Boundary" in labs
    assert "Explore lab" in labs or "Explore Lab" in labs
    assert "AI Agents" in labs or "Agent Governance" in labs
    assert "Interactive demo" in labs
    assert "/labs/know-your-agent" in labs
    assert "/labs/delegated-authority" in labs
    assert "/labs/agent-access-control" in labs
    assert "/labs/agent-escalation-boundary" in labs
    assert "Not investment advice" in labs or "No real accounts" in labs or "educational policy prototype" in labs.lower()


def test_lab004_page_basics():
    html = client.get("/labs/agent-escalation-boundary").text
    assert "The Agent Escalation Boundary" in html
    assert "Run execution judgment" in html
    assert 'data-preset="clear_session_revoke"' in html
    assert 'data-preset="immediate_threat_bounded"' in html
    assert "/static/labs/004/escalation-boundary.svg" in html
    assert "/static/labs/004/lab.js" in html
    assert "PROCEED" in html
    assert "CLARIFY" in html
    assert "ESCALATE" in html
    assert "STOP" in html
    assert "EDITION_4_NEWSLETTER_URL" not in html
    assert "[EDITION_4_NEWSLETTER_URL]" not in html
    assert "The companion Edition 4 newsletter will be linked here after publication." in html
    assert "Read the companion newsletter" not in html
    assert "Previous Lab: Agent Access Control" in html
    assert 'href="/labs/agent-access-control"' in html
    assert "not_performed" in html
    assert 'alt="Flow from context and authority through uncertainty evaluation to proceed, clarify, escalate, or stop, then explain and record."' in html


def test_lab004_newsletter_button_when_published(monkeypatch, tmp_path):
    catalog = tmp_path / "labs.yaml"
    dump(
        catalog,
        [
            valid_lab(
                id="004",
                edition_number=4,
                slug="agent-escalation-boundary",
                title="The Agent Escalation Boundary",
                lab_url="/labs/agent-escalation-boundary",
                newsletter_url="https://www.linkedin.com/newsletters/from-my-desk-example/",
                featured=True,
            )
        ],
    )
    monkeypatch.setenv("CATALOG_PATH", str(catalog))
    reset_settings_cache()
    reset_catalog()
    html = client.get("/labs/agent-escalation-boundary").text
    assert "Read the companion newsletter" in html
    assert 'href="https://www.linkedin.com/newsletters/from-my-desk-example/"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "data-lab004-newsletter" in html
    assert "The companion Edition 4 newsletter will be linked here after publication." not in html
    assert "EDITION_4_NEWSLETTER_URL" not in html


def test_labs_index_hides_placeholder_newsletter():
    html = client.get("/labs").text
    assert "EDITION_4_NEWSLETTER_URL" not in html
    assert "[EDITION_4_NEWSLETTER_URL]" not in html


def test_lab004_api_evaluate_smoke():
    response = client.post(
        "/api/labs/004/evaluate-preset/clear_session_revoke"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["execution_outcome"] == "proceed"
    assert body["execution"] == "not_performed"


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
        ("/static/labs/004/escalation-boundary.svg", "image/svg+xml"),
        ("/static/labs/004/lab.js", "javascript"),
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


def test_lab004_diagram_url_from_rendered_html():
    html = client.get("/labs/agent-escalation-boundary").text
    srcs = re.findall(r'src="(/static/labs/004/[^"]+\.svg)"', html)
    assert srcs == ["/static/labs/004/escalation-boundary.svg"]
    response = client.get(srcs[0])
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    body = response.content
    assert len(body) > 100
    stripped = body.lstrip()
    assert stripped.startswith(b"<?xml") or stripped.startswith(b"<svg")
    body.decode("utf-8")
    ET.parse(io.BytesIO(body))
    source = LAB004_STATIC / "escalation-boundary.svg"
    assert source.is_file()
    assert source.read_bytes() == body


def test_lab004_source_svg_is_valid_utf8_xml():
    path = LAB004_STATIC / "escalation-boundary.svg"
    data = path.read_bytes()
    data.decode("utf-8")
    ET.parse(path)
    assert b"<title" in data
    assert b"<desc" in data
    assert b"PROCEED" in data
    assert b"CLARIFY" in data
    assert b"ESCALATE" in data
    assert b"STOP" in data