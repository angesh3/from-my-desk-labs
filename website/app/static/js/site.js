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

  function sdkSrc(cfg) {
    if (cfg.sdk_src) {
      return cfg.sdk_src;
    }
    if (!cfg.host) {
      return "";
    }
    return String(cfg.host).replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js";
  }

  function initPosthog(cfg) {
    if (!cfg || !cfg.enabled || !cfg.key) {
      return;
    }
    if (!window.posthog || typeof window.posthog.init !== "function") {
      return;
    }
    if (window.__fromMyDeskPosthogReady) {
      return;
    }
    try {
      window.posthog.init(cfg.key, {
        api_host: cfg.host,
        capture_pageview: true,
        capture_pageleave: true,
        autocapture: false,
        disable_session_recording: true,
        person_profiles: "identified_only",
        persistence: "localStorage+cookie",
        respect_dnt: true
      });
      window.__fromMyDeskPosthogReady = true;
    } catch (err) {
      return;
    }
  }

  function loadOfficialSdk(cfg) {
    if (!cfg || !cfg.enabled || !cfg.key) {
      return;
    }
    try {
      if (window.posthog && typeof window.posthog.init === "function") {
        initPosthog(cfg);
        return;
      }
      var src = sdkSrc(cfg);
      if (!src) {
        return;
      }
      var existing = document.querySelector('script[src="' + src.replace(/"/g, "") + '"]');
      if (existing) {
        existing.addEventListener("load", function () {
          initPosthog(cfg);
        });
        return;
      }
      var script = document.createElement("script");
      script.async = true;
      script.crossOrigin = "anonymous";
      script.src = src;
      script.onload = function () {
        initPosthog(cfg);
      };
      script.onerror = function () {
        return;
      };
      document.head.appendChild(script);
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
