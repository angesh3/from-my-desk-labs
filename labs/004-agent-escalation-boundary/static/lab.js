(function () {
  "use strict";

  var LAB_ID = "004";
  var LAB_SLUG = "agent-escalation-boundary";
  var selectedPreset = null;

  var FIELD_IDS = [
    "goal_clarity",
    "evidence_confidence",
    "potential_impact",
    "reversibility",
    "policy_coverage",
    "time_sensitivity",
    "human_availability",
    "authorization_outcome",
    "agent_id",
    "principal_id",
    "requested_action",
    "target_account",
    "delegated_capability",
    "business_context"
  ];

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

  function setValue(id, value) {
    var node = $(id);
    if (!node) {
      return;
    }
    if (node.type === "checkbox") {
      node.checked = !!value;
    } else {
      node.value = value == null ? "" : String(value);
    }
  }

  function readForm() {
    var payload = {};
    FIELD_IDS.forEach(function (id) {
      var node = $(id);
      if (node) {
        payload[id] = node.value;
      }
    });
    payload.confirmation_satisfied = !!($("confirmation_satisfied") && $("confirmation_satisfied").checked);
    payload.stronger_auth_completed = !!($("stronger_auth_completed") && $("stronger_auth_completed").checked);
    if (selectedPreset) {
      payload.preset_id = selectedPreset;
    }
    return payload;
  }

  function applyRequest(request) {
    if (!request) {
      return;
    }
    FIELD_IDS.forEach(function (id) {
      if (Object.prototype.hasOwnProperty.call(request, id)) {
        setValue(id, request[id]);
      }
    });
    setValue("confirmation_satisfied", request.confirmation_satisfied);
    setValue("stronger_auth_completed", request.stronger_auth_completed);
  }

  function outcomeClass(outcome) {
    return "lab004-outcome-" + String(outcome || "stop");
  }

  function renderResult(data) {
    var root = $("result");
    if (!root) {
      return;
    }
    var auth = String(data.authorization_outcome || "").toUpperCase().replace("_", "-");
    var exec = String(data.execution_outcome || "").toUpperCase();
    var rules = (data.triggered_rules || [])
      .map(function (rule) {
        return "<li><strong>" + rule.rule_id + ":</strong> " + rule.summary + "</li>";
      })
      .join("");
    var missing = (data.missing_or_conflicting_evidence || [])
      .map(function (item) {
        return "<li>" + item + "</li>";
      })
      .join("");
    var safe = (data.safe_actions_permitted || [])
      .map(function (item) {
        return "<li>" + item + "</li>";
      })
      .join("");
    var approval = (data.actions_requiring_approval || [])
      .map(function (item) {
        return "<li>" + item + "</li>";
      })
      .join("");
    var bounded = data.bounded_protective_action || {};
    var boundedHtml = "";
    if (bounded.available) {
      boundedHtml =
        "<div class=\"lab004-bounded\">" +
        "<h3>Recommended bounded action</h3>" +
        "<p>" +
        (bounded.explanation || "") +
        "</p>" +
        "<ul>" +
        (bounded.actions || [])
          .map(function (item) {
            return "<li>" + item + "</li>";
          })
          .join("") +
        "</ul>" +
        "<p role=\"note\"><strong>Authority note:</strong> This path does not expand the agent’s delegated capability.</p>" +
        "</div>";
    }

    root.innerHTML =
      '<p class="decision ' +
      outcomeClass(data.execution_outcome) +
      '"><span class="decision-label">' +
      exec +
      "</span></p>" +
      "<p><strong>Authorization outcome:</strong> " +
      auth +
      "</p>" +
      "<p class=\"result-reason\">" +
      (data.explanation || "") +
      "</p>" +
      "<p><strong>Evidence assessment:</strong> " +
      (data.evidence_assessment || "") +
      "</p>" +
      "<h3>Triggered rules</h3><ul>" +
      rules +
      "</ul>" +
      "<h3>Why the agent paused or proceeded</h3><p>" +
      (data.why_paused_or_proceeded || "") +
      "</p>" +
      (missing
        ? "<h3>Missing or conflicting evidence</h3><ul>" + missing + "</ul>"
        : "") +
      "<h3>Impact of acting</h3><p>" +
      (data.impact_of_acting || "") +
      "</p>" +
      "<h3>Impact of waiting</h3><p>" +
      (data.impact_of_waiting || "") +
      "</p>" +
      "<h3>Safe actions already permitted</h3><ul>" +
      safe +
      "</ul>" +
      "<h3>Actions requiring human approval</h3><ul>" +
      approval +
      "</ul>" +
      boundedHtml +
      "<h3>Recommended next step</h3><p>" +
      (data.recommended_next_step || "") +
      "</p>" +
      (data.escalation_destination
        ? "<p><strong>Escalation destination:</strong> " + data.escalation_destination + "</p>"
        : "") +
      "<p><strong>Authority chain:</strong> " +
      (data.authority_chain_summary || "") +
      "</p>" +
      "<ul class=\"result-primary\">" +
      "<li><strong>Decision ID:</strong> " +
      (data.decision_id || "") +
      "</li>" +
      "<li><strong>Evaluated at:</strong> " +
      (data.evaluated_at || "") +
      "</li>" +
      "<li><strong>Execution:</strong> not performed</li>" +
      "</ul>";
  }

  function selectPresetButton(presetId) {
    selectedPreset = presetId;
    document.querySelectorAll(".preset-card").forEach(function (btn) {
      var on = btn.getAttribute("data-preset") === presetId;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      var badge = btn.querySelector(".preset-selected-label");
      if (badge) {
        badge.hidden = !on;
      }
    });
  }

  function loadPreset(presetId) {
    selectPresetButton(presetId);
    track("lab_preset_selected", {
      lab_id: LAB_ID,
      lab_slug: LAB_SLUG,
      preset_id: presetId
    });
    fetch("/api/labs/004/presets/" + encodeURIComponent(presetId), {
      headers: { Accept: "application/json" }
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (payload) {
        if (!payload.ok) {
          return;
        }
        applyRequest(payload.body.request || {});
      })
      .catch(function () {
        return;
      });
  }

  function evaluate(event) {
    if (event) {
      event.preventDefault();
    }
    var payload = readForm();
    var btn = $("evaluate-btn");
    if (btn) {
      btn.disabled = true;
    }
    fetch("/api/labs/004/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (payload) {
        if (btn) {
          btn.disabled = false;
        }
        if (!payload.ok) {
          var root = $("result");
          if (root) {
            root.innerHTML =
              '<p class="decision lab004-outcome-stop"><span class="decision-label">ERROR</span></p>' +
              "<p>Evaluation could not be completed.</p>";
          }
          return;
        }
        renderResult(payload.body);
        var outcome = payload.body.execution_outcome;
        track("policy_evaluation_completed", {
          lab_id: LAB_ID,
          lab_slug: LAB_SLUG,
          preset_id: selectedPreset || "",
          decision: outcome
        });
        if (outcome === "proceed") {
          track("lab_004_outcome_proceed", { lab_id: LAB_ID });
        } else if (outcome === "clarify") {
          track("lab_004_outcome_clarify", { lab_id: LAB_ID });
        } else if (outcome === "escalate") {
          track("lab_004_outcome_escalate", { lab_id: LAB_ID });
        } else if (outcome === "stop") {
          track("lab_004_outcome_stop", { lab_id: LAB_ID });
        }
      })
      .catch(function () {
        if (btn) {
          btn.disabled = false;
        }
        var root = $("result");
        if (root) {
          root.innerHTML =
            '<p class="decision lab004-outcome-stop"><span class="decision-label">ERROR</span></p>' +
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

    var form = $("lab004-form");
    if (form) {
      form.addEventListener("submit", evaluate);
    }

    var newsletter = document.querySelector("[data-lab004-newsletter]");
    if (newsletter) {
      newsletter.addEventListener("click", function () {
        track("lab_004_newsletter_clicked", { lab_id: LAB_ID, lab_slug: LAB_SLUG });
      });
    }

    document
      .querySelectorAll('img[data-architecture-type="lab004-escalation-boundary"]')
      .forEach(function (arch) {
        arch.addEventListener("click", function () {
          track("architecture_viewed", {
            lab_id: LAB_ID,
            architecture_type: "lab004-escalation-boundary"
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
