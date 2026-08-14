"""Production-style HTTP checks for pages and global/lab assets."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

PAGES = {
    "/": "Perspectives shaped by experience",
    "/labs": "Labs",
    "/labs/know-your-agent": "Know Your Agent",
}

ASSET_URL_RE = re.compile(
    r"""(?:href|src)=["'](/static/[^"']+)["']""",
    re.IGNORECASE,
)

FORBIDDEN = (
    "/Users/",
    "localhost:",
    "127.0.0.1",
    "r2.dev",
    "r2.cloudflarestorage",
    "from-my-desk-logo-source.png",
    "cdn.jsdelivr",
    "fonts.googleapis",
)


def test_pages_and_health():
    for path, needle in PAGES.items():
        response = client.get(path)
        assert response.status_code == 200, path
        assert needle in response.text
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


def test_global_assets_content_types_and_tokens():
    css = client.get("/static/css/styles.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    body = css.text
    assert body.strip()
    assert "--navy:" in body
    assert "--gold:" in body
    assert "--ivory:" in body
    assert ".site-header" in body

    js = client.get("/static/js/site.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]
    assert js.text.strip()

    logo = client.get("/static/brand/from-my-desk-logo.webp")
    assert logo.status_code == 200
    assert "image/webp" in logo.headers["content-type"]
    assert logo.content[:4] == b"RIFF"

    favicon = client.get("/static/brand/favicon.png")
    assert favicon.status_code == 200
    assert "image/png" in favicon.headers["content-type"]
    assert favicon.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_lab_assets():
    svg = client.get("/static/labs/001/architecture.svg")
    assert svg.status_code == 200
    assert "image/svg+xml" in svg.headers["content-type"]
    assert "Panel A" in svg.text

    gif = client.get("/static/labs/001/know-your-agent-trust-workflow.gif")
    assert gif.status_code == 200
    assert "image/gif" in gif.headers["content-type"]
    assert gif.content[:6] in {b"GIF87a", b"GIF89a"}


def test_html_emitted_assets_all_resolve():
    seen = set()
    for path in PAGES:
        html = client.get(path).text
        for snippet in FORBIDDEN:
            assert snippet not in html, (path, snippet)
        for match in ASSET_URL_RE.findall(html):
            seen.add(match)
            response = client.get(match)
            assert response.status_code == 200, (path, match)
    assert "/static/css/styles.css" in seen
    assert "/static/js/site.js" in seen
    assert "/static/brand/from-my-desk-logo.webp" in seen
    assert "/static/brand/favicon.png" in seen


def test_source_logo_png_not_public():
    response = client.get("/static/brand/from-my-desk-logo-source.png")
    assert response.status_code == 404
    source = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "source"
        / "from-my-desk-logo-source.png"
    )
    assert source.is_file()
