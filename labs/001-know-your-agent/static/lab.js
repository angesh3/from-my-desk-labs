(function () {
  "use strict";

  var PRESETS = {
    "allow-4k": {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    "confirm-8k": {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 200,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    "step-up-12k": {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 300,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    "deny-18k": {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 450,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    "unknown-agent": {
      principal_id: "principal-demo-001",
      agent_id: "unknown-bot",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    revoked: {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-revoked",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    expired: {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-expired",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    "wrong-principal": {
      principal_id: "principal-other-009",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    restricted: {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "MAPLE",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    },
    unassigned: {
      principal_id: "principal-demo-001",
      agent_id: "kya-agent-001",
      account_id: "paper-desk-alpha",
      ticker: "BRICK",
      side: "buy",
      quantity: 100,
      limit_price: "40.00",
      customer_confirmed: false,
      mfa_verified: false
    }
  };

  function $(id) {
    return document.getElementById(id);
  }

  function track(eventName, properties) {
    if (window.FromMyDesk && typeof window.FromMyDesk.track === "function") {
      window.FromMyDesk.track(eventName, properties);
    }
  }

  function markSelected(name) {
    document.querySelectorAll("[data-preset]").forEach(function (button) {
      var selected = button.getAttribute("data-preset") === name;
      button.classList.toggle("is-selected", selected);
      if (selected) {
        button.setAttribute("aria-pressed", "true");
      } else {
        button.removeAttribute("aria-pressed");
      }
    });
  }

  function applyPreset(name) {
    var preset = PRESETS[name];
    if (!preset) {
      return;
    }
    $("principal_id").value = preset.principal_id;
    $("agent_id").value = preset.agent_id;
    $("account_id").value = preset.account_id;
    $("ticker").value = preset.ticker;
    $("side").value = preset.side;
    $("quantity").value = String(preset.quantity);
    $("limit_price").value = preset.limit_price;
    $("customer_confirmed").checked = preset.customer_confirmed;
    $("mfa_verified").checked = preset.mfa_verified;
    markSelected(name);
    track("scenario_selected", { preset_name: name });
  }

  function readForm() {
    return {
      principal_id: $("principal_id").value,
      agent_id: $("agent_id").value,
      action: "propose_paper_order",
      order: {
        ticker: $("ticker").value,
        side: $("side").value,
        quantity: Number($("quantity").value),
        limit_price: $("limit_price").value,
        account_id: $("account_id").value
      },
      authorization_context: {
        customer_confirmed: $("customer_confirmed").checked,
        mfa_verified: $("mfa_verified").checked
      }
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderResult(requestBody, responseBody, httpStatus) {
    var root = $("result");
    if (!responseBody || !responseBody.decision) {
      root.innerHTML =
        "<p>The service returned an error (" +
        escapeHtml(httpStatus) +
        "). No order was executed.</p><pre>" +
        escapeHtml(JSON.stringify(responseBody, null, 2)) +
        "</pre>";
      return;
    }
    var decision = responseBody.decision;
    var checks = (responseBody.checks || [])
      .map(function (item) {
        return (
          "<li><span class=\"" +
          escapeHtml(item.result) +
          "\">" +
          escapeHtml(item.result.toUpperCase()) +
          "</span> " +
          escapeHtml(item.name) +
          " — " +
          escapeHtml(item.explanation) +
          "</li>"
        );
      })
      .join("");
    root.innerHTML =
      "<p><span class=\"decision-label\">Decision:</span> <span class=\"decision decision-" +
      escapeHtml(decision) +
      "\" role=\"status\">" +
      escapeHtml(decision.toUpperCase()) +
      "</span></p>" +
      "<p>" +
      escapeHtml(responseBody.reason) +
      "</p>" +
      "<p>Required next action: <strong>" +
      escapeHtml(responseBody.required_action || "none") +
      "</strong></p>" +
      "<p>Policy ID: <code class=\"wrap-id\">" +
      escapeHtml(responseBody.policy_id) +
      "</code> · Notional: " +
      escapeHtml(responseBody.notional || "n/a") +
      "</p>" +
      "<p class=\"execution-note\">Execution: <strong>not performed</strong>.</p>" +
      "<p class=\"audit-meta\">Audit ID: <code class=\"wrap-id\">" +
      escapeHtml(responseBody.audit_id) +
      "</code></p>" +
      "<details id=\"checks-list\"><summary>Policy checks</summary><ul class=\"checks\">" +
      checks +
      "</ul></details>" +
      "<details id=\"request-json\"><summary>Request JSON</summary><pre>" +
      escapeHtml(JSON.stringify(requestBody, null, 2)) +
      "</pre></details>" +
      "<details id=\"response-json\"><summary>Response JSON</summary><pre>" +
      escapeHtml(JSON.stringify(responseBody, null, 2)) +
      "</pre></details>";
  }

  function bandFromNotional(raw) {
    var amount = Number(raw);
    if (!(amount >= 0)) {
      return "unknown";
    }
    if (amount <= 5000) {
      return "0_to_5k";
    }
    if (amount <= 10000) {
      return "5k_to_10k";
    }
    if (amount <= 15000) {
      return "10k_to_15k";
    }
    return "above_15k";
  }

  async function submitEvaluation(event) {
    if (event) {
      event.preventDefault();
    }
    var body = readForm();
    track("evaluation_submitted", { amount_band: bandFromNotional(Number(body.order.quantity) * Number(body.order.limit_price)) });
    var started = Date.now();
    try {
      var response = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      var payload = await response.json();
      renderResult(body, payload, response.status);
      if (payload && payload.decision) {
        track("decision_returned", {
          decision: payload.decision,
          reason_category: payload.reason_code === "ok" ? payload.decision : "deny_or_challenge",
          amount_band: bandFromNotional(payload.notional),
          response_time_bucket: Date.now() - started < 200 ? "under_200ms" : "200ms_plus"
        });
      } else {
        track("evaluation_failed", { response_time_bucket: "n/a" });
      }
    } catch (err) {
      renderResult(body, { reason: "The evaluation request failed in the browser." }, 0);
      track("evaluation_failed", { response_time_bucket: "n/a" });
    }
  }

  function init() {
    var path = window.location.pathname;
    if (path === "/labs/know-your-agent") {
      track("lab_opened", { page_path: path });
    }

    document.querySelectorAll("[data-preset]").forEach(function (button) {
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () {
        applyPreset(button.getAttribute("data-preset"));
      });
    });

    var form = $("evaluate-form");
    if (form) {
      form.addEventListener("submit", submitEvaluation);
    }

    var arch = document.getElementById("architecture");
    if (arch && "IntersectionObserver" in window) {
      var seen = false;
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!seen && entry.isIntersecting) {
            seen = true;
            track("architecture_viewed", { page_path: path });
          }
        });
      });
      observer.observe(arch);
    }

    document.addEventListener("toggle", function (event) {
      var target = event.target;
      if (!(target && target.id)) {
        return;
      }
      if (target.id === "request-json" || target.id === "response-json") {
        if (target.open) {
          track("json_expanded", { page_path: path });
        }
      }
      if (target.id === "checks-list" && target.open) {
        track("checks_expanded", { page_path: path });
      }
    }, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
