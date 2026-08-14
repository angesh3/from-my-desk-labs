import importlib
from pathlib import Path

import pytest


def test_lab_package_is_uniquely_named():
    import from_my_desk.main
    import know_your_agent.gateway
    import know_your_agent.loader
    import know_your_agent.models
    import know_your_agent.policy_engine

    assert from_my_desk.main.app is not None
    assert know_your_agent.gateway.router is not None
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("policy_engine")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("loader")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("models")


def test_application_code_does_not_mutate_sys_path():
    roots = [
        Path(__file__).resolve().parents[2] / "website" / "app",
        Path(__file__).resolve().parents[2] / "labs" / "001-know-your-agent" / "src",
    ]
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "sys.path" not in text, path


def test_website_package_includes_templates_and_static():
    import from_my_desk

    package_dir = Path(from_my_desk.__file__).resolve().parent
    assert (package_dir / "templates" / "base.html").is_file()
    assert (package_dir / "static" / "css" / "styles.css").is_file()
    assert (package_dir / "static" / "brand" / "from-my-desk-logo.webp").is_file()
    assert not (package_dir / "static" / "brand" / "from-my-desk-logo-source.png").exists()
