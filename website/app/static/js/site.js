(function () {
  "use strict";

  function telemetryConfig() {
    var node = document.getElementById("telemetry-config");
    if (!node) {
      return { enabled: false };
    }
    try {
      return JSON.parse(node.textContent || "{}");
    } catch (err) {
      return { enabled: false };
    }
  }

  function pageType(pathname) {
    var path = pathname || window.location.pathname;
    if (path === "/") {
      return "home";
    }
    if (path === "/labs") {
      return "labs_index";
    }
    if (path.indexOf("/labs/") === 0) {
      return "lab";
    }
    return null;
  }

  function destinationForAnchor(href) {
    var url;
    try {
      url = new URL(href, window.location.origin);
    } catch (err) {
      return null;
    }
    var host = (url.hostname || "").toLowerCase();
    if (host === "github.com" || host.slice(-11) === ".github.com") {
      return "github";
    }
    if (host === "linkedin.com" || host.slice(-13) === ".linkedin.com") {
      return "linkedin_newsletter";
    }
    if (url.hash === "#architecture") {
      return "architecture";
    }
    return null;
  }

  function safeProperties(properties) {
    var allowed = {
      lab_id: true,
      preset_category: true,
      decision: true,
      reason_category: true,
      destination: true,
      page_type: true
    };
    var out = {};
    var key;
    if (!properties) {
      return out;
    }
    for (key in properties) {
      if (Object.prototype.hasOwnProperty.call(properties, key) && allowed[key]) {
        out[key] = properties[key];
      }
    }
    return out;
  }

  function track(eventName, properties) {
    var cfg = telemetryConfig();
    if (!cfg || !cfg.enabled) {
      return;
    }
    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(eventName, safeProperties(properties));
      }
    } catch (err) {
      return;
    }
  }

  function capturePageviewOnce(posthog) {
    if (window.__fromMyDeskPageviewSent) {
      return;
    }
    var client = posthog || window.posthog;
    if (!client || typeof client.capture !== "function") {
      return;
    }
    try {
      window.__fromMyDeskPageviewSent = true;
      client.capture("$pageview", {
        "$current_url": window.location.href,
        "$pathname": window.location.pathname,
        "page_title": document.title
      });
    } catch (err) {
      window.__fromMyDeskPageviewSent = false;
    }
  }

  function installOfficialStub() {
    if (window.posthog && window.posthog.__SV) {
      return;
    }
    /* Official PostHog snippet (https://posthog.com/docs/libraries/js). Queues
       capture/init, then loads array.js. site.js is first-party so CSP stays
       script-src 'self' plus PostHog hosts. */
    (function (t, e) {
      var o, n, p, r;
      if (e.__SV) {
        return;
      }
      window.posthog = e;
      e._i = [];
      e.init = function (i, s, a) {
        function g(t, e) {
          var o = e.split(".");
          if (2 === o.length) {
            t = t[o[0]];
            e = o[1];
          }
          t[e] = function () {
            t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
          };
        }
        p = t.createElement("script");
        p.type = "text/javascript";
        p.crossOrigin = "anonymous";
        p.async = true;
        p.src = s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js";
        r = t.getElementsByTagName("script")[0];
        r.parentNode.insertBefore(p, r);
        var u = e;
        if (void 0 !== a) {
          u = e[a] = [];
        } else {
          a = "posthog";
        }
        u.people = u.people || [];
        u.toString = function (t) {
          var e = "posthog";
          return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e;
        };
        u.people.toString = function () {
          return u.toString(1) + ".people (stub)";
        };
        o = "init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagResult isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" ");
        for (n = 0; n < o.length; n++) {
          g(u, o[n]);
        }
        e._i.push([i, s, a]);
      };
      e.__SV = 1;
    })(document, window.posthog || []);
  }

  function initPosthog(cfg) {
    if (!cfg || !cfg.enabled || !cfg.key) {
      return;
    }
    if (window.__fromMyDeskPosthogReady) {
      return;
    }
    try {
      installOfficialStub();
      if (!window.posthog || typeof window.posthog.init !== "function") {
        return;
      }
      window.__fromMyDeskPosthogReady = true;
      window.posthog.init(cfg.key, {
        api_host: cfg.host,
        defaults: "2026-05-30",
        capture_pageview: false,
        capture_pageleave: true,
        autocapture: false,
        disable_session_recording: true,
        person_profiles: "identified_only",
        persistence: "localStorage+cookie",
        respect_dnt: true,
        loaded: function (posthog) {
          capturePageviewOnce(posthog);
        }
      });
    } catch (err) {
      window.__fromMyDeskPosthogReady = false;
    }
  }

  function loadOfficialSdk(cfg) {
    if (!cfg || !cfg.enabled || !cfg.key) {
      return;
    }
    try {
      initPosthog(cfg);
    } catch (err) {
      return;
    }
  }

  window.FromMyDesk = {
    track: track,
    telemetryConfig: telemetryConfig,
    pageType: pageType
  };

  function initOutboundClicks() {
    document.addEventListener("click", function (event) {
      var page = pageType();
      if (!page) {
        return;
      }
      var node = event.target;
      if (!node || !node.closest) {
        return;
      }
      var arch = node.closest("#architecture, [data-analytics-destination=\"architecture\"]");
      if (arch) {
        track("outbound_link_clicked", { destination: "architecture", page_type: page });
        return;
      }
      var link = node.closest("a[href]");
      if (!link) {
        return;
      }
      var dest = destinationForAnchor(link.getAttribute("href"));
      if (!dest) {
        return;
      }
      track("outbound_link_clicked", { destination: dest, page_type: page });
    });
  }

  function init() {
    loadOfficialSdk(telemetryConfig());
    initOutboundClicks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
