"""Optional privacy-conscious PostHog analytics. Disabled unless configured."""

from __future__ import annotations

from typing import Any, Dict, FrozenSet

from from_my_desk.config import Settings

BLOCKED_HOSTS: FrozenSet[str] = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "testserver",
        "0.0.0.0",
    }
)

BASE_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def posthog_assets_origin(api_host: str) -> str:
    """Official JS is served from the PostHog assets host derived from api_host."""
    origin = (api_host or "").strip().rstrip("/")
    if ".i.posthog.com" in origin:
        return origin.replace(".i.posthog.com", "-assets.i.posthog.com")
    return origin


def posthog_sdk_src(api_host: str) -> str:
    return posthog_assets_origin(api_host) + "/static/array.js"


def hostname_is_blocked(host: str) -> bool:
    hostname = (host or "").split(":")[0].lower().strip("[]")
    return hostname in BLOCKED_HOSTS


def telemetry_enabled_for_request(settings: Settings, host: str) -> bool:
    if not settings.posthog_enabled:
        return False
    if not settings.posthog_key:
        return False
    if hostname_is_blocked(host):
        return False
    return True


def public_telemetry_config(settings: Settings, host: str) -> Dict[str, Any]:
    """JSON passed to pages. Token is the public client project token only."""
    if not telemetry_enabled_for_request(settings, host):
        return {"enabled": False}
    api_host = settings.posthog_host
    return {
        "enabled": True,
        "key": settings.posthog_key,
        "host": api_host,
        "sdk_src": posthog_sdk_src(api_host),
        "capture_pageview": False,
        "capture_pageleave": True,
        "autocapture": False,
        "disable_session_recording": True,
        "person_profiles": "identified_only",
        "persistence": "localStorage+cookie",
        "respect_dnt": True,
    }


def content_security_policy(settings: Settings, host: str) -> str:
    script_src = ["'self'"]
    connect_src = ["'self'"]
    extra = ""
    if telemetry_enabled_for_request(settings, host):
        # PostHog hosts rotate; a narrow origin list silently drops capture.
        # https://posthog.com/docs/libraries/js
        for origin in ("https://*.i.posthog.com", "https://*.posthog.com"):
            script_src.append(origin)
            connect_src.append(origin)
        extra = "worker-src 'self' blob: data:; "
    return (
        "default-src 'self'; "
        "script-src {0}; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src {1}; "
        "{2}"
        "base-uri 'self'; "
        "form-action 'self'".format(" ".join(script_src), " ".join(connect_src), extra)
    )


def security_headers_for_request(settings: Settings, host: str) -> Dict[str, str]:
    headers = dict(BASE_SECURITY_HEADERS)
    headers["Content-Security-Policy"] = content_security_policy(settings, host)
    return headers
