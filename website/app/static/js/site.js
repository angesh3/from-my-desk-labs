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

  function track(eventName, properties) {
    var cfg = telemetryConfig();
    if (!cfg || !cfg.enabled) {
      return;
    }
    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(eventName, properties || {});
      }
    } catch (err) {
      return;
    }
  }

  window.FromMyDesk = {
    track: track,
    telemetryConfig: telemetryConfig
  };

  function init() {
    var path = window.location.pathname;
    if (path === "/") {
      track("page_viewed", { page_path: "/" });
    } else if (path === "/labs") {
      track("page_viewed", { page_path: "/labs" });
    } else if (path.indexOf("/labs/") === 0) {
      track("page_viewed", { page_path: path });
    }

    document.querySelectorAll('a[href*="github.com"]').forEach(function (link) {
      link.addEventListener("click", function () {
        track("github_link_clicked", { page_path: path });
      });
    });
    document.querySelectorAll('a[href*="linkedin.com"]').forEach(function (link) {
      link.addEventListener("click", function () {
        track("newsletter_link_clicked", { page_path: path });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
