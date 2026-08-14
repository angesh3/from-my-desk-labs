"""Optional privacy-conscious product telemetry. Disabled unless configured."""

from __future__ import annotations

from typing import Any, Dict

from from_my_desk.config import Settings


def telemetry_enabled_for_request(settings: Settings, host: str, is_test: bool) -> bool:
    if is_test:
        return False
    if not settings.posthog_enabled:
        return False
    if not settings.posthog_project_token:
        return False
    hostname = (host or "").split(":")[0].lower()
    if hostname in {"localhost", "127.0.0.1", "::1", "testserver"}:
        return False
    return True


def public_telemetry_config(
    settings: Settings, host: str, is_test: bool = False
) -> Dict[str, Any]:
    enabled = telemetry_enabled_for_request(settings, host, is_test)
    if not enabled:
        return {"enabled": False}
    return {
        "enabled": True,
        "token": settings.posthog_project_token,
        "host": settings.posthog_host,
        "cookieless": True,
        "disable_session_recording": True,
        "autocapture": False,
        "person_profiles": "never",
    }
