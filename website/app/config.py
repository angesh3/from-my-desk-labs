"""Global website settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

APP_VERSION = "0.3.0"
APP_NAME = "from-my-desk"

PACKAGE_DIR = Path(__file__).resolve().parent


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _source_repo_root() -> Path | None:
    """Return the git repo root when running from the source / editable layout."""
    if PACKAGE_DIR.name == "app" and PACKAGE_DIR.parent.name == "website":
        root = PACKAGE_DIR.parents[1]
        if (root / "website" / "catalog" / "labs.yaml").is_file():
            return root
    return None


def _default_website_template_dir() -> Path:
    root = _source_repo_root()
    if root is not None:
        return root / "website" / "app" / "templates"
    return PACKAGE_DIR / "templates"


def _default_website_static_dir() -> Path:
    root = _source_repo_root()
    if root is not None:
        return root / "website" / "app" / "static"
    return PACKAGE_DIR / "static"


def _default_catalog_path() -> Path:
    root = _source_repo_root()
    if root is not None:
        return root / "website" / "catalog" / "labs.yaml"
    return PACKAGE_DIR / "catalog" / "labs.yaml"


def _default_lab_static_dir() -> Path:
    root = _source_repo_root()
    if root is not None:
        return root / "labs" / "001-know-your-agent" / "static"
    return Path("/srv/labs/001-know-your-agent/static")


def _default_policy_dir() -> Path:
    root = _source_repo_root()
    if root is not None:
        return root / "labs" / "001-know-your-agent" / "policies"
    return Path("/srv/labs/001-know-your-agent/policies")


class Settings:
    def __init__(self) -> None:
        self.app_version = APP_VERSION
        self.website_template_dir = Path(
            os.environ.get("WEBSITE_TEMPLATE_DIR") or _default_website_template_dir()
        )
        self.website_static_dir = Path(
            os.environ.get("WEBSITE_STATIC_DIR") or _default_website_static_dir()
        )
        self.lab_static_dir = Path(
            os.environ.get("LAB_STATIC_DIR") or _default_lab_static_dir()
        )
        self.catalog_path = Path(
            os.environ.get("CATALOG_PATH") or _default_catalog_path()
        )
        self.policy_dir = Path(
            os.environ.get("POLICY_DIR") or _default_policy_dir()
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
        # POSTHOG_KEY is the public client project token, not a Personal API key.
        self.posthog_key = (
            os.environ.get("POSTHOG_KEY", "").strip()
            or os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
        )
        self.posthog_host = os.environ.get(
            "POSTHOG_HOST", "https://us.i.posthog.com"
        ).rstrip("/")
        self.rate_limit_per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))


REQUIRED_TEMPLATE_FILES = ("base.html", "home.html", "labs.html", "lab.html")
REQUIRED_GLOBAL_STATIC_FILES = (
    "css/styles.css",
    "js/site.js",
    "brand/from-my-desk-logo.webp",
    "brand/favicon.png",
)
REQUIRED_LAB_STATIC_FILES = (
    "architecture.svg",
    "know-your-agent-trust-workflow.gif",
)
REQUIRED_POLICY_FILES = ("desk-policy.yaml", "agent-registry.yaml")


class ResourceConfigError(RuntimeError):
    """Raised when a required production resource path is missing."""


def validate_runtime_resources(settings: Settings) -> None:
    """Fail startup if templates, static assets, catalog, or policies are missing."""
    missing: list[str] = []

    for name in REQUIRED_TEMPLATE_FILES:
        path = settings.website_template_dir / name
        if not path.is_file():
            missing.append(f"template:{name}")

    for rel in REQUIRED_GLOBAL_STATIC_FILES:
        path = settings.website_static_dir / rel
        if not path.is_file():
            missing.append(f"static:{rel}")

    for rel in REQUIRED_LAB_STATIC_FILES:
        path = settings.lab_static_dir / rel
        if not path.is_file():
            missing.append(f"lab_static:{rel}")

    if not settings.catalog_path.is_file():
        missing.append("catalog:labs.yaml")

    for name in REQUIRED_POLICY_FILES:
        path = settings.policy_dir / name
        if not path.is_file():
            missing.append(f"policy:{name}")

    if missing:
        raise ResourceConfigError(
            "Refusing to start: required website resources are missing: "
            + ", ".join(missing)
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
