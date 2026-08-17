"""PostHog analytics is off by default and never includes sensitive lab fields."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from from_my_desk.config import Settings, reset_settings_cache
from from_my_desk.main import app
from from_my_desk.telemetry import (
    content_security_policy,
    public_telemetry_config,
    telemetry_enabled_for_request,
)

REPO = Path(__file__).resolve().parents[2]
SITE_JS = REPO / "website" / "app" / "static" / "js" / "site.js"
LAB_JS = REPO / "labs" / "001-know-your-agent" / "static" / "lab.js"

SENSITIVE = (
    "principal_id",
    "agent_id",
    "account_id",
    "audit_id",
    "limit_price",
    "notional",
    "quantity",
    "ticker",
    "phx_",
    "identify(",
)

TEST_PUBLIC_TOKEN = "phc_test_public_client_token_not_a_secret"


@pytest.fixture
def telemetry_env_cleanup():
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_analytics_disabled_by_default(telemetry_env_cleanup):
    settings = Settings()
    assert settings.posthog_enabled is False
    assert settings.posthog_key == ""
    assert telemetry_enabled_for_request(settings, "from-my-desk.example") is False
    html = TestClient(app).get("/").text
    assert '"enabled": false' in html
    assert "array.js" not in html
    assert "us-assets.i.posthog.com" not in html
    assert TEST_PUBLIC_TOKEN not in html


def test_no_posthog_script_when_disabled(telemetry_env_cleanup):
    for path in ("/", "/labs", "/labs/know-your-agent"):
        html = TestClient(app).get(path).text
        assert "array.js" not in html
        assert "posthog.init" not in html
        assert '"enabled": false' in html


def test_no_posthog_script_on_localhost_even_when_configured(
    monkeypatch, telemetry_env_cleanup
):
    monkeypatch.setenv("POSTHOG_ENABLED", "true")
    monkeypatch.setenv("POSTHOG_KEY", TEST_PUBLIC_TOKEN)
    monkeypatch.setenv("POSTHOG_HOST", "https://us.i.posthog.com")
    reset_settings_cache()
    settings = Settings()
    assert telemetry_enabled_for_request(settings, "localhost") is False
    assert telemetry_enabled_for_request(settings, "127.0.0.1") is False
    assert telemetry_enabled_for_request(settings, "testserver") is False
    local = TestClient(app, base_url="http://127.0.0.1:8080")
    html = local.get("/").text
    assert '"enabled": false' in html
    assert "array.js" not in html
    csp = local.get("/").headers.get("content-security-policy", "")
    assert "posthog.com" not in csp
    assert "worker-src" not in csp
    pytest_client = TestClient(app)
    assert "array.js" not in pytest_client.get("/labs/know-your-agent").text
    tight = content_security_policy(settings, "127.0.0.1")
    assert "posthog.com" not in tight
    assert "worker-src" not in tight


def test_official_sdk_present_when_enabled_on_production_host(
    monkeypatch, telemetry_env_cleanup
):
    monkeypatch.setenv("POSTHOG_ENABLED", "true")
    monkeypatch.setenv("POSTHOG_KEY", TEST_PUBLIC_TOKEN)
    monkeypatch.setenv("POSTHOG_HOST", "https://us.i.posthog.com")
    reset_settings_cache()
    client = TestClient(app, base_url="https://from-my-desk.example")
    html = client.get("/").text
    assert '"enabled": true' in html
    assert TEST_PUBLIC_TOKEN in html
    assert '"sdk_src": "https://us-assets.i.posthog.com/static/array.js"' in html
    assert '<script src="https://us-assets.i.posthog.com/static/array.js"' not in html
    assert "/static/js/site.js" in html
    assert html.count("<script") == 2
    assert '"capture_pageview": false' in html
    assert '"capture_pageleave": true' in html
    assert '"autocapture": false' in html
    assert '"disable_session_recording": true' in html
    assert '"person_profiles": "identified_only"' in html
    assert '"persistence": "localStorage+cookie"' in html
    assert '"respect_dnt": true' in html
    assert "posthog.identify" not in html
    assert "posthog.init" not in html
    csp = client.get("/").headers.get("content-security-policy", "")
    assert "https://*.i.posthog.com" in csp
    assert "https://*.posthog.com" in csp
    assert "worker-src 'self' blob: data:" in csp
    assert "https://us.i.posthog.com" not in csp
    assert "https://us-assets.i.posthog.com" not in csp
    js = client.get("/static/js/site.js").text
    assert "installOfficialStub" in js
    assert "e.__SV" in js
    assert "/static/array.js" in js
    assert js.count("window.posthog.init(") == 1
    assert 'defaults: "2026-05-30"' in js
    assert "capture_pageview: false" in js
    assert "capture_pageleave: true" in js
    assert "autocapture: false" in js
    assert "disable_session_recording: true" in js
    assert "posthog.identify" not in js
    assert "capture_pageview: true" not in js
    assert re.search(r'capture\(\s*"\$pageview"', js)
    assert "loaded: function (posthog)" in js
    assert js.count('"$pageview"') == 1 or js.count("'$pageview'") + js.count('"$pageview"') == 1


def test_exactly_one_pageview_after_single_init():
    js = SITE_JS.read_text(encoding="utf-8")
    assert js.count("window.posthog.init(") == 1
    assert len(re.findall(r'capture\(\s*"\$pageview"', js)) == 1
    assert "__fromMyDeskPosthogReady" in js
    assert "__fromMyDeskPageviewSent" in js
    assert "loaded: function (posthog)" in js
    capture_block = re.search(
        r'capture\(\s*"\$pageview"\s*,\s*\{([^}]+)\}',
        js,
        re.DOTALL,
    )
    assert capture_block, "expected a $pageview capture payload"
    body = capture_block.group(1)
    assert "$current_url" in body
    assert "$pathname" in body
    assert "page_title" in body
    for needle in (
        "principal_id",
        "agent_id",
        "account_id",
        "audit_id",
        "limit_price",
        "notional",
        "ticker",
        "quantity",
    ):
        assert needle not in body
    assert "href:" not in body
    assert "window.location.href" in body
    # $pageview is not sent through track(), which would strip these fields.
    assert "track(" not in body


LOADER_HARNESS = r"""
const fs = require("fs");
const vm = require("vm");
const siteJs = fs.readFileSync(process.argv[2], "utf8");
const cfg = JSON.parse(process.argv[3]);

function pickOptions(opts) {
  opts = opts || {};
  return {
    api_host: opts.api_host,
    defaults: opts.defaults,
    capture_pageview: opts.capture_pageview,
    capture_pageleave: opts.capture_pageleave,
    autocapture: opts.autocapture,
    disable_session_recording: opts.disable_session_recording,
    person_profiles: opts.person_profiles,
    persistence: opts.persistence,
    respect_dnt: opts.respect_dnt,
    has_loaded: typeof opts.loaded === "function"
  };
}

function boot(window, scripts) {
  const document = {
    readyState: "complete",
    title: "Know Your Agent",
    getElementById: function (id) {
      if (id === "telemetry-config") {
        return { textContent: JSON.stringify(cfg) };
      }
      return null;
    },
    createElement: function () {
      return { type: "", crossOrigin: "", async: false, src: "" };
    },
    getElementsByTagName: function () {
      return [{
        parentNode: {
          insertBefore: function (node) {
            scripts.push(node.src);
          }
        }
      }];
    },
    addEventListener: function () {}
  };
  window.document = document;
  const context = { window: window, document: document, console: console };
  vm.createContext(context);
  vm.runInContext(siteJs, context);
}

const scripts = [];
const captures = [];
const windowObj = {
  location: {
    href: "https://from-my-desk.example/labs/know-your-agent",
    pathname: "/labs/know-your-agent"
  }
};
boot(windowObj, scripts);
const queued = (windowObj.posthog && windowObj.posthog._i) || [];
const inits = queued.map(function (entry) {
  const opts = entry[1] || {};
  const client = {
    capture: function (name, props) {
      captures.push({ name: name, props: props });
    }
  };
  if (typeof opts.loaded === "function") {
    opts.loaded(client);
    opts.loaded(client);
  }
  return { key: entry[0], options: pickOptions(opts) };
});
boot(windowObj, scripts);
const queuedAfterReload = (windowObj.posthog && windowObj.posthog._i) || [];
process.stdout.write(JSON.stringify({
  scripts: scripts,
  captures: captures,
  inits: inits,
  queuedAfterReload: queuedAfterReload.length,
  pageviewSent: Boolean(windowObj.__fromMyDeskPageviewSent),
  ready: Boolean(windowObj.__fromMyDeskPosthogReady)
}));
"""


def _run_loader_harness(config: dict) -> dict:
    import json
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    node = shutil.which("node")
    if not node:
        pytest.skip("node is required to execute the PostHog loader harness")
    with tempfile.TemporaryDirectory() as tmp:
        harness = Path(tmp) / "posthog_loader_harness.js"
        harness.write_text(LOADER_HARNESS, encoding="utf-8")
        result = subprocess.run(
            [node, str(harness), str(SITE_JS), json.dumps(config)],
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        pytest.fail(result.stderr or result.stdout or "loader harness failed")
    return json.loads(result.stdout)


def test_loader_captures_exactly_one_pageview_and_does_not_reinit():
    cfg = {
        "enabled": True,
        "key": TEST_PUBLIC_TOKEN,
        "host": "https://us.i.posthog.com",
        "capture_pageview": False,
        "capture_pageleave": True,
        "autocapture": False,
        "disable_session_recording": True,
    }
    report = _run_loader_harness(cfg)
    assert len(report["inits"]) == 1
    options = report["inits"][0]["options"]
    assert report["inits"][0]["key"] == TEST_PUBLIC_TOKEN
    assert options["api_host"] == "https://us.i.posthog.com"
    assert options["defaults"] == "2026-05-30"
    assert options["capture_pageview"] is False
    assert options["capture_pageleave"] is True
    assert options["autocapture"] is False
    assert options["disable_session_recording"] is True
    assert options["has_loaded"] is True
    assert report["queuedAfterReload"] == 1
    assert len(report["scripts"]) == 1
    assert report["scripts"][0].endswith("/static/array.js")
    assert "us-assets.i.posthog.com" in report["scripts"][0]
    pageviews = [item for item in report["captures"] if item["name"] == "$pageview"]
    assert len(pageviews) == 1
    props = pageviews[0]["props"]
    assert set(props) == {"$current_url", "$pathname", "page_title"}
    assert props["$current_url"] == "https://from-my-desk.example/labs/know-your-agent"
    assert props["$pathname"] == "/labs/know-your-agent"
    assert props["page_title"] == "Know Your Agent"
    assert report["ready"] is True
    assert report["pageviewSent"] is True


def test_loader_stays_idle_when_telemetry_disabled():
    report = _run_loader_harness({"enabled": False})
    assert report["inits"] == []
    assert report["scripts"] == []
    assert report["captures"] == []
    assert report["queuedAfterReload"] == 0
    assert report["ready"] is False
    assert report["pageviewSent"] is False


def test_config_helper_omits_key_when_disabled(telemetry_env_cleanup):
    cfg = public_telemetry_config(Settings(), "from-my-desk.example")
    assert cfg == {"enabled": False}


def test_js_never_includes_sensitive_telemetry_fields():
    site = SITE_JS.read_text(encoding="utf-8")
    lab = LAB_JS.read_text(encoding="utf-8")
    assert "lab_preset_selected" in lab
    assert "policy_evaluation_completed" in lab
    assert "outbound_link_clicked" in site
    assert "preset_category" in lab
    assert "reason_category" in lab
    combined = site + "\n" + lab
    assert "posthog.identify" not in combined
    payloads = re.findall(
        r'\btrack\s*\(\s*"([^"]+)"\s*,\s*\{([^}]*)\}',
        combined,
        re.DOTALL,
    )
    names = {name for name, _body in payloads}
    assert "lab_preset_selected" in names
    assert "policy_evaluation_completed" in names
    assert "outbound_link_clicked" in names
    for name, body in payloads:
        for needle in (
            "principal_id",
            "agent_id",
            "account_id",
            "audit_id",
            "limit_price",
            "notional",
            "ticker",
            "quantity",
            "href",
        ):
            assert needle not in body


def test_pages_and_policy_unchanged_with_default_analytics(telemetry_env_cleanup):
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "Perspectives shaped by experience" in client.get("/").text
    assert client.get("/labs").status_code == 200
    lab = client.get("/labs/know-your-agent")
    assert lab.status_code == 200
    assert "/static/css/styles.css" in lab.text
    css = client.get("/static/css/styles.css")
    assert css.status_code == 200
    assert "--navy:" in css.text
    payload = {
        "principal_id": "principal-demo-001",
        "agent_id": "kya-agent-001",
        "action": "propose_paper_order",
        "order": {
            "ticker": "BRICK",
            "side": "buy",
            "quantity": 100,
            "limit_price": "40.00",
            "account_id": "paper-desk-alpha",
        },
        "authorization_context": {"customer_confirmed": False, "mfa_verified": False},
    }
    allow = client.post("/api/evaluate", json=payload)
    assert allow.json()["decision"] == "allow"
    assert allow.json()["execution"] == "not_performed"
    payload["order"]["quantity"] = 200
    assert client.post("/api/evaluate", json=payload).json()["decision"] == "confirm"
    payload["order"]["quantity"] = 300
    assert client.post("/api/evaluate", json=payload).json()["decision"] == "step_up"
    payload["order"]["quantity"] = 450
    assert client.post("/api/evaluate", json=payload).json()["decision"] == "deny"


def test_source_files_have_no_personal_api_key_or_hardcoded_token():
    for path in (
        SITE_JS,
        LAB_JS,
        REPO / "website" / "app" / "telemetry.py",
        REPO / "website" / "app" / "config.py",
        REPO / ".env.example",
        REPO / "Dockerfile",
        REPO / "docker-compose.yml",
    ):
            text = path.read_text(encoding="utf-8")
            assert "phx_" not in text
            assert not re.search(r"phc_[A-Za-z0-9]", text)
            if "Personal API" in text:
                assert "never" in text.lower() or "not a" in text.lower()
