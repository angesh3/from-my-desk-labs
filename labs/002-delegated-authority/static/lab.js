(function () {
  "use strict";

  var LAB_ID = "002";
  var LAB_SLUG = "delegated-authority";
  var selectedId = null;
  var selectedCategory = null;
  var lastResult = null;
  var scenariosById = {};

  var FALLBACK_LABELS = {
    none: "None",
    register_agent: "Register the agent",
    collect_profile: "Collect a trusted profile",
    refresh_posture: "Refresh posture evidence",
    request_human_review: "Request human review",
    request_new_delegation: "Request a new delegation",
    request_narrower_action: "Request a narrower action",
    correct_delegation: "Correct the delegation",
    correct_delegation_period: "Correct the delegation period",
    request_direct_delegation: "Request direct delegation",
    upgrade_version: "Upgrade to an approved version",
    restore_approved_configuration: "Restore approved configuration",
    investigate_tool_change: "Investigate the tool change"
  };

  var TAKEAWAY = {
    allow: "Policy approved; execution remains separate.",
    confirm: "Explicit human confirmation required.",
    step_up: "Stronger or fresher assurance required.",
    deny: "Original action stopped."
  };

  function track(eventName, properties) {
    try {
      if (window.FromMyDesk && typeof window.FromMyDesk.track === "function") {
        window.FromMyDesk.track(eventName, properties);
      }
    } catch (err) {
      return;
    }
  }

  function $(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    var node = $(id);
    if (node) {
      node.textContent = value == null || value === "" ? "—" : String(value);
    }
  }

  function humanFallback(type) {
    return FALLBACK_LABELS[type] || String(type || "Recovery action").replace(/_/g, " ");
  }

  function stageTone(stage, status, decision) {
    var s = String(status || "").toLowerCase();
    if (stage === "policy") {
      if (decision === "deny") {
        return "fail";
      }
      if (decision === "confirm" || decision === "step_up") {
        return "challenge";
      }
      if (decision === "allow") {
        return "pass";
      }
    }
    if (
      s.indexOf("fail") >= 0 ||
      s.indexOf("invalid") >= 0 ||
      s.indexOf("broken") >= 0 ||
      s.indexOf("revoked") >= 0 ||
      s.indexOf("expired") >= 0 ||
      s.indexOf("constraint") >= 0 ||
      s.indexOf("unknown") >= 0 ||
      s.indexOf("noncompliant") >= 0 ||
      s === "deny"
    ) {
      return "fail";
    }
    if (
      s.indexOf("stale") >= 0 ||
      s.indexOf("conflict") >= 0 ||
      s.indexOf("mismatch") >= 0 ||
      s === "confirm" ||
      s === "step_up"
    ) {
      return "challenge";
    }
    return "pass";
  }

  function humanStage(stage, status, summary, decision, reasonCode) {
    var tone = stageTone(stage, status, decision);
    var label = "Checked";
    var copy = summary || "";
    if (stage === "identity") {
      if (tone === "fail") {
        label = "Failed";
        copy = reasonCode === "agent_unknown"
          ? "The requesting agent is unknown to the management plane."
          : reasonCode === "principal_mismatch"
            ? "The agent is not bound to the stated principal."
            : "Identity evaluation failed for this agent.";
      } else if (tone === "challenge") {
        label = "Needs assurance";
        copy = "Identity is known, but stronger assurance is required.";
      } else {
        label = "Verified";
        copy = "Agent identity and principal binding are valid.";
      }
    } else if (stage === "delegation") {
      if (tone === "fail") {
        label = "Failed";
        if (reasonCode === "capability_not_delegated") {
          copy = "The requested capability is outside effective authority.";
        } else if (reasonCode === "child_expiry_exceeds_parent") {
          copy = "Child authority expires after its parent.";
        } else if (reasonCode === "child_limit_exceeds_parent") {
          copy = "Child maximum amount exceeds the parent limit.";
        } else if (reasonCode === "child_capability_exceeds_parent") {
          copy = "Child capabilities exceed parent capabilities.";
        } else if (reasonCode === "delegation_depth_exceeded") {
          copy = "Delegation depth was exceeded.";
        } else if (reasonCode === "parent_expired") {
          copy = "A parent delegation expired; downstream authority is invalid.";
        } else if (reasonCode === "parent_revoked") {
          copy = "A parent delegation was revoked; downstream authority is invalid.";
        } else {
          copy = "Delegation constraints were violated.";
        }
      } else {
        label = "Valid";
        copy = "The delegation chain and effective authority are intact.";
      }
    } else if (stage === "ape") {
      if (status === "unknown") {
        label = "Unknown";
        copy = "No trusted profile exists for this agent.";
      } else if (tone === "challenge" || tone === "fail") {
        label = "Mismatch";
        copy = "APE detected a profile mismatch requiring human review.";
      } else {
        label = "Known";
        copy = summary || "Trusted profile is available.";
      }
    } else if (stage === "apse") {
      if (tone === "fail") {
        label = "Noncompliant";
        copy = reasonCode === "tool_inventory_changed"
          ? "Unexpected tools appeared in the inventory."
          : "APSE found a hard posture failure.";
      } else if (tone === "challenge") {
        label = "Stale or recoverable";
        copy = reasonCode === "model_version_noncompliant"
          ? "The model or runtime version needs upgrade."
          : "Posture evidence needs refresh before proceeding.";
      } else {
        label = "Compliant";
        copy = "Posture evidence is current.";
      }
    } else if (stage === "policy") {
      label = String(decision || status || "").toUpperCase().replace("_", "-");
      if (decision === "deny") {
        copy = "Hard failure cannot be overridden by confirmation or stronger authentication.";
      } else if (decision === "confirm") {
        copy = "Authority is valid; explicit confirmation is still required.";
      } else if (decision === "step_up") {
        copy = "Authority may be valid; fresher or stronger assurance is required.";
      } else {
        copy = "Identity, delegation, profile, posture, scope, limits, and context are satisfied.";
      }
    }
    return { tone: tone, label: label, copy: copy };
  }

  function selectScenario(button) {
    var scenarioId = button.getAttribute("data-scenario");
    var category = button.getAttribute("data-category") || "other";
    selectedId = scenarioId;
    selectedCategory = category;

    document.querySelectorAll(".preset-card").forEach(function (btn) {
      var on = btn === button;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      var badge = btn.querySelector(".preset-selected-label");
      if (badge) {
        badge.hidden = !on;
      }
    });

    var evalBtn = $("evaluate-btn");
    if (evalBtn) {
      evalBtn.disabled = !selectedId;
    }

    var annotation = button.getAttribute("data-annotation") || "";
    var note = $("chain-annotation");
    if (note) {
      note.textContent = annotation;
    }
    var focusNode = button.getAttribute("data-node");
    document.querySelectorAll(".chain-node").forEach(function (node) {
      node.classList.toggle("is-focus", node.getAttribute("data-node") === focusNode);
    });

    track("lab_preset_selected", {
      lab_id: LAB_ID,
      scenario_category: selectedCategory,
      preset_id: scenarioId
    });
    loadSummary(scenarioId);
  }

  function loadSummary(scenarioId) {
    var meta = scenariosById[scenarioId] || {};
    setText("sum-capability", meta._capability);
    setText("sum-resource", meta._resource);
    setText("sum-amount", meta._amount);
    setText("sum-time", meta._time);
    setText("sum-class", meta._classification);
    setText("sum-confidence", meta._confidence);
    setText("sum-posture", meta._posture);
    setText("sum-parent", meta._parent);
    var pre = $("request-json");
    if (pre) {
      pre.textContent = JSON.stringify({ scenario_id: scenarioId }, null, 2);
    }
  }

  function renderJourney(data) {
    var journey = data.journey || [];
    var byStage = {};
    journey.forEach(function (step) {
      byStage[step.stage] = step;
    });
    document.querySelectorAll(".journey-step").forEach(function (li) {
      var stage = li.getAttribute("data-stage");
      var raw = byStage[stage] || {};
      var human = humanStage(stage, raw.status, raw.summary, data.decision, data.reason_code);
      li.classList.remove("is-pass", "is-challenge", "is-fail");
      li.classList.add("is-" + human.tone);
      var status = li.querySelector(".journey-status");
      var copy = li.querySelector(".journey-copy");
      if (status) {
        status.textContent = human.label;
      }
      if (copy) {
        copy.textContent = human.copy;
      }
    });
  }

  function renderResult(data) {
    lastResult = data;
    var root = $("result");
    if (!root) {
      return;
    }
    var decision = data.decision || "deny";
    var label = decision.toUpperCase().replace("_", "-");
    var html = "";
    html += '<p class="decision decision-' + decision + '">';
    html += '<span class="decision-label">' + label + "</span></p>";
    html += '<p class="result-takeaway">' + (TAKEAWAY[decision] || "") + "</p>";
    html += '<p class="result-reason">' + (data.explanation || "") + "</p>";
    html += "<ul class=\"result-primary\">";
    html += "<li><strong>Execution:</strong> not performed</li>";
    html += "<li><strong>Fallback:</strong> " +
      (data.fallback && data.fallback.available
        ? humanFallback(data.fallback.fallback_type)
        : "None") +
      "</li>";
    html += "</ul>";
    html += "<details class=\"tech-details\"><summary>Technical details</summary><ul>";
    html += "<li><strong>Reason code:</strong> " + (data.reason_code || "") + "</li>";
    html += "<li><strong>Violated constraint:</strong> " + (data.violated_constraint || "none") + "</li>";
    html += "<li><strong>Delegation path:</strong> " + (data.delegation_path || []).join(" → ") + "</li>";
    html += "<li><strong>Profile version:</strong> " + (data.profile_version || "n/a") + "</li>";
    html += "<li><strong>Posture version:</strong> " + (data.posture_version || "n/a") + "</li>";
    html += "<li><strong>Audit ID:</strong> " + (data.audit_id || "") + "</li>";
    html += "<li><strong>Decision valid until:</strong> " + (data.decision_valid_until || "n/a") + "</li>";
    html += "</ul></details>";
    root.innerHTML = html;
    renderJourney(data);

    var fbSection = $("fallback-section");
    var fbPanel = $("fallback-panel");
    var fbPreview = $("fallback-preview");
    if (fbSection && fbPanel) {
      if (data.fallback && data.fallback.available) {
        fbSection.hidden = false;
        fbPanel.innerHTML =
          "<p><strong>Recovery path:</strong> " + humanFallback(data.fallback.fallback_type) + "</p>" +
          "<p>" + (data.fallback.explanation || "") + "</p>";
        if (fbPreview) {
          fbPreview.hidden = true;
          fbPreview.innerHTML = "";
        }
      } else {
        fbSection.hidden = true;
      }
    }
  }

  function evaluate() {
    if (!selectedId) {
      return;
    }
    fetch("/api/labs/002/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ scenario_id: selectedId })
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (payload) {
        if (!payload.ok) {
          var root = $("result");
          if (root) {
            root.innerHTML = "<p class=\"decision decision-deny\"><span class=\"decision-label\">ERROR</span></p><p>Evaluation could not be completed.</p>";
          }
          return;
        }
        renderResult(payload.body);
        track("policy_evaluation_completed", {
          lab_id: LAB_ID,
          scenario_category: selectedCategory,
          decision: payload.body.decision,
          reason_category: payload.body.reason_category,
          fallback_available: !!(payload.body.fallback && payload.body.fallback.available)
        });
        var selected = document.querySelector(".preset-card.is-selected");
        if (selected && selected.scrollIntoView) {
          selected.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      })
      .catch(function () {
        var root = $("result");
        if (root) {
          root.innerHTML = "<p class=\"decision decision-deny\"><span class=\"decision-label\">ERROR</span></p><p>Network error.</p>";
        }
      });
  }

  function previewFallback() {
    if (!lastResult || !lastResult.fallback || !lastResult.fallback.available) {
      return;
    }
    var fb = lastResult.fallback;
    var node = $("fallback-preview");
    if (!node) {
      return;
    }
    var recovery = humanFallback(fb.fallback_type);
    node.hidden = false;
    node.innerHTML =
      '<ol class="fallback-steps">' +
      "<li><strong>Original decision</strong><span>" +
      String(lastResult.decision || "").toUpperCase().replace("_", "-") +
      "</span></li>" +
      "<li><strong>Action stopped</strong><span>Protected action was not performed</span></li>" +
      "<li><strong>Evidence recorded</strong><span>Audit ID retained</span></li>" +
      "<li><strong>Recovery action</strong><span>" + recovery + "</span></li>" +
      "<li><strong>New request</strong><span>Issue a corrected path</span></li>" +
      "<li><strong>New policy evaluation</strong><span>Required before any progress</span></li>" +
      "</ol>" +
      "<p class=\"fallback-note\">The original decision remains unchanged.</p>" +
      "<p class=\"fallback-note\">Fallback does not execute the protected action.</p>" +
      "<p class=\"fallback-note\">New evaluation required.</p>" +
      "<details class=\"tech-details\"><summary>Technical details</summary><ul>" +
      "<li>Fallback type: " + (fb.fallback_type || "") + "</li>" +
      "<li>Permitted: " + (fb.permitted_operations || []).join(", ") + "</li>" +
      "<li>Prohibited: " + (fb.prohibited_operations || []).join(", ") + "</li>" +
      "</ul></details>";
    track("fallback_previewed", {
      lab_id: LAB_ID,
      decision: lastResult.decision,
      fallback_type: fb.fallback_type
    });
  }

  function hydrateScenarioMeta(list) {
    var summaries = {
      valid_narrow_delegation: { capability: "research", resource: "market-summaries", amount: "500.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      confirmation_required: { capability: "research", resource: "market-summaries", amount: "7500.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      stale_posture: { capability: "research", resource: "market-summaries", amount: "500.00", classification: "Research Agent", confidence: "high", posture: "stale", parent: "active", time: "2026-03-15T14:00:00Z" },
      unusual_context: { capability: "research", resource: "market-summaries", amount: "500.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T02:00:00Z" },
      execution_not_delegated: { capability: "execute", resource: "market-summaries", amount: "500.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      child_capability_exceeds_parent: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      child_limit_exceeds_parent: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      child_expiry_exceeds_parent: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      delegation_depth_exceeded: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      parent_expired: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "expired", time: "2026-03-15T14:00:00Z" },
      parent_revoked: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "Research Agent", confidence: "high", posture: "compliant", parent: "revoked", time: "2026-03-15T14:00:00Z" },
      unknown_agent: { capability: "research", resource: "market-summaries", amount: "100.00", classification: "unknown", confidence: "low", posture: "unknown", parent: "n/a", time: "2026-03-15T14:00:00Z" },
      profile_mismatch: { capability: "research", resource: "market-summaries", amount: "200.00", classification: "Research Agent", confidence: "medium", posture: "compliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      noncompliant_model_version: { capability: "research", resource: "market-summaries", amount: "200.00", classification: "Research Agent", confidence: "medium", posture: "noncompliant", parent: "active", time: "2026-03-15T14:00:00Z" },
      tool_inventory_changed: { capability: "research", resource: "market-summaries", amount: "200.00", classification: "Research Agent", confidence: "high", posture: "noncompliant", parent: "active", time: "2026-03-15T14:00:00Z" }
    };
    (list || []).forEach(function (item) {
      var extra = summaries[item.id] || {};
      item._capability = extra.capability;
      item._resource = extra.resource;
      item._amount = extra.amount;
      item._time = extra.time;
      item._classification = extra.classification;
      item._confidence = extra.confidence;
      item._posture = extra.posture;
      item._parent = extra.parent;
      scenariosById[item.id] = item;
    });
    Object.keys(summaries).forEach(function (id) {
      if (!scenariosById[id]) {
        scenariosById[id] = Object.assign({ id: id }, summaries[id]);
        scenariosById[id]._capability = summaries[id].capability;
        scenariosById[id]._resource = summaries[id].resource;
        scenariosById[id]._amount = summaries[id].amount;
        scenariosById[id]._time = summaries[id].time;
        scenariosById[id]._classification = summaries[id].classification;
        scenariosById[id]._confidence = summaries[id].confidence;
        scenariosById[id]._posture = summaries[id].posture;
        scenariosById[id]._parent = summaries[id].parent;
      }
    });
  }

  function init() {
    track("lab_opened", { lab_id: LAB_ID, lab_slug: LAB_SLUG });
    hydrateScenarioMeta([]);

    fetch("/api/labs/002/scenarios", { headers: { Accept: "application/json" } })
      .then(function (response) { return response.json(); })
      .then(function (list) { hydrateScenarioMeta(list || []); })
      .catch(function () { return; });

    document.querySelectorAll(".preset-card").forEach(function (btn) {
      btn.addEventListener("click", function () {
        selectScenario(btn);
      });
    });

    var evalBtn = $("evaluate-btn");
    if (evalBtn) {
      evalBtn.addEventListener("click", evaluate);
    }
    var previewBtn = $("preview-fallback");
    if (previewBtn) {
      previewBtn.addEventListener("click", previewFallback);
    }

    document.querySelectorAll("#architecture img[data-analytics-destination=\"architecture\"], .lab002-workflow img[data-analytics-destination=\"architecture\"]").forEach(function (arch) {
      arch.addEventListener("click", function () {
        track("architecture_viewed", {
          lab_id: LAB_ID,
          architecture_type: arch.getAttribute("data-architecture-type") || "lab002"
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
