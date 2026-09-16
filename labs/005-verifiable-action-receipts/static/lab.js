(function () {
  "use strict";

  var LAB_ID = "005";
  var LAB_SLUG = "verifiable-action-receipts";
  var selectedPreset = "";
  var lastResponse = null;

  function $(id) {
    return document.getElementById(id);
  }

  function track(eventName, props) {
    if (window.fromMyDeskTrack) {
      window.fromMyDeskTrack(eventName, props || {});
    }
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  var LABELS = {
    revoke_suspicious_session: "Revoke suspicious session",
    temporarily_suspend_access: "Temporarily suspend access",
    secure_the_account: "Secure the account",
    preserve_evidence: "Preserve evidence",
    require_stronger_authentication: "Require stronger authentication",
    permanently_delete_account: "Permanently delete account",
    revoke_sessions: "Revoke sessions",
    "cq-session-control": "Cedar Quill session control",
    "cq-access-control": "Cedar Quill access control",
    "cq-evidence-vault": "Cedar Quill evidence vault",
    "cq-delegation-register": "Cedar Quill delegation register",
    "cq-soc-response-policy": "Cedar Quill SOC response policy",
    revoke_session: "Revoke session",
    temporary_suspend: "Temporary suspend",
    preserve_case_bundle: "Preserve case bundle",
    "auth.allow": "Authorization allowed",
    "auth.confirm": "Authorization required confirmation",
    "judgment.proceed": "Judgment: proceed",
    "judgment.clarify": "Judgment: clarify",
    "judgment.escalate": "Judgment: escalate",
    "judgment.proceed_after_clarify": "Judgment: proceed after clarify",
    "human.approval_recorded": "Human approval recorded",
    "tool.session_revoke_simulated": "Tool: session revoke simulated",
    "request.ambiguous_goal": "Request: ambiguous goal",
    "evidence.conflicting": "Evidence: conflicting",
    "impact.high": "Impact: high",
    "demo.integrity_failure": "Demo: integrity failure",
    "demo.chain_break": "Demo: chain break",
    "evid-login-geo-mismatch": "Login geography mismatch",
    "evid-device-fingerprint-new": "New device fingerprint",
    "evid-threat-intel-ip": "Threat-intel IP match",
    "evid-unusual-file-access": "Unusual file access",
    "evid-active-customer-meeting": "Active customer meeting",
    "evid-operator-chat-turn-1": "Operator chat turn 1",
    "evid-operator-chat-turn-2": "Operator chat turn 2",
    "evid-travel-calendar-possible": "Possible travel on calendar",
    "evid-customer-meeting-live": "Live customer meeting",
    "evid-case-opened": "Investigation case opened",
    observed_outcome: "Observed outcome",
    authorization_outcome: "Authorization outcome",
    none: "None",
    clarification: "Clarification",
    approval: "Approval",
    modification: "Modification",
    rejection: "Rejection",
    escalation: "Escalation",
    simulated: "Simulated",
    not_performed: "Not performed"
  };

  function humanLabel(value) {
    if (value == null || value === "") return "—";
    var key = String(value);
    if (Object.prototype.hasOwnProperty.call(LABELS, key)) {
      return LABELS[key];
    }
    if (key.indexOf("_") !== -1) {
      return key
        .split("_")
        .map(function (part) {
          return part ? part.charAt(0).toUpperCase() + part.slice(1) : part;
        })
        .join(" ");
    }
    return key;
  }

  function ensureSelectOption(el, value, label) {
    if (!el || value == null || value === "") return;
    var exists = Array.prototype.some.call(el.options, function (opt) {
      return opt.value === String(value);
    });
    if (!exists) {
      var option = document.createElement("option");
      option.value = String(value);
      option.textContent = label || humanLabel(value);
      el.appendChild(option);
    }
  }

  function setValue(id, value) {
    var el = $(id);
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = Boolean(value);
      return;
    }
    if (el.tagName === "SELECT" && el.multiple) {
      var wanted = Array.isArray(value)
        ? value.map(String)
        : String(value || "")
            .split(/\n|,/)
            .map(function (item) {
              return item.trim();
            })
            .filter(Boolean);
      wanted.forEach(function (item) {
        ensureSelectOption(el, item);
      });
      Array.prototype.forEach.call(el.options, function (opt) {
        opt.selected = wanted.indexOf(opt.value) !== -1;
      });
      return;
    }
    if (el.tagName === "SELECT") {
      ensureSelectOption(el, value);
    }
    el.value = value == null ? "" : String(value);
  }

  function getValue(id) {
    var el = $(id);
    if (!el) return "";
    if (el.type === "checkbox") return el.checked;
    if (el.tagName === "SELECT" && el.multiple) {
      return Array.prototype.filter
        .call(el.options, function (opt) {
          return opt.selected;
        })
        .map(function (opt) {
          return opt.value;
        });
    }
    return el.value;
  }

  function readForm() {
    var evidence = getValue("evidence_references");
    var reasons = getValue("reason_codes");
    return {
      request_id: getValue("request_id"),
      correlation_id: getValue("correlation_id"),
      agent_identity: getValue("agent_identity"),
      principal_identity: getValue("principal_identity"),
      target_resource: getValue("target_resource"),
      requested_action: getValue("requested_action"),
      delegated_capability: getValue("delegated_capability"),
      authority_source: getValue("authority_source"),
      policy_id: getValue("policy_id"),
      policy_version: getValue("policy_version"),
      authorization_outcome: getValue("authorization_outcome"),
      execution_judgment: getValue("execution_judgment"),
      evidence_references: Array.isArray(evidence) ? evidence : [],
      evidence_summary: getValue("evidence_summary"),
      human_involvement: getValue("human_involvement"),
      approval_reference: getValue("approval_reference"),
      original_request: getValue("original_request"),
      clarification_note: getValue("clarification_note"),
      simulated_tool: getValue("simulated_tool"),
      simulated_tool_action: getValue("simulated_tool_action"),
      observed_outcome: getValue("observed_outcome"),
      reason_codes: Array.isArray(reasons) ? reasons : [],
      explanation: getValue("explanation"),
      previous_receipt_hash: getValue("previous_receipt_hash"),
      force_tamper_field: getValue("force_tamper_field") || null,
      force_tamper_value: getValue("force_tamper_value") || null,
      force_broken_chain: Boolean(getValue("force_broken_chain")),
      preset_id: selectedPreset || null
    };
  }

  function applyRequest(request) {
    if (!request) return;
    setValue("request_id", request.request_id);
    setValue("correlation_id", request.correlation_id);
    setValue("agent_identity", request.agent_identity);
    setValue("principal_identity", request.principal_identity);
    setValue("target_resource", request.target_resource);
    setValue("requested_action", request.requested_action);
    setValue("delegated_capability", request.delegated_capability);
    setValue("authority_source", request.authority_source || "cq-delegation-register");
    setValue("policy_id", request.policy_id || "cq-soc-response-policy");
    setValue("policy_version", request.policy_version || "lab005-receipt-v1");
    setValue("authorization_outcome", request.authorization_outcome);
    setValue("execution_judgment", request.execution_judgment);
    setValue("evidence_references", request.evidence_references || []);
    setValue("evidence_summary", request.evidence_summary || "");
    setValue("human_involvement", request.human_involvement || "none");
    setValue("approval_reference", request.approval_reference || "");
    setValue("original_request", request.original_request || "");
    setValue("clarification_note", request.clarification_note || "");
    setValue("simulated_tool", request.simulated_tool || "");
    setValue("simulated_tool_action", request.simulated_tool_action || "");
    setValue("observed_outcome", request.observed_outcome || "");
    setValue("reason_codes", request.reason_codes || []);
    setValue("explanation", request.explanation || "");
    setValue("previous_receipt_hash", request.previous_receipt_hash || "");
    setValue("force_tamper_field", request.force_tamper_field || "");
    setValue("force_tamper_value", request.force_tamper_value || "");
    setValue("force_broken_chain", Boolean(request.force_broken_chain));
  }

  function integrityClass(status) {
    return "lab005-integrity-" + String(status || "verified");
  }

  function integrityLabel(status) {
    var value = String(status || "").toUpperCase();
    if (value === "CHAIN_BROKEN") return "CHAIN BROKEN";
    return value || "UNKNOWN";
  }

  function listHtml(items) {
    if (!items || !items.length) return "<p class=\"hint\">None recorded.</p>";
    return (
      "<ul>" +
      items
        .map(function (item) {
          return "<li>" + escapeHtml(humanLabel(item)) + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  function receiptSection(title, rows) {
    var body = rows
      .map(function (row) {
        var display = row[2] ? humanLabel(row[1]) : row[1];
        var mono = row[3] ? " class=\"lab005-mono\"" : "";
        return (
          "<p" +
          mono +
          "><strong>" +
          escapeHtml(row[0]) +
          ":</strong> " +
          escapeHtml(display) +
          "</p>"
        );
      })
      .join("");
    return "<h3>" + escapeHtml(title) + "</h3>" + body;
  }

  function renderReceipt(receipt, verification, options) {
    options = options || {};
    var prefix = options.prefix || "";
    var html =
      '<p class="decision ' +
      integrityClass(verification.integrity_status) +
      '"><span class="decision-label">' +
      escapeHtml(integrityLabel(verification.integrity_status)) +
      "</span></p>" +
      "<p class=\"result-reason\">" +
      escapeHtml(verification.explanation || "") +
      "</p>";

    if (verification.failures && verification.failures.length) {
      html +=
        "<h3>Verification failures</h3>" + listHtml(verification.failures);
    }

    html += receiptSection("Request", [
      ["Request ID", receipt.request_id, false, true],
      ["Correlation ID", receipt.correlation_id, false, true],
      ["Requested action", receipt.requested_action, true],
      ["Target resource", receipt.target_resource],
      ["Original request", receipt.original_request || "—"],
      ["Clarification note", receipt.clarification_note || "—"]
    ]);

    html += receiptSection("Identity and authority", [
      ["Agent", receipt.agent_identity],
      ["Principal", receipt.principal_identity],
      ["Delegated capability", receipt.delegated_capability, true],
      ["Authority source", receipt.authority_source, true],
      [
        "Policy",
        humanLabel(receipt.policy_id) + " @ " + receipt.policy_version
      ]
    ]);

    html += receiptSection("Decision and evidence", [
      ["Authorization outcome", String(receipt.authorization_outcome).toUpperCase()],
      ["Execution judgment", String(receipt.execution_judgment).toUpperCase()],
      ["Evidence summary", receipt.evidence_summary || "—"]
    ]);
    html += "<h3>Evidence references</h3>" + listHtml(receipt.evidence_references);
    html += "<h3>Reason codes</h3>" + listHtml(receipt.reason_codes);

    html += receiptSection("Human involvement", [
      ["Involvement", receipt.human_involvement, true],
      ["Approval reference", receipt.approval_reference || "—"]
    ]);

    html += receiptSection("Execution and outcome", [
      ["Simulated tool", receipt.simulated_tool || "—", true],
      ["Simulated tool action", receipt.simulated_tool_action || "—", true],
      ["Execution status", receipt.execution_status, true],
      ["Observed outcome", receipt.observed_outcome || "—"],
      ["Explanation", receipt.explanation || "—"]
    ]);

    html += receiptSection("Integrity", [
      ["Receipt ID", receipt.receipt_id, false, true],
      ["Created at", receipt.created_at],
      ["Previous receipt hash", receipt.previous_receipt_hash || "—", false, true],
      ["Receipt hash", receipt.receipt_hash, false, true],
      ["Integrity status", integrityLabel(receipt.integrity_status)],
      ["Content match", verification.content_match ? "true" : "false"],
      ["Chain match", verification.chain_match ? "true" : "false"]
    ]);

    html +=
      "<details class=\"lab005-raw\"><summary>Raw JSON" +
      (prefix ? " (" + escapeHtml(prefix) + ")" : "") +
      "</summary><pre class=\"lab005-mono\">" +
      escapeHtml(JSON.stringify(receipt, null, 2)) +
      "</pre></details>";

    return html;
  }

  function renderResult(data) {
    var root = $("result");
    if (!root) return;
    lastResponse = data;
    var html =
      "<p><strong>Real execution:</strong> not_performed</p>" +
      renderReceipt(data.receipt, data.verification, { prefix: "primary" });

    if (data.follow_up_receipt && data.follow_up_verification) {
      html +=
        "<h2 class=\"lab005-followup-heading\">Follow-up receipt after clarification</h2>" +
        renderReceipt(data.follow_up_receipt, data.follow_up_verification, {
          prefix: "follow-up"
        });
    }

    if (data.prior_receipt && data.prior_verification) {
      html +=
        "<h2 class=\"lab005-followup-heading\">Prior receipt in chain</h2>" +
        renderReceipt(data.prior_receipt, data.prior_verification, {
          prefix: "prior"
        });
    }

    root.innerHTML = html;
    root.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function selectPresetButton(presetId) {
    selectedPreset = presetId;
    document.querySelectorAll(".preset-card").forEach(function (btn) {
      var on = btn.getAttribute("data-preset") === presetId;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      var badge = btn.querySelector(".preset-selected-label");
      if (badge) badge.hidden = !on;
    });
  }

  function loadPreset(presetId) {
    selectPresetButton(presetId);
    track("lab_preset_selected", {
      lab_id: LAB_ID,
      lab_slug: LAB_SLUG,
      preset_id: presetId
    });
    fetch("/api/labs/005/presets/" + encodeURIComponent(presetId), {
      headers: { Accept: "application/json" }
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (payload) {
        if (!payload.ok) return;
        applyRequest(payload.body.request || {});
      })
      .catch(function () {
        return;
      });
  }

  function generate(event) {
    if (event) event.preventDefault();
    var btn = $("generate-btn");
    if (btn) btn.disabled = true;

    var url = selectedPreset
      ? "/api/labs/005/evaluate-preset/" + encodeURIComponent(selectedPreset)
      : "/api/labs/005/generate";
    var init = selectedPreset
      ? {
          method: "POST",
          headers: { Accept: "application/json" }
        }
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json"
          },
          body: JSON.stringify(readForm())
        };

    fetch(url, init)
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (payload) {
        if (btn) btn.disabled = false;
        if (!payload.ok) {
          var root = $("result");
          if (root) {
            root.innerHTML =
              '<p class="decision lab005-integrity-tampered"><span class="decision-label">ERROR</span></p>' +
              "<p>" +
              escapeHtml(
                (payload.body && payload.body.detail && payload.body.detail.reason) ||
                  (payload.body && payload.body.reason) ||
                  "Receipt generation could not be completed."
              ) +
              "</p>";
          }
          return;
        }
        renderResult(payload.body);
        track("policy_evaluation_completed", {
          lab_id: LAB_ID,
          lab_slug: LAB_SLUG,
          preset_id: selectedPreset || "",
          decision: payload.body.verification.integrity_status
        });
      })
      .catch(function () {
        if (btn) btn.disabled = false;
        var root = $("result");
        if (root) {
          root.innerHTML =
            '<p class="decision lab005-integrity-tampered"><span class="decision-label">ERROR</span></p>' +
            "<p>Network error.</p>";
        }
      });
  }

  function init() {
    track("lab_opened", { lab_id: LAB_ID, lab_slug: LAB_SLUG });

    document.querySelectorAll(".preset-card").forEach(function (btn) {
      btn.addEventListener("click", function () {
        loadPreset(btn.getAttribute("data-preset"));
      });
    });

    var form = $("lab005-form");
    if (form) form.addEventListener("submit", generate);

    var newsletter = document.querySelector("[data-lab005-newsletter]");
    if (newsletter) {
      newsletter.addEventListener("click", function () {
        track("lab_005_newsletter_clicked", { lab_id: LAB_ID, lab_slug: LAB_SLUG });
      });
    }

    document
      .querySelectorAll('img[data-architecture-type="lab005-receipt-chain"]')
      .forEach(function (arch) {
        arch.addEventListener("click", function () {
          track("architecture_viewed", {
            lab_id: LAB_ID,
            architecture_type: "lab005-receipt-chain"
          });
        });
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
