from fastapi.testclient import TestClient

from from_my_desk.main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "From My Desk" in response.text
    assert "Perspectives shaped by experience" in response.text
    assert "leadership" in response.text.lower()
    assert 'href="/static/css/styles.css"' in response.text
    assert "/static/brand/from-my-desk-logo.webp" in response.text


def test_labs_page():
    response = client.get("/labs")
    assert response.status_code == 200
    assert "Know Your Agent" in response.text
    assert "Desk Index" in response.text


def test_lab_page_controls_and_assets():
    response = client.get("/labs/know-your-agent")
    assert response.status_code == 200
    assert "Identity Is Only the Beginning" in response.text
    assert 'id="evaluate-form"' in response.text
    assert "<label>Principal" in response.text
    assert 'id="principal_id"' in response.text
    assert 'id="customer_confirmed"' in response.text
    assert "How it works" in response.text
    assert "/static/labs/001/architecture.svg" in response.text
    assert "/static/labs/001/know-your-agent-trust-workflow.gif" in response.text
    assert 'data-preset="allow-4k"' in response.text
    assert "not investment advice" in response.text.lower()
    css = client.get("/static/css/styles.css")
    js = client.get("/static/labs/001/lab.js")
    svg = client.get("/static/labs/001/architecture.svg")
    gif = client.get("/static/labs/001/know-your-agent-trust-workflow.gif")
    assert css.status_code == 200
    assert js.status_code == 200
    assert svg.status_code == 200
    assert gif.status_code == 200
    assert "image/svg+xml" in svg.headers["content-type"]
    assert "image/gif" in gif.headers["content-type"]
    assert '"enabled": false' in response.text


def test_presets_in_javascript_are_consistent():
    js = client.get("/static/labs/001/lab.js").text
    assert "allow-4k" in js
    assert "quantity: 100" in js
    assert "unknown-bot" in js
    assert "kya-agent-revoked" in js
    assert "MAPLE" in js
