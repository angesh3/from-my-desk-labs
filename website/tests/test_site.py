from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

PAGES = ("/", "/labs", "/labs/know-your-agent")
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
        assert "Explore the interactive lab" in html or "Explore lab" in html
        assert "AI Agents" in html
        assert "Interactive demo" in html
        assert "/labs/know-your-agent" in html
        assert "Not investment advice" in html


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
