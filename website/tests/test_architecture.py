from pathlib import Path

from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)

SVG_PATH = (
    Path(__file__).resolve().parents[2]
    / "labs"
    / "001-know-your-agent"
    / "static"
    / "architecture.svg"
)


def test_architecture_svg_is_valid_utf8():
    data = SVG_PATH.read_bytes()
    text = data.decode("utf-8")
    assert b"\xb7" not in data
    assert text.startswith("<?xml")


def test_architecture_svg_has_required_content():
    text = SVG_PATH.read_text(encoding="utf-8")
    assert "Panel A" in text
    assert "Runtime request path" in text
    assert "Panel B" in text
    assert "Inside the Trust Gateway" in text
    assert "marker-end=" in text
    assert 'id="arrow"' in text
    assert "Identity registry" in text
    assert "Delegated authority" in text
    assert "Policy rules" in text
    assert "Request context" in text
    assert "ALLOW" in text
    assert "CONFIRM" in text
    assert "STEP_UP" in text
    assert "DENY" in text
    assert "resubmit" in text
    assert "customer confirmation" in text
    assert "MFA" in text
    assert "POST /api/evaluate" in text


def test_architecture_url_and_type():
    response = client.get("/static/labs/001/architecture.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    body = response.content.decode("utf-8")
    assert "Panel A" in body
    assert "Panel B" in body
