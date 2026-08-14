"""Runtime path configuration, route order, and resource validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from starlette.routing import Mount

from from_my_desk.config import (
    ResourceConfigError,
    Settings,
    reset_settings_cache,
    validate_runtime_resources,
)
from from_my_desk.main import app, iter_route_table


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_settings_honor_explicit_env_paths(monkeypatch, tmp_path):
    template_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    lab_static = tmp_path / "lab-static"
    catalog = tmp_path / "labs.yaml"
    policy_dir = tmp_path / "policies"
    for path in (template_dir, static_dir, lab_static, policy_dir):
        path.mkdir()
    catalog.write_text("labs: []\n", encoding="utf-8")

    monkeypatch.setenv("WEBSITE_TEMPLATE_DIR", str(template_dir))
    monkeypatch.setenv("WEBSITE_STATIC_DIR", str(static_dir))
    monkeypatch.setenv("LAB_STATIC_DIR", str(lab_static))
    monkeypatch.setenv("CATALOG_PATH", str(catalog))
    monkeypatch.setenv("POLICY_DIR", str(policy_dir))
    reset_settings_cache()

    settings = Settings()
    assert settings.website_template_dir == template_dir
    assert settings.website_static_dir == static_dir
    assert settings.lab_static_dir == lab_static
    assert settings.catalog_path == catalog
    assert settings.policy_dir == policy_dir
    reset_settings_cache()


def test_validate_runtime_resources_passes_for_repo_layout():
    reset_settings_cache()
    settings = Settings()
    validate_runtime_resources(settings)


def test_validate_runtime_resources_fails_when_css_missing(tmp_path, monkeypatch):
    settings = Settings()
    # Point static dir at an empty tree while keeping other real paths.
    empty_static = tmp_path / "static"
    (empty_static / "css").mkdir(parents=True)
    (empty_static / "js").mkdir()
    (empty_static / "brand").mkdir()
    monkeypatch.setenv("WEBSITE_STATIC_DIR", str(empty_static))
    monkeypatch.setenv("WEBSITE_TEMPLATE_DIR", str(settings.website_template_dir))
    monkeypatch.setenv("LAB_STATIC_DIR", str(settings.lab_static_dir))
    monkeypatch.setenv("CATALOG_PATH", str(settings.catalog_path))
    monkeypatch.setenv("POLICY_DIR", str(settings.policy_dir))
    reset_settings_cache()
    with pytest.raises(ResourceConfigError, match="static:css/styles.css"):
        validate_runtime_resources(Settings())
    reset_settings_cache()


def test_required_routes_registered_once_in_safe_order():
    table = list(iter_route_table())
    by_name = {row["name"]: row for row in table if row["name"]}

    required = {
        "health": ("/health", ["GET"]),
        "registry": ("/registry", ["GET"]),
        "evaluate_legacy": ("/evaluate", ["POST"]),
        "evaluate_api": ("/api/evaluate", ["POST"]),
        "home": ("/", ["GET"]),
        "labs_index": ("/labs", ["GET"]),
        "lab_page": ("/labs/{slug}", ["GET"]),
        "lab001-static": ("/static/labs/001", []),
        "static": ("/static", []),
    }
    for name, (path, methods) in required.items():
        assert name in by_name, name
        assert by_name[name]["path"] == path
        if methods:
            assert by_name[name]["methods"] == methods

    # Exactly one of each critical path.
    paths = [row["path"] for row in table]
    for path in ("/", "/labs", "/labs/{slug}", "/health", "/api/evaluate"):
        assert paths.count(path) == 1, path

    home_idx = next(i for i, row in enumerate(table) if row["name"] == "home")
    labs_idx = next(i for i, row in enumerate(table) if row["name"] == "labs_index")
    lab_idx = next(i for i, row in enumerate(table) if row["name"] == "lab_page")
    lab_static_idx = next(i for i, row in enumerate(table) if row["name"] == "lab001-static")
    static_idx = next(i for i, row in enumerate(table) if row["name"] == "static")
    health_idx = next(i for i, row in enumerate(table) if row["name"] == "health")

    assert health_idx < home_idx < labs_idx < lab_idx < lab_static_idx < static_idx

    # Page routes must not be Mount objects; static mounts must not precede pages.
    for route in app.routes:
        if getattr(route, "path", None) in {"/", "/labs"}:
            assert isinstance(route, APIRoute)
            assert not isinstance(route, Mount)


def test_unknown_route_is_normal_404():
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404


def test_source_repo_defaults_point_at_real_files(monkeypatch):
    # Clear production-style overrides so local defaults are exercised.
    for key in (
        "WEBSITE_TEMPLATE_DIR",
        "WEBSITE_STATIC_DIR",
        "LAB_STATIC_DIR",
        "CATALOG_PATH",
        "POLICY_DIR",
    ):
        monkeypatch.delenv(key, raising=False)
    reset_settings_cache()
    settings = Settings()
    assert settings.website_template_dir == REPO_ROOT / "website" / "app" / "templates"
    assert settings.website_static_dir == REPO_ROOT / "website" / "app" / "static"
    assert settings.catalog_path == REPO_ROOT / "website" / "catalog" / "labs.yaml"
    assert (settings.website_template_dir / "home.html").is_file()
    assert (settings.website_static_dir / "css" / "styles.css").is_file()
    reset_settings_cache()
