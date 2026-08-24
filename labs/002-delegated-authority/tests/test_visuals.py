"""Lab 002 visual assets and reader-facing UI contracts."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi.testclient import TestClient

from from_my_desk.main import app

REPO = Path(__file__).resolve().parents[3]
LAB = REPO / "labs" / "002-delegated-authority"
STATIC = LAB / "static"
DIAGRAMS = LAB / "diagrams"
GIF = STATIC / "delegated-authority-trust-workflow.gif"
TEMPLATE = REPO / "website" / "app" / "templates" / "lab002.html"

client = TestClient(app)

FIVE_DIAGRAMS = (
    "delegated-authority-workflow.svg",
    "system-architecture.svg",
    "evaluation-flow.svg",
    "fallback-flow.svg",
    "revocation-flow.svg",
)


def _assert_svg_response(path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, path
    assert "image/svg+xml" in response.headers["content-type"], path
    text = response.text
    assert text.lstrip().startswith("<?xml") or "<svg" in text[:200], path
    root = ET.fromstring(text)
    assert root.tag.endswith("svg"), path
    assert "viewBox" in root.attrib or "viewbox" in {k.lower() for k in root.attrib}, path
    lowered = text.lower()
    assert "cdn." not in lowered
    assert "fonts.googleapis" not in lowered
    assert 'xlink:href="http' not in lowered
    assert "\x14" not in text
    return text


def test_five_unique_diagram_routes():
    bodies = []
    for name in FIVE_DIAGRAMS:
        text = _assert_svg_response(f"/static/labs/002/{name}")
        bodies.append(hashlib.md5(text.encode("utf-8")).hexdigest())
        assert (STATIC / name).is_file()
        assert (DIAGRAMS / name).is_file()
    assert len(set(bodies)) == 5, "diagrams must not be duplicates of each other"


def test_architecture_svg_duplicate_removed():
    assert not (STATIC / "architecture.svg").exists()
    assert not (DIAGRAMS / "architecture.svg").exists()
    assert client.get("/static/labs/002/architecture.svg").status_code == 404


def test_system_architecture_diagram_files_valid():
    svg = (DIAGRAMS / "system-architecture.svg").read_text(encoding="utf-8")
    ET.fromstring(svg)
    mmd = (DIAGRAMS / "system-architecture.mmd").read_text(encoding="utf-8")
    assert "Trust Gateway" in mmd or "Trust Gateway" in svg
    assert "Separate executor" in svg


def test_workflow_diagram_is_end_to_end():
    svg = (STATIC / "delegated-authority-workflow.svg").read_text(encoding="utf-8")
    ET.fromstring(svg)
    assert "Human Principal" in svg
    assert "Trust Gateway" in svg
    assert "ALLOW" in svg or "ALLOW ACTION" in svg


def test_lab_page_embeds_all_five_diagrams_and_no_broken_gif():
    html = client.get("/labs/delegated-authority").text
    for name in FIVE_DIAGRAMS:
        assert f'/static/labs/002/{name}' in html, name
    assert "/static/labs/002/architecture.svg" not in html
    assert "journey-stepper" in html
    assert "authority-chain" in html
    assert "How to use this Lab" in html
    assert "preset-card" in html
    assert 'aria-pressed="false"' in html
    assert "Evaluate delegated authority" in html
    assert "Ordered policy evaluation" in html
    assert "Restricted fallback" in html
    assert "Revocation propagates downstream" in html
    if GIF.is_file():
        assert "/static/labs/002/delegated-authority-trust-workflow.gif" in html
        gif = client.get("/static/labs/002/delegated-authority-trust-workflow.gif")
        assert gif.status_code == 200
        assert "image/gif" in gif.headers["content-type"]
    else:
        assert "delegated-authority-trust-workflow.gif" not in html
        assert "Animated GIF not installed" in html or "ASSETS.md" in html


def test_lab_js_human_readable_journey_and_fallback():
    js = client.get("/static/labs/002/lab.js").text
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "Verified" in js
    assert "Original action stopped" in js
    assert "Policy approved; execution remains separate" in js
    assert "humanStage" in js
    assert "fallback-steps" in js
    assert "The original decision remains unchanged" in js
    assert "aria-pressed" in template
    assert "Technical details" in js or "tech-details" in js


def test_demo_guide_and_assets_docs_exist():
    demo = (LAB / "docs" / "demo-guide.md").read_text(encoding="utf-8")
    assets = (LAB / "docs" / "ASSETS.md").read_text(encoding="utf-8")
    assert "Valid narrow delegation" in demo
    assert "not_performed" in demo
    assert "delegated-authority-trust-workflow.gif" in assets
    assert "delegated-authority-workflow.svg" in assets
    assert "system-architecture.svg" in assets
    assert "evaluation-flow.svg" in assets
    assert "fallback-flow.svg" in assets
    assert "revocation-flow.svg" in assets
    assert "99e92baecbb68a5a6321b1b774018c81" in assets
