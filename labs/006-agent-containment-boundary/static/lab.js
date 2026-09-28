(function () {
  "use strict";

  var LAB_ID = "006";
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
    JUSTIFIED_REFUSAL: "Justified refusal",
    NEEDS_REVIEW: "Needs review",
    NON_COMPLIANT: "Non-compliant",
    ROGUE_BEHAVIOR: "Rogue behavior",
    CONTINUE: "Continue",
    RESTRICT: "Restrict",
    ISOLATE: "Isolate",
    TERMINATE: "Terminate",
    not_performed: "Not performed",
    preserved: "Preserved",
    incomplete: "Incomplete",
    broken: "Broken",
    valid: "Valid",
    suspended: "Suspended",
    revoked: "Revoked",
    expired: "Expired",
    active: "Active",
    none: "None",
    incident_commander: "Incident commander",
    unverified_operator: "Unverified operator",
    automated_alert: "Automated alert",
    peer_agent: "Peer agent",
    high: "High",
    medium: "Medium",
    low: "Low",
    conflicting: "Conflicting",
    moderate: "Moderate",
    critical: "Critical",
    easily_reversible: "Easily reversible",
    partially_reversible: "Partially reversible",
    difficult_to_reverse: "Difficult to reverse",
    irreversible: "Irreversible",
    urgent: "Urgent",
    immediate_threat: "Immediate threat",
    "authority.stop_source_unverified": "Stop source unverified",
    "authority.principal_invalid": "Principal authority invalid",
    "policy.request_prohibited": "Request prohibited by policy",
    "policy.outside_delegated_scope": "Outside delegated scope",
    "policy.safety_rule_triggered": "Safety rule triggered",
    "policy.request_requires_review": "Request requires review",
    "instruction.valid_stop_present": "Valid stop present",
    "instruction.valid_stop_followed": "Valid stop followed",
    "instruction.valid_stop_ignored": "Valid stop ignored",
    "instruction.needs_review": "Instruction needs review",
    "agent.justified_refusal": "Justified refusal",
    "agent.tool_switch_after_revocation": "Tool switch after revocation",
    "agent.delegation_after_stop": "Delegation after stop",
    "agent.within_policy": "Within policy",
    "credential.use_after_revocation": "Credential use after revocation",
    "lease.invalid_or_expired": "Lease invalid or expired",
    "delegation.around_containment": "Delegation around containment",
    "containment.continued_after_isolation": "Continued after isolation",
    "containment.restrict_while_reviewing": "Restrict while reviewing",
    "containment.repeated_high_impact_violations": "Repeated high-impact violations",
    "containment.high_impact_no_broad_path": "High-impact: no broad path",
    "containment.effective": "Containment effective",
    "evidence.preserve_required": "Evidence preservation required",
    "receipt.chain_preserved": "Receipt chain preserved",
    "receipt.chain_broken": "Receipt chain broken"
  };

  function humanLabel(value) {
    if (value == null || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    var key = String(value);
    if (Object.prototype.hasOwnProperty.call(LABELS, key)) {
      return LABELS[key];
    }
    if (key.indexOf("_") !== -1) {
      return key
        .split("_")
        .map(function (part) {
          return part ? part.charAt(0).toUpperCase() + part.slice(1).toLowerCase() : part;
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

  function getBool(id) {
    var el = $(id);
    return el ? Boolean(el.checked) : false;
  }

  function getList(id) {
    var el = $(id);
    if (!el) return [];
    return String(el.value || "")
      .split(/\n|,/)
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean)
      .slice(0, 20);
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

  function fillFromRequest(request, presetId) {
    if (!request) return;
    setValue("principal_identity", request.principal_identity);
    setValue("principal_role", request.principal_role);
    setValue("principal_authority_valid", request.principal_authority_valid);
    setValue("agent_identity", request.agent_identity);
    setValue("agent_owner", request.agent_owner);
    setValue("requested_action", request.requested_action);
    setValue("stop_instruction_present", request.stop_instruction_present);
    setValue("stop_instruction_source", request.stop_instruction_source);
    setValue("stop_instruction_authority_valid", request.stop_instruction_authority_valid);
    setValue("stop_instruction_acknowledged", request.stop_instruction_acknowledged);
    setValue("policy_id", request.policy_id);
    setValue("policy_version", request.policy_version);
    setValue("policy_allows_requested_action", request.policy_allows_requested_action);
    setValue("request_within_delegated_scope", request.request_within_delegated_scope);
    setValue("safety_rule_triggered", request.safety_rule_triggered);
    setValue("evidence_confidence", request.evidence_confidence);
    setValue("potential_impact", request.potential_impact);
    setValue("reversibility", request.reversibility);
    setValue("time_sensitivity", request.time_sensitivity);
    setValue("active_tool_sessions", request.active_tool_sessions);
    setValue("active_sub_agents", request.active_sub_agents);
    setValue("credential_state", request.credential_state);
    setValue("execution_lease_state", request.execution_lease_state);
    setValue("attempted_tool_switch", request.attempted_tool_switch);
    setValue("attempted_delegation_after_stop", request.attempted_delegation_after_stop);
    setValue("attempted_use_after_revocation", request.attempted_use_after_revocation);
    setValue("continued_after_isolation", request.continued_after_isolation);
    setValue("violation_count", request.violation_count);
    setValue("receipt_chain_status", request.receipt_chain_status);
    setValue("agent_refused_request", request.agent_refused_request);
    setValue("agent_requested_clarification", request.agent_requested_clarification);
    setValue("agent_followed_stop", request.agent_followed_stop);
    setValue("containment_already_applied", request.containment_already_applied);
    markSelected(presetId);
  }

  function collectPayload() {
    return {
      principal_identity: $("principal_identity").value.trim(),
      principal_role: $("principal_role").value.trim(),
      principal_authority_valid: getBool("principal_authority_valid"),
      agent_identity: $("agent_identity").value.trim(),
      agent_owner: $("agent_owner").value.trim(),
      requested_action: $("requested_action").value.trim(),
      stop_instruction_present: getBool("stop_instruction_present"),
      stop_instruction_source: $("stop_instruction_source").value,
      stop_instruction_authority_valid: getBool("stop_instruction_authority_valid"),
      stop_instruction_acknowledged: getBool("stop_instruction_acknowledged"),
      policy_id: $("policy_id").value.trim(),
      policy_version: $("policy_version").value.trim(),
      policy_allows_requested_action: getBool("policy_allows_requested_action"),
      request_within_delegated_scope: getBool("request_within_delegated_scope"),
      safety_rule_triggered: getBool("safety_rule_triggered"),
      evidence_confidence: $("evidence_confidence").value,
      potential_impact: $("potential_impact").value,
      reversibility: $("reversibility").value,
      time_sensitivity: $("time_sensitivity").value,
      active_tool_sessions: getList("active_tool_sessions"),
      active_sub_agents: getList("active_sub_agents"),
      credential_state: $("credential_state").value,
      execution_lease_state: $("execution_lease_state").value,
      attempted_tool_switch: getBool("attempted_tool_switch"),
      attempted_delegation_after_stop: getBool("attempted_delegation_after_stop"),
      attempted_use_after_revocation: getBool("attempted_use_after_revocation"),
      continued_after_isolation: getBool("continued_after_isolation"),
      violation_count: parseInt($("violation_count").value, 10) || 0,
      receipt_chain_status: $("receipt_chain_status").value,
      agent_refused_request: getBool("agent_refused_request"),
      agent_requested_clarification: getBool("agent_requested_clarification"),
      agent_followed_stop: getBool("agent_followed_stop"),
      containment_already_applied: getBool("containment_already_applied"),
      preset_id: selectedPreset || null
    };
  }

  function listHtml(items) {
    if (!items || !items.length) return "<p class=\"hint\">None for this simulated result.</p>";
    return (
      "<ul>" +
      items
        .map(function (item) {
          return "<li>" + escapeHtml(item) + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  function reasonListHtml(codes) {
    if (!codes || !codes.length) return "<p class=\"hint\">No reason codes.</p>";
    return (
      "<ul class=\"lab006-reason-list\">" +
      codes
        .map(function (code) {
          return (
            "<li><code class=\"lab006-mono\">" +
            escapeHtml(code) +
            "</code> — " +
            escapeHtml(humanLabel(code)) +
            "</li>"
          );
        })
        .join("") +
      "</ul>"
    );
  }

  function complianceLabel(value) {
    if (value === true) return "Yes";
    if (value === false) return "No";
    return "Not applicable";
  }

  function renderResult(data) {
    lastResponse = data;
    var panel = $("lab006-result");
    if (!panel) return;
    var assessment = data.behavior_assessment;
    var enforcement = data.enforcement_response;
    var tone = "continue";
    if (enforcement === "RESTRICT") tone = "restrict";
    if (enforcement === "ISOLATE") tone = "isolate";
    if (enforcement === "TERMINATE") tone = "terminate";
    panel.className = "lab006-result lab006-tone-" + tone;
    panel.hidden = false;
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML =
      "<h3>Evaluation result</h3>" +
      "<p class=\"decision-label\">" +
      escapeHtml(assessment ? humanLabel(assessment) : "Compliant behavior (no refusal)") +
      " · " +
      escapeHtml(humanLabel(enforcement)) +
      "</p>" +
      "<dl class=\"lab006-result-grid\">" +
      "<div><dt>Behavior assessment</dt><dd>" +
      escapeHtml(assessment ? humanLabel(assessment) : "— (compliant stop / no refusal)") +
      "</dd></div>" +
      "<div><dt>Instruction compliance</dt><dd>" +
      escapeHtml(complianceLabel(data.instruction_compliance)) +
      "</dd></div>" +
      "<div><dt>Enforcement response</dt><dd>" +
      escapeHtml(humanLabel(enforcement)) +
      "</dd></div>" +
      "<div><dt>Containment effective</dt><dd>" +
      escapeHtml(data.containment_effective ? "Yes" : "No") +
      "</dd></div>" +
      "<div><dt>Real execution</dt><dd>" +
      escapeHtml(humanLabel(data.execution)) +
      "</dd></div>" +
      "<div><dt>Receipt chain</dt><dd>" +
      escapeHtml(humanLabel(data.receipt_chain_status)) +
      "</dd></div>" +
      "</dl>" +
      "<p>" +
      escapeHtml(data.summary) +
      "</p>" +
      "<p>" +
      escapeHtml(data.human_explanation) +
      "</p>" +
      "<h4>Reason codes</h4>" +
      reasonListHtml(data.reason_codes) +
      "<h4>Authority findings</h4>" +
      listHtml(data.authority_findings) +
      "<h4>Policy findings</h4>" +
      listHtml(data.policy_findings) +
      "<h4>Behavior findings</h4>" +
      listHtml(data.behavior_findings) +
      "<h4 id=\"containment-actions-heading\">Recommended containment actions</h4>" +
      "<p class=\"hint\">Simulated policy outputs only. No real agent, credential, process, tool session, or external system is modified.</p>" +
      listHtml(data.containment_actions) +
      "<h4>Recovery requirements</h4>" +
      listHtml(data.recovery_requirements) +
      "<h4>Evidence to preserve</h4>" +
      listHtml(data.evidence_to_preserve) +
      "<details class=\"lab006-raw\"><summary>Raw JSON</summary><pre class=\"lab006-mono\">" +
      escapeHtml(JSON.stringify(data, null, 2)) +
      "</pre></details>";
  }

  function showError(message) {
    var panel = $("lab006-result");
    if (!panel) return;
    panel.hidden = false;
    panel.className = "lab006-result lab006-tone-terminate";
    panel.innerHTML =
      "<h3>Evaluation could not complete</h3><p>" + escapeHtml(message) + "</p>";
  }

  function loadPreset(presetId) {
    track("lab_preset_selected", { lab_id: LAB_ID, preset_id: presetId });
    return fetch("/api/labs/006/presets/" + encodeURIComponent(presetId))
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
    return fetch("/api/labs/006/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (res) {
        return res.json().then(function (body) {
          if (!res.ok) {
            throw new Error(
              (body && (body.reason || body.detail)) || "Evaluation failed."
            );
          }
          return body;
        });
      })
      .then(function (data) {
        renderResult(data);
        var panel = $("lab006-result");
        if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch(function (err) {
        showError(
          typeof err.message === "string" ? err.message : "Evaluation failed."
        );
      });
  }

  function init() {
    document.querySelectorAll(".preset-card[data-preset]").forEach(function (card) {
      card.addEventListener("click", function () {
        loadPreset(card.getAttribute("data-preset"));
      });
    });
    var form = $("lab006-form");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        evaluate();
      });
    }
    var first = document.querySelector('.preset-card[data-preset="justified_policy_refusal"]');
    if (first) loadPreset("justified_policy_refusal");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
