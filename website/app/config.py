"""Global website settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

APP_VERSION = "0.3.0"
APP_NAME = "from-my-desk"

REPO_ROOT = Path(__file__).resolve().parents[2]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.app_version = APP_VERSION
        self.policy_dir = Path(
            os.environ.get("POLICY_DIR")
            or (REPO_ROOT / "labs" / "001-know-your-agent" / "policies")
        )
        self.catalog_path = Path(
            os.environ.get("CATALOG_PATH") or (REPO_ROOT / "website" / "catalog" / "labs.yaml")
        )
        self.lab_static_dir = Path(
            os.environ.get("LAB_STATIC_DIR")
            or (REPO_ROOT / "labs" / "001-know-your-agent" / "static")
        )
        self.port = int(os.environ.get("PORT", "8080"))
        self.registry_mode = os.environ.get("REGISTRY_PUBLIC", "sanitized").strip().lower()
        self.github_url = os.environ.get(
            "PUBLIC_GITHUB_URL",
            "https://github.com/angesh3/from-my-desk-labs",
        )
        self.newsletter_url = os.environ.get(
            "PUBLIC_NEWSLETTER_URL",
            "https://www.linkedin.com/newsletters/from-my-desk-7492634647890341890/",
        )
        self.public_base_url = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
        self.posthog_enabled = _bool_env("POSTHOG_ENABLED", False)
        self.posthog_project_token = os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
        self.posthog_host = os.environ.get(
            "POSTHOG_HOST", "https://us.i.posthog.com"
        ).rstrip("/")
        self.rate_limit_per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
