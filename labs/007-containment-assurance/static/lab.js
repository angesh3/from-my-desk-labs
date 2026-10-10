(function () {
  "use strict";

  var LAB_ID = "007";
  var selectedPreset = "";
  var lastResponse = null;
  var CHECK_IDS = [
    "primary_runtime_stopped",
    "active_sessions_revoked",
    "delegated_credentials_revoked",
    "tool_access_disabled",
    "queued_actions_cancelled",
    "scheduled_work_cancelled",
    "child_agents_stopped",
    "network_egress_blocked",
    "alternate_network_paths_checked",
    "persistent_state_quarantined",
    "restart_recovery_disabled",
    "telemetry_coverage_complete",
    "evidence_freshness_acceptable",
    "evidence_source_independence",
    "post_containment_activity_absent"
  ];

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
    CONFIRMED: "Confirmed",
    PARTIAL: "Partial",
    UNVERIFIED: "Unverified",
    FAILED: "Failed",
    RESTRICT: "Restrict",
    ISOLATE: "Isolate",
    TERMINATE: "Terminate",
    not_performed: "Not performed",
    pass: "Pass",
    fail: "Fail",
    missing: "Missing",
    fresh: "Fresh",
    stale: "Stale",
    unknown: "Unknown",
    independent_control_plane: "Independent control plane",
    agent_self_report: "Agent self-report",
    partial_telemetry: "Partial telemetry",
    none: "None",
    primary_runtime_stopped: "Primary runtime stopped",
    active_sessions_revoked: "Active sessions revoked",
    delegated_credentials_revoked: "Delegated credentials revoked",
    tool_access_disabled: "Tool access disabled",
    queued_actions_cancelled: "Queued actions cancelled",
    scheduled_work_cancelled: "Scheduled work cancelled",
    child_agents_stopped: "Child agents stopped",
    network_egress_blocked: "Network egress blocked",
    alternate_network_paths_checked: "Alternate network paths checked",
    persistent_state_quarantined: "Persistent state quarantined",
    restart_recovery_disabled: "Restart/recovery disabled",
    telemetry_coverage_complete: "Telemetry coverage complete",
    evidence_freshness_acceptable: "Evidence freshness acceptable",
    evidence_source_independence: "Evidence source independence",
    post_containment_activity_absent: "Post-containment activity absent"
  };

  function humanLabel(value) {
    if (value == null || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    var key = String(value);
    if (Object.prototype.hasOwnProperty.call(LABELS, key)) return LABELS[key];
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

  function setValue(id, value) {
    var el = $(id);
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = Boolean(value);
      return;
    }
    if (el.tagName === "TEXTAREA") {
      el.value = Array.isArray(value) ? value.join("\n") : String(value == null ? "" : value);
      return;
    }
    el.value = value == null ? "" : String(value);
  }

  function markSelected(presetId) {
    selectedPreset = presetId || "";
    document.querySelectorAll(".preset-card[data-preset]").forEach(function (card) {
      var match = card.getAttribute("data-preset") === selectedPreset;
      card.classList.toggle("is-selected", match);
      card.setAttribute("aria-pressed", match ? "true" : "false");
      var label = card.querySelector(".preset-selected-label");
      if (label) label.hidden = !match;
    });
  }

  function fillChecks(checks) {
    var byId = {};
    (checks || []).forEach(function (c) {
      byId[c.check_id] = c;
    });
    CHECK_IDS.forEach(function (cid) {
      var c = byId[cid] || {};
      setValue("check_" + cid + "_observed", c.observed_state || "");
      setValue("check_" + cid + "_expected", c.expected_state || "");
      setValue("check_" + cid + "_evidence", c.evidence_reference || "");
      setValue("check_" + cid + "_freshness", c.evidence_freshness || "unknown");
      setValue("check_" + cid + "_source", c.evidence_source || "none");
    });
  }

  function fillFromRequest(request, presetId) {
    if (!request) return;
    setValue("request_id", request.request_id);
    setValue("correlation_id", request.correlation_id);
    setValue("agent_id", request.agent_id);
    setValue("principal_id", request.principal_id);
    setValue("attempted_enforcement", request.attempted_enforcement);
    setValue("evaluated_at", request.evaluated_at);
    setValue("evidence_window_minutes", request.evidence_window_minutes);
    setValue("post_containment_activity", request.post_containment_activity);
    setValue("containment_regression_detected", request.containment_regression_detected);
    setValue("agent_self_report_stopped", request.agent_self_report_stopped);
    fillChecks(request.checks);
    markSelected(presetId);
  }

  function collectChecks() {
    return CHECK_IDS.map(function (cid) {
      return {
        check_id: cid,
        expected_state: ($("check_" + cid + "_expected") || {}).value || "required",
        observed_state: ($("check_" + cid + "_observed") || {}).value || "unknown",
        evidence_reference: ($("check_" + cid + "_evidence") || {}).value || null,
        evidence_freshness: ($("check_" + cid + "_freshness") || {}).value || "unknown",
        evidence_source: ($("check_" + cid + "_source") || {}).value || "none"
      };
    });
  }

  function collectPayload() {
    var activity = String(($("post_containment_activity") || {}).value || "")
      .split(/\n/)
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
    return {
      request_id: $("request_id").value.trim(),
      correlation_id: $("correlation_id").value.trim(),
      agent_id: $("agent_id").value.trim(),
      principal_id: $("principal_id").value.trim(),
      attempted_enforcement: $("attempted_enforcement").value,
      evaluated_at: $("evaluated_at").value.trim(),
      evidence_window_minutes: parseInt($("evidence_window_minutes").value, 10) || 15,
      checks: collectChecks(),
      post_containment_activity: activity,
      containment_regression_detected: Boolean($("containment_regression_detected").checked),
      agent_self_report_stopped: Boolean($("agent_self_report_stopped").checked),
      preset_id: selectedPreset || null
    };
  }

  function listHtml(items) {
    if (!items || !items.length) return "<p class=\"hint\">None for this simulated result.</p>";
    return (
      "<ul>" +
      items
        .map(function (item) {
          return "<li class=\"lab007-wrap\">" + escapeHtml(humanLabel(item) !== item ? humanLabel(item) + " (" + item + ")" : item) + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  function plainList(items) {
    if (!items || !items.length) return "<p class=\"hint\">None for this simulated result.</p>";
    return (
      "<ul>" +
      items
        .map(function (item) {
          return "<li class=\"lab007-wrap\">" + escapeHtml(item) + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  function checksTable(checks) {
    if (!checks || !checks.length) return "";
    var rows = checks
      .map(function (c) {
        return (
          "<tr>" +
          "<td class=\"lab007-wrap\">" +
          escapeHtml(humanLabel(c.check_id)) +
          "</td>" +
          "<td>" +
          escapeHtml(humanLabel(c.check_result)) +
          "</td>" +
          "<td class=\"lab007-wrap\">" +
          escapeHtml(c.observed_state) +
          "</td>" +
          "<td class=\"lab007-wrap\">" +
          escapeHtml(c.evidence_reference || "—") +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
    return (
      "<div class=\"lab007-table-wrap\"><table class=\"lab007-checks-table\"><thead><tr>" +
      "<th>Check</th><th>Result</th><th>Observed</th><th>Evidence</th>" +
      "</tr></thead><tbody>" +
      rows +
      "</tbody></table></div>"
    );
  }

  function renderResult(data) {
    lastResponse = data;
    var panel = $("lab007-result");
    if (!panel) return;
    var status = data.assurance_status;
    var tone = String(status || "").toLowerCase();
    panel.className = "lab007-result lab007-tone-" + tone;
    panel.hidden = false;
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML =
      "<h3>Assurance result</h3>" +
      "<p class=\"decision-label\">" +
      escapeHtml(humanLabel(data.attempted_enforcement)) +
      " attempted · " +
      escapeHtml(humanLabel(status)) +
      "</p>" +
      "<dl class=\"lab007-result-grid\">" +
      "<div><dt>Attempted enforcement</dt><dd>" +
      escapeHtml(humanLabel(data.attempted_enforcement)) +
      "</dd></div>" +
      "<div><dt>Assurance status</dt><dd>" +
      escapeHtml(humanLabel(status)) +
      "</dd></div>" +
      "<div><dt>Containment effective</dt><dd>" +
      escapeHtml(data.containment_effective ? "Yes" : "No") +
      "</dd></div>" +
      "<div><dt>Real execution</dt><dd>" +
      escapeHtml(humanLabel(data.execution)) +
      "</dd></div>" +
      "</dl>" +
      "<p>" +
      escapeHtml(data.summary) +
      "</p>" +
      "<p>" +
      escapeHtml(data.explanation) +
      "</p>" +
      "<h4>Passed checks</h4>" +
      listHtml(data.passed_checks) +
      "<h4>Failed checks</h4>" +
      listHtml(data.failed_checks) +
      "<h4>Missing evidence</h4>" +
      listHtml(data.missing_evidence) +
      "<h4>Residual paths</h4>" +
      plainList(data.residual_paths) +
      "<h4>Post-containment activity</h4>" +
      plainList(data.post_containment_activity) +
      "<h4>Reason codes</h4>" +
      plainList(data.reason_codes) +
      "<h4>Check details</h4>" +
      checksTable(data.checks) +
      "<details class=\"lab007-raw\"><summary>Raw JSON</summary><pre class=\"lab007-mono\">" +
      escapeHtml(JSON.stringify(data, null, 2)) +
      "</pre></details>";
  }

  function showError(message) {
    var panel = $("lab007-result");
    if (!panel) return;
    panel.hidden = false;
    panel.className = "lab007-result lab007-tone-failed";
    panel.innerHTML =
      "<h3>Evaluation could not complete</h3><p>" + escapeHtml(message) + "</p>";
  }

  function loadPreset(presetId) {
    track("lab_preset_selected", { lab_id: LAB_ID, preset_id: presetId });
    return fetch("/api/labs/007/presets/" + encodeURIComponent(presetId))
      .then(function (res) {
        if (!res.ok) throw new Error("Could not load preset.");
        return res.json();
      })
      .then(function (detail) {
        fillFromRequest(detail.request, detail.id);
      })
      .catch(function (err) {
        showError(err.message || "Preset load failed.");
      });
  }

  function evaluate() {
    var payload = collectPayload();
    track("lab_evaluate", { lab_id: LAB_ID, preset_id: selectedPreset || "custom" });
    return fetch("/api/labs/007/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (res) {
        return res.json().then(function (body) {
          if (!res.ok) {
            throw new Error((body && (body.reason || body.detail)) || "Evaluation failed.");
          }
          return body;
        });
      })
      .then(function (data) {
        renderResult(data);
        var panel = $("lab007-result");
        if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch(function (err) {
        showError(typeof err.message === "string" ? err.message : "Evaluation failed.");
      });
  }

  function init() {
    document.querySelectorAll(".preset-card[data-preset]").forEach(function (card) {
      card.addEventListener("click", function () {
        loadPreset(card.getAttribute("data-preset"));
      });
    });
    var form = $("lab007-form");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        evaluate();
      });
    }
    loadPreset("complete_containment");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
