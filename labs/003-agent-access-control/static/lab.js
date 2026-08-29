(function () {
  "use strict";

  var LAB_ID = "003";
  var LAB_SLUG = "agent-access-control";
  var REVEAL_MS = 650;
  var EVALUATING_MS = 220;

  var selectedId = null;
  var selectedCategory = null;
  var evaluationMode = "guided";
  var lastResult = null;
  var scenariosById = {};
  var canonicalEvents = [];
  var revealedCount = 0;
  var revealTimer = null;
  var isPaused = false;
  var isEvaluating = false;
  var prefersReducedMotion = false;
  var lastLiveAnnouncement = "";
  var followProgress = true;
  var lastFollowedGroup = null;

  var GROUP_ORDER = ["actor", "request", "authority", "current_state", "decision"];
  var GROUP_LABELS = {
    actor: "Actor",
    request: "Request",
    authority: "Authority",
    current_state: "Current state",
    decision: "Decision"
  };
  var EVENT_GROUPS = {
    actor: [
      "agent.discovered",
      "agent.registration_evaluated",
      "agent.identity_evaluated",
      "principal.evaluated"
    ],
    request: ["request.received", "action.evaluated", "tool.evaluated"],
    authority: [
      "resource_data.evaluated",
      "purpose.evaluated",
      "limits.evaluated",
      "delegation.evaluated"
    ],
    current_state: ["posture.evaluated", "context.evaluated"],
    decision: ["decision.produced", "restricted_path.recommended", "audit.completed"]
  };
  var EVENT_LABELS = {
    "request.received": "Request received",
    "agent.discovered": "Agent discovered",
    "agent.registration_evaluated": "Registration evaluated",
    "agent.identity_evaluated": "Identity evaluated",
    "principal.evaluated": "Principal evaluated",
    "action.evaluated": "Action evaluated",
    "tool.evaluated": "Tool evaluated",
    "resource_data.evaluated": "Resource and data evaluated",
    "purpose.evaluated": "Purpose evaluated",
    "limits.evaluated": "Limits evaluated",
    "delegation.evaluated": "Delegation evaluated",
    "posture.evaluated": "Posture evaluated",
    "context.evaluated": "Context evaluated",
    "decision.produced": "Decision produced",
    "restricted_path.recommended": "Restricted path recommended",
    "audit.completed": "Audit completed"
  };
  var EVENT_SHORT_LABELS = {
    "request.received": "Request",
    "agent.discovered": "Agent",
    "agent.registration_evaluated": "Registration",
    "agent.identity_evaluated": "Identity",
    "principal.evaluated": "Principal",
    "action.evaluated": "Action",
    "tool.evaluated": "Tool",
    "resource_data.evaluated": "Resource and data",
    "purpose.evaluated": "Purpose",
    "limits.evaluated": "Limits",
    "delegation.evaluated": "Delegation",
    "posture.evaluated": "Posture",
    "context.evaluated": "Context",
    "decision.produced": "Decision",
    "restricted_path.recommended": "Restricted path",
    "audit.completed": "Audit"
  };
  var RESTRICTED_LABELS = {
    none: "None",
    register_agent: "Register the agent",
    collect_profile: "Collect a trusted profile",
    refresh_posture: "Refresh posture evidence",
    request_human_review: "Request human review",
    request_new_delegation: "Request a new delegation",
    upgrade_version: "Upgrade to an approved version",
    investigate_tool_change: "Investigate the tool change",
    request_consent: "Request human consent",
    context_review: "Review operating context"
  };
  var TAKEAWAY = {
    allow: "Policy approved; execution remains separate.",
    confirm: "Explicit human confirmation required.",
    step_up: "Stronger or fresher assurance required.",
    deny: "Original action stopped."
  };
  var CATEGORY_LABELS = {
    valid_recoverable: "Valid and recoverable",
    delegation_failure: "Delegation failures",
    identity_failure: "Identity failures",
    restricted_recovery: "Restricted recovery",
    profile_posture: "Profile and posture",
    resource_failure: "Resource failures",
    lifecycle_failure: "Lifecycle failures",
    purpose_failure: "Purpose failures"
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

  function humanRestricted(type) {
    return RESTRICTED_LABELS[type] || String(type || "Recovery action").replace(/_/g, " ");
  }

  function humanCategory(category) {
    return CATEGORY_LABELS[category] || String(category || "").replace(/_/g, " ");
  }

  function eventLabel(eventType) {
    return EVENT_LABELS[eventType] || String(eventType || "").replace(/\./g, " · ").replace(/_/g, " ");
  }

  function eventShortLabel(eventType) {
    return EVENT_SHORT_LABELS[eventType] || eventLabel(eventType);
  }

  function clearLiveAnnouncement() {
    lastLiveAnnouncement = "";
    var node = $("guided-live-status");
    if (node) {
      node.textContent = "";
    }
  }

  function announceLive(message) {
    var node = $("guided-live-status");
    if (!node || !message) {
      return;
    }
    if (message === lastLiveAnnouncement) {
      node.textContent = "";
      window.setTimeout(function () {
        node.textContent = message;
        lastLiveAnnouncement = message;
      }, 30);
      return;
    }
    node.textContent = message;
    lastLiveAnnouncement = message;
  }

  function eventBriefSummary(event) {
    if (event.status === "skipped") {
      if (event.skip_reason === "authority_boundary_already_failed") {
        return "authority already failed";
      }
      return event.summary || "skipped";
    }
    var text = (event.fragment && event.fragment.summary) || event.summary || "";
    if (text.length > 96) {
      return text.slice(0, 93) + "...";
    }
    return text;
  }

  function announceEvaluating(event) {
    if (evaluationMode !== "guided" || !event) {
      return;
    }
    announceLive("Evaluating " + eventShortLabel(event.event_type));
  }

  function announceEventFinal(event) {
    if (evaluationMode !== "guided" || !event) {
      return;
    }
    var label = eventShortLabel(event.event_type);
    if (event.event_type === "decision.produced" && lastResult && lastResult.decision) {
      announceLive(
        "Decision: " + String(lastResult.decision).toUpperCase().replace("_", "-")
      );
      return;
    }
    var tone = fragmentTone(event.fragment, event.status);
    if (tone === "skipped") {
      announceLive(label + " skipped: " + eventBriefSummary(event));
      return;
    }
    if (tone === "fail") {
      announceLive(label + " failed: " + eventBriefSummary(event));
      return;
    }
    if (tone === "challenge") {
      announceLive(label + " needs attention: " + eventBriefSummary(event));
      return;
    }
    announceLive(label + " passed");
  }

  function fragmentTone(fragment, status) {
    if (status === "skipped") {
      return "skipped";
    }
    if (!fragment) {
      return "waiting";
    }
    var outcome = String(fragment.outcome || "").toLowerCase();
    if (outcome === "failed" || fragment.hard_authority_failure) {
      return "fail";
    }
    if (outcome === "warning" || outcome === "restricted") {
      return "challenge";
    }
    if (outcome === "skipped") {
      return "skipped";
    }
    return "pass";
  }

  function groupForEventType(eventType) {
    for (var i = 0; i < GROUP_ORDER.length; i++) {
      var groupKey = GROUP_ORDER[i];
      if ((EVENT_GROUPS[groupKey] || []).indexOf(eventType) >= 0) {
        return groupKey;
      }
    }
    return null;
  }

  function groupForEventIndex(index) {
    if (index < 0 || index >= canonicalEvents.length) {
      return null;
    }
    return groupForEventType(canonicalEvents[index].event_type);
  }

  function isElementComfortablyVisible(el) {
    if (!el || !el.getBoundingClientRect) {
      return true;
    }
    var rect = el.getBoundingClientRect();
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var margin = Math.min(96, vh * 0.15);
    return rect.top >= margin && rect.bottom <= vh - margin;
  }

  function updateFollowProgressControl() {
    var wrap = $("follow-progress-wrap");
    if (!wrap) {
      return;
    }
    wrap.hidden = evaluationMode !== "guided";
    var input = $("follow-progress");
    if (input) {
      input.disabled = evaluationMode !== "guided";
    }
  }

  function followActivePhaseIfNeeded() {
    if (!followProgress || evaluationMode !== "guided" || canonicalEvents.length === 0) {
      return;
    }
    var index;
    if (isEvaluating) {
      index = revealedCount;
    } else if (revealedCount > 0) {
      index = revealedCount - 1;
    } else {
      return;
    }
    var groupKey = groupForEventIndex(index);
    if (!groupKey) {
      return;
    }
    if (groupKey === lastFollowedGroup) {
      return;
    }
    lastFollowedGroup = groupKey;
    var stepper = $("live-eval-stepper");
    if (!stepper) {
      return;
    }
    var groupEl = stepper.querySelector(".eval-group[data-group=\"" + groupKey + "\"]");
    if (!groupEl || isElementComfortablyVisible(groupEl)) {
      return;
    }
    var behavior = prefersReducedMotion ? "auto" : "smooth";
    window.requestAnimationFrame(function () {
      groupEl.scrollIntoView({ behavior: behavior, block: "center" });
    });
  }

  function clearRevealTimer() {
    if (revealTimer) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
  }

  function scrollToLiveAuthorityEvaluation() {
    var target = $("live-authority-evaluation");
    var heading = $("live-eval-heading");
    if (!target && !heading) {
      return;
    }
    var scrollBehavior = prefersReducedMotion ? "auto" : "smooth";
    window.requestAnimationFrame(function () {
      var scrollNode = target || heading;
      if (scrollNode && scrollNode.scrollIntoView) {
        scrollNode.scrollIntoView({ behavior: scrollBehavior, block: "start" });
      }
      if (heading) {
        try {
          heading.focus({ preventScroll: true });
        } catch (err) {
          heading.focus();
        }
      }
    });
  }

  function updateGuidedControls() {
    var controls = $("guided-controls");
    if (!controls) {
      return;
    }
    var active = evaluationMode === "guided" && canonicalEvents.length > 0;
    controls.hidden = !active;
    var pauseBtn = $("guided-pause");
    var resumeBtn = $("guided-resume");
    var nextBtn = $("guided-next");
    if (pauseBtn) {
      pauseBtn.hidden =
        !active || isPaused || (revealedCount >= canonicalEvents.length && !isEvaluating);
    }
    if (resumeBtn) {
      resumeBtn.hidden = !active || !isPaused;
    }
    if (nextBtn) {
      nextBtn.hidden = !active;
      nextBtn.disabled =
        revealedCount >= canonicalEvents.length && !isEvaluating;
    }
    updateFollowProgressControl();
  }

  function eventStatusLabel(event, visible, tone, evaluating) {
    if (evaluating) {
      return "Evaluating";
    }
    if (!visible) {
      return "Waiting";
    }
    if (event.status === "skipped" || tone === "skipped") {
      return "Skipped";
    }
    if (tone === "fail") {
      return "Failed";
    }
    if (tone === "challenge") {
      return "Attention";
    }
    if (tone === "pass") {
      return "Passed";
    }
    return "Completed";
  }

  function renderEventNode(event, index, visible, evaluating) {
    var li = document.createElement("li");
    li.className = "eval-event";
    li.setAttribute("data-event-type", event.event_type);
    li.setAttribute("data-index", String(index));
    if (!visible) {
      li.classList.add("is-pending");
    } else {
      li.classList.add("is-visible");
      if (evaluating) {
        li.classList.add("is-evaluating");
        if (evaluationMode === "guided" && !prefersReducedMotion) {
          li.classList.add("is-entering");
        }
      } else {
        var tone = fragmentTone(event.fragment, event.status);
        li.classList.add("is-" + tone);
        if (
          index === revealedCount - 1 &&
          evaluationMode === "guided" &&
          !prefersReducedMotion &&
          !isEvaluating
        ) {
          li.classList.add("is-entering");
        }
      }
    }

    var toneForStatus = evaluating
      ? "evaluating"
      : visible
        ? fragmentTone(event.fragment, event.status)
        : "waiting";

    var title = document.createElement("p");
    title.className = "eval-event-title";
    title.textContent = eventLabel(event.event_type);

    var status = document.createElement("p");
    status.className = "eval-event-status";
    status.textContent = eventStatusLabel(event, visible, toneForStatus, evaluating);

    var copy = document.createElement("p");
    copy.className = "eval-event-copy";
    if (!visible) {
      copy.textContent = "Awaiting evaluation.";
    } else if (evaluating) {
      copy.textContent = "Checking policy evidence.";
    } else if (event.status === "skipped") {
      copy.textContent =
        event.skip_reason === "authority_boundary_already_failed"
          ? "Skipped because authority already failed."
          : event.summary || "Stage skipped.";
    } else {
      copy.textContent = (event.fragment && event.fragment.summary) || event.summary || "";
    }

    li.appendChild(title);
    li.appendChild(status);
    li.appendChild(copy);
    return li;
  }

  function renderStepper() {
    var stepper = $("live-eval-stepper");
    if (!stepper) {
      return;
    }
    stepper.innerHTML = "";
    var eventsByType = {};
    canonicalEvents.forEach(function (event, index) {
      eventsByType[event.event_type] = { event: event, index: index };
    });

    GROUP_ORDER.forEach(function (groupKey) {
      var types = EVENT_GROUPS[groupKey] || [];
      var groupLi = document.createElement("li");
      groupLi.className = "eval-group";
      groupLi.setAttribute("data-group", groupKey);

      var heading = document.createElement("h3");
      heading.className = "eval-group-title";
      heading.textContent = GROUP_LABELS[groupKey] || groupKey;

      var eventList = document.createElement("ol");
      eventList.className = "eval-events";

      types.forEach(function (eventType) {
        var entry = eventsByType[eventType];
        if (!entry) {
          return;
        }
        var visible = entry.index < revealedCount;
        var evaluating =
          evaluationMode === "guided" &&
          isEvaluating &&
          entry.index === revealedCount;
        eventList.appendChild(
          renderEventNode(entry.event, entry.index, visible || evaluating, evaluating)
        );
      });

      if (eventList.children.length) {
        groupLi.appendChild(heading);
        groupLi.appendChild(eventList);
        stepper.appendChild(groupLi);
      }
    });
    updateGuidedControls();
    updateFollowProgressControl();
  }

  function resetStepper() {
    clearRevealTimer();
    revealedCount = 0;
    isPaused = false;
    isEvaluating = false;
    canonicalEvents = [];
    lastFollowedGroup = null;
    clearLiveAnnouncement();
    renderStepper();
    setText("stepper-hint", "Select a scenario and run evaluation.");
  }

  function finalizeCurrentEvent(scheduleNext) {
    if (!isEvaluating) {
      updateGuidedControls();
      return;
    }
    var event = canonicalEvents[revealedCount];
    isEvaluating = false;
    revealedCount += 1;
    renderStepper();
    if (event) {
      announceEventFinal(event);
    }
    updateGuidedControls();
    if (
      scheduleNext &&
      !isPaused &&
      evaluationMode === "guided" &&
      revealedCount < canonicalEvents.length
    ) {
      revealTimer = window.setTimeout(beginEvaluatingEvent, REVEAL_MS - EVALUATING_MS);
    }
  }

  function beginEvaluatingEvent() {
    if (
      evaluationMode !== "guided" ||
      revealedCount >= canonicalEvents.length ||
      isEvaluating
    ) {
      updateGuidedControls();
      return;
    }
    isEvaluating = true;
    renderStepper();
    announceEvaluating(canonicalEvents[revealedCount]);
    followActivePhaseIfNeeded();
    updateGuidedControls();
    if (!isPaused && !prefersReducedMotion) {
      revealTimer = window.setTimeout(function () {
        finalizeCurrentEvent(true);
      }, EVALUATING_MS);
    }
  }

  function guidedNext() {
    clearRevealTimer();
    if (isEvaluating) {
      finalizeCurrentEvent(!isPaused);
      if (!isPaused && revealedCount < canonicalEvents.length) {
        beginEvaluatingEvent();
      }
      return;
    }
    if (revealedCount < canonicalEvents.length) {
      beginEvaluatingEvent();
    }
  }

  function scheduleReveal() {
    beginEvaluatingEvent();
  }

  function startReveal() {
    clearRevealTimer();
    isPaused = false;
    isEvaluating = false;
    if (prefersReducedMotion || evaluationMode === "instant") {
      revealedCount = canonicalEvents.length;
      renderStepper();
      updateGuidedControls();
      return;
    }
    if (revealedCount >= canonicalEvents.length) {
      revealedCount = 0;
    }
    beginEvaluatingEvent();
  }

  function pauseReveal() {
    isPaused = true;
    clearRevealTimer();
    updateGuidedControls();
    updateFollowProgressControl();
  }

  function resumeReveal() {
    isPaused = false;
    updateGuidedControls();
    if (evaluationMode !== "guided") {
      return;
    }
    if (isEvaluating) {
      revealTimer = window.setTimeout(function () {
        finalizeCurrentEvent(true);
      }, EVALUATING_MS);
      return;
    }
    if (revealedCount < canonicalEvents.length) {
      beginEvaluatingEvent();
    }
  }

  function replayReveal() {
    revealedCount = 0;
    isPaused = false;
    isEvaluating = false;
    lastFollowedGroup = null;
    clearLiveAnnouncement();
    renderStepper();
    scrollToLiveAuthorityEvaluation();
    startReveal();
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

    track("lab_preset_selected", {
      lab_id: LAB_ID,
      scenario_category: selectedCategory,
      preset_id: scenarioId
    });
    loadSummary(scenarioId);
    resetStepper();
  }

  function loadSummary(scenarioId) {
    var meta = scenariosById[scenarioId] || {};
    setText("sum-action", meta._action);
    setText("sum-tool", meta._tool);
    setText("sum-resource", meta._resource);
    setText("sum-classification", meta._classification);
    setText("sum-amount", meta._amount);
    setText("sum-purpose", meta._purpose);
    setText("sum-time", meta._time);
    setText("sum-agent", meta._agent);
    setText("sum-principal", meta._principal);
    setText("sum-registration", meta._registration);
    setText("mgmt-agent", meta._agent);
    setText("mgmt-principal", meta._principal);
    setText("mgmt-classification", meta._mgmtClass);
    setText("mgmt-registration", meta._registration);
    setText("mgmt-status", meta._mgmtStatus);
    var pre = $("request-json");
    if (pre) {
      pre.textContent = JSON.stringify({ scenario_id: scenarioId }, null, 2);
    }
  }

  function renderDecision(data) {
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
    html += '<ul class="result-primary">';
    html += "<li><strong>Execution:</strong> not performed</li>";
    html += "<li><strong>Restricted path:</strong> " +
      (data.restricted && data.restricted.available
        ? humanRestricted(data.restricted.restricted_type)
        : "None") +
      "</li>";
    html += "</ul>";
    root.innerHTML = html;
  }

  function renderEvidence(data) {
    var panel = $("evidence-panel");
    if (!panel) {
      return;
    }
    var profile = data.profile_summary || {};
    var posture = data.posture_summary || {};
    panel.innerHTML =
      "<details class=\"tech-details\" open>" +
      "<summary>Technical evidence</summary>" +
      "<ul>" +
      "<li><strong>Reason code:</strong> " + (data.reason_code || "") + "</li>" +
      "<li><strong>Reason category:</strong> " + (data.reason_category || "") + "</li>" +
      "<li><strong>Violated constraint:</strong> " + (data.violated_constraint || "none") + "</li>" +
      "<li><strong>Delegation path:</strong> " + (data.delegation_path || []).join(" → ") + "</li>" +
      "<li><strong>Profile:</strong> " + (profile.classification || "") +
      " · confidence " + (profile.confidence || "") +
      (profile.profile_mismatch ? " · mismatch" : "") + "</li>" +
      "<li><strong>Posture:</strong> " + (posture.status || "") +
      " · evidence " + (posture.evidence_freshness || "") + "</li>" +
      "<li><strong>Policy version:</strong> " + (data.policy_version || "n/a") + "</li>" +
      "<li><strong>Request fingerprint:</strong> " + (data.request_fingerprint || "n/a") + "</li>" +
      "</ul></details>";
  }

  function renderAudit(data) {
    var panel = $("audit-panel");
    if (!panel) {
      return;
    }
    panel.innerHTML =
      "<dl class=\"input-summary audit-summary\">" +
      "<div><dt>Audit ID</dt><dd>" + (data.audit_id || "—") + "</dd></div>" +
      "<div><dt>Evaluated at</dt><dd>" + (data.evaluated_at || "—") + "</dd></div>" +
      "<div><dt>Decision valid until</dt><dd>" + (data.decision_valid_until || "n/a") + "</dd></div>" +
      "<div><dt>Chain version</dt><dd>" + (data.chain_version || "n/a") + "</dd></div>" +
      "<div><dt>Profile version</dt><dd>" + (data.profile_version || "n/a") + "</dd></div>" +
      "<div><dt>Posture version</dt><dd>" + (data.posture_version || "n/a") + "</dd></div>" +
      "</dl>";
  }

  function renderRestricted(data) {
    var section = $("restricted-section");
    var panel = $("restricted-panel");
    if (!section || !panel) {
      return;
    }
    if (data.restricted && data.restricted.available) {
      section.hidden = false;
      var rec = data.restricted;
      panel.innerHTML =
        "<p><strong>Recovery path:</strong> " + humanRestricted(rec.restricted_type) + "</p>" +
        "<p>" + (rec.explanation || "") + "</p>" +
        "<p class=\"fallback-invariants\" role=\"note\">" +
        "The original decision remains unchanged. Restricted recovery does not execute the protected action. " +
        "New evaluation required.</p>";
    } else {
      section.hidden = true;
      panel.innerHTML = "";
    }
    var preview = $("restricted-preview");
    if (preview) {
      preview.hidden = true;
      preview.innerHTML = "";
    }
  }

  function updateManagementFromResult(data) {
    var regEvent = (data.events || []).find(function (e) {
      return e.event_type === "agent.registration_evaluated" && e.fragment;
    });
    if (regEvent && regEvent.fragment && regEvent.fragment.details) {
      var state = regEvent.fragment.details.registration_state;
      if (state) {
        setText("mgmt-registration", String(state));
        setText("sum-registration", String(state));
      }
    }
    if (data.profile_summary && data.profile_summary.classification) {
      setText("mgmt-classification", data.profile_summary.classification);
    }
  }

  function renderResult(data) {
    lastResult = data;
    canonicalEvents = data.events || [];
    revealedCount = 0;
    isPaused = false;
    isEvaluating = false;
    lastFollowedGroup = null;
    clearLiveAnnouncement();
    renderDecision(data);
    renderEvidence(data);
    renderAudit(data);
    renderRestricted(data);
    updateManagementFromResult(data);
    setText(
      "stepper-hint",
      evaluationMode === "guided"
        ? "Guided mode: events reveal in canonical server order."
        : "Instant mode: all events shown immediately."
    );
    startReveal();
  }

  function evaluate() {
    if (!selectedId) {
      return;
    }
    var evalBtn = $("evaluate-btn");
    if (evalBtn) {
      evalBtn.disabled = true;
    }
    setText("stepper-hint", "Evaluating…");
    fetch("/api/labs/003/evaluate", {
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
        if (evalBtn) {
          evalBtn.disabled = !selectedId;
        }
        if (!payload.ok) {
          var root = $("result");
          if (root) {
            root.innerHTML =
              '<p class="decision decision-deny"><span class="decision-label">ERROR</span></p>' +
              "<p>Evaluation could not be completed.</p>";
          }
          resetStepper();
          return;
        }
        renderResult(payload.body);
        scrollToLiveAuthorityEvaluation();
        track("policy_evaluation_completed", {
          lab_id: LAB_ID,
          scenario_category: selectedCategory,
          evaluation_mode: evaluationMode,
          decision: payload.body.decision,
          reason_category: payload.body.reason_category,
          fallback_available: !!(payload.body.restricted && payload.body.restricted.available)
        });
      })
      .catch(function () {
        if (evalBtn) {
          evalBtn.disabled = !selectedId;
        }
        var root = $("result");
        if (root) {
          root.innerHTML =
            '<p class="decision decision-deny"><span class="decision-label">ERROR</span></p>' +
            "<p>Network error.</p>";
        }
        resetStepper();
      });
  }

  function previewRestricted() {
    if (!lastResult || !lastResult.restricted || !lastResult.restricted.available) {
      return;
    }
    var rec = lastResult.restricted;
    var node = $("restricted-preview");
    if (!node) {
      return;
    }
    var recovery = humanRestricted(rec.restricted_type);
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
      '<p class="fallback-note">The original decision remains unchanged.</p>' +
      '<p class="fallback-note">Restricted recovery does not execute the protected action.</p>' +
      '<p class="fallback-note">New evaluation required.</p>' +
      '<details class="tech-details"><summary>Technical details</summary><ul>' +
      "<li>Restricted type: " + (rec.restricted_type || "") + "</li>" +
      "<li>Permitted: " + (rec.permitted_operations || []).join(", ") + "</li>" +
      "<li>Prohibited: " + (rec.prohibited_operations || []).join(", ") + "</li>" +
      "</ul></details>";
    track("fallback_previewed", {
      lab_id: LAB_ID,
      decision: lastResult.decision,
      fallback_type: rec.restricted_type
    });
  }

  var SCENARIO_SUMMARIES = {
    managed_public_data_read: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-001", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    sensitive_action_consent: {
      action: "propose", tool: "document_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "portfolio analysis",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-sensitive", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    stale_runtime_attestation: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-stale", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    unapproved_model: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-version", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    undelegated_capability: {
      action: "execute", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-undelegated", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    unknown_agent_protected_tool: {
      action: "read", tool: "order_gateway", resource: "cedar-quill-public-research",
      classification: "public", amount: "100.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-unknown-agent-999", principal: "cq-principal-001",
      registration: "unknown", mgmtClass: "unknown", mgmtStatus: "unknown"
    },
    unknown_agent_registration: {
      action: "register", tool: "registration_portal", resource: "agent-registration-catalog",
      classification: "public", amount: "0.00", purpose: "agent onboarding",
      time: "2026-03-15T14:00:00Z", agent: "cq-unknown-agent-888", principal: "cq-principal-001",
      registration: "unknown", mgmtClass: "unknown", mgmtStatus: "restricted onboarding"
    },
    undeclared_tool: {
      action: "read", tool: "shadow_scraper", resource: "cedar-quill-public-research",
      classification: "public", amount: "200.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-tools", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    data_boundary_violation: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-confidential-positions",
      classification: "confidential", amount: "200.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-boundary", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    parent_delegation_expired: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "100.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-001", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    parent_delegation_revoked: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "100.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-001", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    purpose_conflict: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "200.00", purpose: "portfolio analysis",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-purpose", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    limit_requires_confirmation: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "7500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-limit", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    },
    material_context_change: {
      action: "read", tool: "market_feed_reader", resource: "cedar-quill-public-research",
      classification: "public", amount: "500.00", purpose: "market research",
      time: "2026-03-15T14:00:00Z", agent: "cq-research-agent-context", principal: "cq-principal-001",
      registration: "registered", mgmtClass: "Research Agent", mgmtStatus: "active"
    }
  };

  function hydrateScenarioMeta(list) {
    (list || []).forEach(function (item) {
      var extra = SCENARIO_SUMMARIES[item.id] || {};
      item._action = extra.action;
      item._tool = extra.tool;
      item._resource = extra.resource;
      item._classification = extra.classification;
      item._amount = extra.amount;
      item._purpose = extra.purpose;
      item._time = extra.time;
      item._agent = extra.agent;
      item._principal = extra.principal;
      item._registration = extra.registration;
      item._mgmtClass = extra.mgmtClass;
      item._mgmtStatus = extra.mgmtStatus;
      scenariosById[item.id] = item;
    });
    Object.keys(SCENARIO_SUMMARIES).forEach(function (id) {
      if (!scenariosById[id]) {
        var extra = SCENARIO_SUMMARIES[id];
        scenariosById[id] = {
          id: id,
          _action: extra.action,
          _tool: extra.tool,
          _resource: extra.resource,
          _classification: extra.classification,
          _amount: extra.amount,
          _purpose: extra.purpose,
          _time: extra.time,
          _agent: extra.agent,
          _principal: extra.principal,
          _registration: extra.registration,
          _mgmtClass: extra.mgmtClass,
          _mgmtStatus: extra.mgmtStatus
        };
      }
    });
  }

  function setEvaluationMode(mode) {
    evaluationMode = mode === "instant" ? "instant" : "guided";
    document.querySelectorAll('input[name="eval-mode"]').forEach(function (input) {
      input.checked = input.value === evaluationMode;
    });
    if (lastResult && canonicalEvents.length) {
      startReveal();
    }
    updateGuidedControls();
    updateFollowProgressControl();
  }

  function init() {
    prefersReducedMotion =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    track("lab_opened", { lab_id: LAB_ID, lab_slug: LAB_SLUG });
    hydrateScenarioMeta([]);

    fetch("/api/labs/003/scenarios", { headers: { Accept: "application/json" } })
      .then(function (response) { return response.json(); })
      .then(function (list) { hydrateScenarioMeta(list || []); })
      .catch(function () { return; });

    document.querySelectorAll(".preset-card").forEach(function (btn) {
      btn.addEventListener("click", function () {
        selectScenario(btn);
      });
    });

    document.querySelectorAll('input[name="eval-mode"]').forEach(function (input) {
      input.addEventListener("change", function () {
        if (input.checked) {
          setEvaluationMode(input.value);
        }
      });
    });

    var followInput = $("follow-progress");
    if (followInput) {
      followInput.checked = followProgress;
      followInput.addEventListener("change", function () {
        followProgress = followInput.checked;
        if (followProgress && evaluationMode === "guided" && canonicalEvents.length) {
          lastFollowedGroup = null;
          followActivePhaseIfNeeded();
        }
      });
    }

    var evalBtn = $("evaluate-btn");
    if (evalBtn) {
      evalBtn.addEventListener("click", evaluate);
    }
    var pauseBtn = $("guided-pause");
    if (pauseBtn) {
      pauseBtn.addEventListener("click", pauseReveal);
    }
    var resumeBtn = $("guided-resume");
    if (resumeBtn) {
      resumeBtn.addEventListener("click", resumeReveal);
    }
    var nextBtn = $("guided-next");
    if (nextBtn) {
      nextBtn.addEventListener("click", guidedNext);
    }
    var replayBtn = $("guided-replay");
    if (replayBtn) {
      replayBtn.addEventListener("click", replayReveal);
    }
    var resetBtn = $("guided-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", resetStepper);
    }
    var previewBtn = $("preview-restricted");
    if (previewBtn) {
      previewBtn.addEventListener("click", previewRestricted);
    }

    document
      .querySelectorAll(
        '#architecture img[data-analytics-destination="architecture"], .lab003-nac img[data-analytics-destination="architecture"]'
      )
      .forEach(function (arch) {
        arch.addEventListener("click", function () {
          track("architecture_viewed", {
            lab_id: LAB_ID,
            architecture_type: arch.getAttribute("data-architecture-type") || "lab003"
          });
        });
      });

    renderStepper();
    updateFollowProgressControl();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
