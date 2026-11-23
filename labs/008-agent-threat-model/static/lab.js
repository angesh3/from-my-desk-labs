(function () {
  "use strict";

  var LAB_ID = "008";
  var selectedPreset = "";
  var lastResponse = null;

  var SURFACE_LABELS = {
    IDENTITY: "Identity",
    AUTHORITY: "Authority",
    INSTRUCTIONS: "Instructions and intent",
    MEMORY_CONTEXT: "Memory and context",
    TOOLS_EXECUTION: "Tools and execution",
    DELEGATION: "Delegation and coordination",
    EVIDENCE_CONTROL: "Evidence and control"
  };

  var COVERAGE_LABELS = {
    COMPLETE: "Complete",
    PARTIAL: "Partial",
    NONE: "None",
    UNVERIFIED: "Unverified"
  };

  var RISK_LABELS = {
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical",
    UNKNOWN: "Unknown"
  };

  var STATUS_LABELS = {
    PRESENT: "Present",
    MISSING: "Missing",
    INEFFECTIVE: "Ineffective",
    UNKNOWN: "Unknown"
  };

  var LABELS = Object.assign(
    {
      not_performed: "Not performed",
      preventive: "Preventive",
      detective: "Detective",
      containment: "Containment",
      recovery: "Recovery"
    },
    SURFACE_LABELS,
    COVERAGE_LABELS,
    RISK_LABELS,
    STATUS_LABELS
  );

  var CONTROL_GROUPS = [
    "preventive_controls",
    "detective_controls",
    "containment_controls",
    "recovery_controls"
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

  function humanLabel(value) {
    if (value == null || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    var key = String(value);
    if (Object.prototype.hasOwnProperty.call(LABELS, key)) return LABELS[key];
    return key;
  }

  function setValue(id, value) {
    var el = $(id);
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = Boolean(value);
      return;
    }
    el.value = value == null ? "" : String(value);
  }

  function getValue(id) {
    var el = $(id);
    if (!el) return "";
    if (el.type === "checkbox") return el.checked;
    return el.value;
  }

  function linesToList(text) {
    return String(text || "")
      .split(/\n|,/)
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
  }

  function listToLines(items) {
    return (items || []).join("\n");
  }

  function coverageTone(coverage) {
    if (coverage === "COMPLETE") return "complete";
    if (coverage === "PARTIAL") return "partial";
    if (coverage === "NONE") return "none";
    return "unverified";
  }

  function coverageSymbol(coverage) {
    if (coverage === "COMPLETE") return "✓";
    if (coverage === "PARTIAL") return "!";
    if (coverage === "NONE") return "×";
    return "?";
  }

  function renderControlEditor(group, items) {
    var host = $(group + "_editor");
    if (!host) return;
    host.innerHTML = "";
    (items || []).forEach(function (item, index) {
      var row = document.createElement("div");
      row.className = "lab008-control-row";
      row.dataset.index = String(index);
      row.innerHTML =
        '<label>Control ID<input data-field="control_id" value="' +
        escapeHtml(item.control_id || "") +
        '"></label>' +
        '<label>Name<input data-field="name" value="' +
        escapeHtml(item.name || "") +
        '"></label>' +
        '<label>Status<select data-field="status">' +
        ["PRESENT", "MISSING", "INEFFECTIVE", "UNKNOWN"]
          .map(function (status) {
            return (
              '<option value="' +
              status +
              '"' +
              (item.status === status ? " selected" : "") +
              ">" +
              humanLabel(status) +
              "</option>"
            );
          })
          .join("") +
        "</select></label>" +
        '<label class="lab008-span-2">Expected behavior<textarea data-field="expected_behavior" rows="2">' +
        escapeHtml(item.expected_behavior || "") +
        "</textarea></label>" +
        '<label>Evidence reference<input data-field="evidence_reference" value="' +
        escapeHtml(item.evidence_reference || "") +
        '"></label>';
      host.appendChild(row);
    });
  }

  function collectControls(group, category) {
    var host = $(group + "_editor");
    if (!host) return [];
    var rows = host.querySelectorAll(".lab008-control-row");
    var out = [];
    rows.forEach(function (row) {
      var get = function (field) {
        var el = row.querySelector('[data-field="' + field + '"]');
        return el ? el.value.trim() : "";
      };
      var controlId = get("control_id");
      if (!controlId) return;
      out.push({
        control_id: controlId,
        name: get("name") || controlId,
        category: category,
        expected_behavior: get("expected_behavior") || "Expected behavior not specified",
        evidence_reference: get("evidence_reference") || null,
        status: get("status") || "UNKNOWN"
      });
    });
    return out;
  }

  function collectPayload() {
    return {
      case_id: getValue("case_id"),
      title: getValue("title"),
      description: getValue("description"),
      agent_identity: getValue("agent_identity"),
      principal_identity: getValue("principal_identity"),
      environment: getValue("environment"),
      policy_version: getValue("policy_version") || "lab008-threat-model-v1",
      asset_name: getValue("asset_name"),
      asset_type: getValue("asset_type"),
      asset_sensitivity: getValue("asset_sensitivity"),
      security_objective: getValue("security_objective"),
      threat_source: getValue("threat_source"),
      failure_mode: getValue("failure_mode"),
      primary_surface: getValue("primary_surface"),
      secondary_surfaces: linesToList(getValue("secondary_surfaces")),
      trust_boundary: getValue("trust_boundary"),
      preconditions: linesToList(getValue("preconditions")),
      threat_path: linesToList(getValue("threat_path")),
      potential_impact: getValue("potential_impact"),
      initial_likelihood: getValue("initial_likelihood"),
      initial_impact: getValue("initial_impact"),
      preventive_controls: collectControls("preventive_controls", "preventive"),
      detective_controls: collectControls("detective_controls", "detective"),
      containment_controls: collectControls("containment_controls", "containment"),
      recovery_controls: collectControls("recovery_controls", "recovery"),
      evidence_sources: linesToList(getValue("evidence_sources")),
      evidence_summary: getValue("evidence_summary"),
      evidence_gaps: linesToList(getValue("evidence_gaps")),
      observation_window: getValue("observation_window") || "15m",
      agent_self_report_present: Boolean(getValue("agent_self_report_present")),
      independent_evidence_sufficient: Boolean(
        getValue("independent_evidence_sufficient")
      ),
      residual_likelihood: getValue("residual_likelihood") || null,
      residual_impact: getValue("residual_impact") || null,
      preset_id: selectedPreset || null
    };
  }

  function applyRequest(request) {
    if (!request) return;
    setValue("case_id", request.case_id);
    setValue("title", request.title);
    setValue("description", request.description);
    setValue("agent_identity", request.agent_identity);
    setValue("principal_identity", request.principal_identity);
    setValue("environment", request.environment);
    setValue("policy_version", request.policy_version);
    setValue("asset_name", request.asset_name);
    setValue("asset_type", request.asset_type);
    setValue("asset_sensitivity", request.asset_sensitivity);
    setValue("security_objective", request.security_objective);
    setValue("threat_source", request.threat_source);
    setValue("failure_mode", request.failure_mode);
    setValue("primary_surface", request.primary_surface);
    setValue("secondary_surfaces", listToLines(request.secondary_surfaces || []));
    setValue("trust_boundary", request.trust_boundary);
    setValue("preconditions", listToLines(request.preconditions || []));
    setValue("threat_path", listToLines(request.threat_path || []));
    setValue("potential_impact", request.potential_impact);
    setValue("initial_likelihood", request.initial_likelihood);
    setValue("initial_impact", request.initial_impact);
    setValue("evidence_sources", listToLines(request.evidence_sources || []));
    setValue("evidence_summary", request.evidence_summary || "");
    setValue("evidence_gaps", listToLines(request.evidence_gaps || []));
    setValue("observation_window", request.observation_window || "15m");
    setValue("agent_self_report_present", request.agent_self_report_present);
    setValue(
      "independent_evidence_sufficient",
      request.independent_evidence_sufficient !== false
    );
    setValue("residual_likelihood", request.residual_likelihood || "");
    setValue("residual_impact", request.residual_impact || "");
    renderControlEditor("preventive_controls", request.preventive_controls || []);
    renderControlEditor("detective_controls", request.detective_controls || []);
    renderControlEditor("containment_controls", request.containment_controls || []);
    renderControlEditor("recovery_controls", request.recovery_controls || []);
  }

  function renderList(items) {
    if (!items || !items.length) return "<p class=\"hint\">None recorded.</p>";
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

  function renderResult(data) {
    var host = $("lab008-result");
    if (!host) return;
    lastResponse = data;
    var tone = coverageTone(data.control_coverage);
    var secondary =
      (data.secondary_surfaces || [])
        .map(function (item) {
          return humanLabel(item);
        })
        .join(", ") || "None";
    host.className = "lab008-result lab008-tone-" + tone;
    host.innerHTML =
      "<h3><span class=\"lab008-coverage-mark\" aria-hidden=\"true\">" +
      escapeHtml(coverageSymbol(data.control_coverage)) +
      "</span> Control coverage: " +
      escapeHtml(humanLabel(data.control_coverage)) +
      " <span class=\"lab008-mono\">(" +
      escapeHtml(data.control_coverage) +
      ")</span></h3>" +
      "<p class=\"hint\">Real execution: <code>not_performed</code></p>" +
      '<dl class="lab008-result-grid">' +
      "<div><dt>Primary threat surface</dt><dd>" +
      escapeHtml(humanLabel(data.primary_surface)) +
      " <span class=\"lab008-mono\">(" +
      escapeHtml(data.primary_surface) +
      ")</span></dd></div>" +
      "<div><dt>Secondary surfaces</dt><dd>" +
      escapeHtml(secondary) +
      "</dd></div>" +
      "<div><dt>Initial risk</dt><dd>" +
      escapeHtml(humanLabel(data.initial_risk)) +
      " <span class=\"lab008-mono\">(" +
      escapeHtml(data.initial_risk) +
      ")</span></dd></div>" +
      "<div><dt>Residual risk</dt><dd>" +
      escapeHtml(humanLabel(data.residual_risk)) +
      " <span class=\"lab008-mono\">(" +
      escapeHtml(data.residual_risk) +
      ")</span></dd></div>" +
      "</dl>" +
      "<p>" +
      escapeHtml(data.residual_risk_explanation || "") +
      "</p>" +
      "<h4>Material gaps</h4>" +
      renderList(data.material_gaps) +
      "<h4>Recommended actions</h4>" +
      renderList(data.recommended_actions) +
      "<h4>Assumptions</h4>" +
      renderList(data.assumptions) +
      "<h4>Limitations</h4>" +
      renderList(data.limitations) +
      "<h4>Reason codes</h4>" +
      renderList(data.reason_codes) +
      '<details class="lab008-raw"><summary>Raw JSON</summary><pre>' +
      escapeHtml(JSON.stringify(data, null, 2)) +
      "</pre></details>";
  }

  function setPresetSelection(presetId) {
    selectedPreset = presetId || "";
    document.querySelectorAll(".preset-card[data-preset]").forEach(function (card) {
      var active = card.getAttribute("data-preset") === selectedPreset;
      card.setAttribute("aria-pressed", active ? "true" : "false");
      var label = card.querySelector(".preset-selected-label");
      if (label) label.hidden = !active;
    });
  }

  function loadPreset(presetId) {
    track("lab_preset_selected", { lab_id: LAB_ID, preset_id: presetId });
    return fetch("/api/labs/008/presets/" + encodeURIComponent(presetId))
      .then(function (response) {
        if (!response.ok) throw new Error("Preset unavailable");
        return response.json();
      })
      .then(function (detail) {
        setPresetSelection(presetId);
        applyRequest(detail.request);
        return detail;
      });
  }

  function evaluateCase() {
    var payload = collectPayload();
    track("lab_evaluate", { lab_id: LAB_ID, preset_id: selectedPreset || "custom" });
    return fetch("/api/labs/008/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok) throw body;
          return body;
        });
      })
      .then(function (data) {
        renderResult(data);
      })
      .catch(function (err) {
        var host = $("lab008-result");
        if (!host) return;
        host.className = "lab008-result lab008-tone-none";
        host.innerHTML =
          "<h3>Evaluation could not be completed</h3><p>" +
          escapeHtml((err && (err.reason || err.detail)) || "Request failed") +
          "</p><p class=\"hint\">Real execution: <code>not_performed</code></p>";
      });
  }

  function bind() {
    document.querySelectorAll(".preset-card[data-preset]").forEach(function (card) {
      card.addEventListener("click", function () {
        var presetId = card.getAttribute("data-preset");
        loadPreset(presetId).then(function () {
          evaluateCase();
        });
      });
    });
    var form = $("lab008-form");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        evaluateCase();
      });
    }
  }

  bind();
  loadPreset("retrieved_prompt_injection_blocked").then(function () {
    evaluateCase();
  });
})();
