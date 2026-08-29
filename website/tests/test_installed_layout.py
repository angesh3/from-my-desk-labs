"""Exercise a non-editable install layout with explicit absolute resource paths."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.slow
def test_non_editable_install_resolves_explicit_paths(tmp_path):
    """Install the wheel/package non-editably and boot with /srv-style absolute paths."""
    target = tmp_path / "site-packages"
    target.mkdir()
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-cache-dir",
            "--target",
            str(target),
            str(REPO_ROOT),
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    env["WEBSITE_TEMPLATE_DIR"] = str(REPO_ROOT / "website" / "app" / "templates")
    env["WEBSITE_STATIC_DIR"] = str(REPO_ROOT / "website" / "app" / "static")
    env["LAB_STATIC_DIR"] = str(REPO_ROOT / "labs" / "001-know-your-agent" / "static")
    env["LAB002_STATIC_DIR"] = str(REPO_ROOT / "labs" / "002-delegated-authority" / "static")
    env["CATALOG_PATH"] = str(REPO_ROOT / "website" / "catalog" / "labs.yaml")
    env["POLICY_DIR"] = str(REPO_ROOT / "labs" / "001-know-your-agent" / "policies")
    env["LAB002_DATA_DIR"] = str(REPO_ROOT / "labs" / "002-delegated-authority" / "examples")
    env["LAB002_POLICY_DIR"] = str(REPO_ROOT / "labs" / "002-delegated-authority" / "policies")
    env["LAB003_DATA_DIR"] = str(REPO_ROOT / "labs" / "003-agent-access-control" / "examples")
    env["LAB003_POLICY_DIR"] = str(REPO_ROOT / "labs" / "003-agent-access-control" / "policies")
    env["LAB003_STATIC_DIR"] = str(REPO_ROOT / "labs" / "003-agent-access-control" / "static")
    env["POSTHOG_ENABLED"] = "false"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    probe = r"""
import from_my_desk
from pathlib import Path
from from_my_desk.config import get_settings, validate_runtime_resources, reset_settings_cache
from fastapi.testclient import TestClient

reset_settings_cache()
# Import after env is set so mounts/templates bind to explicit paths.
import importlib
import from_my_desk.main as main
importlib.reload(main)

settings = get_settings()
validate_runtime_resources(settings)
assert settings.website_template_dir == Path(r'''{templates}''')
assert settings.website_static_dir == Path(r'''{static}''')
pkg = Path(from_my_desk.__file__).resolve().parent
assert 'site-packages' in str(pkg) or pkg != Path(r'''{templates}''').parent

client = TestClient(main.app)
assert client.get('/').status_code == 200
assert 'Perspectives shaped by experience' in client.get('/').text
assert client.get('/labs').status_code == 200
assert client.get('/labs/know-your-agent').status_code == 200
assert client.get('/labs/delegated-authority').status_code == 200
assert client.get('/labs/agent-access-control').status_code == 200
assert client.get('/static/labs/002/system-architecture.svg').status_code == 200
assert client.get('/static/labs/002/delegated-authority-workflow.svg').status_code == 200
assert client.get('/static/labs/002/evaluation-flow.svg').status_code == 200
assert client.get('/static/labs/002/fallback-flow.svg').status_code == 200
assert client.get('/static/labs/002/revocation-flow.svg').status_code == 200
assert client.post('/api/labs/002/evaluate', json={{'scenario_id': 'valid_narrow_delegation'}}).json()['decision'] == 'allow'
assert client.post('/api/labs/003/evaluate', json={{'scenario_id': 'managed_public_data_read'}}).json()['decision'] == 'allow'
assert client.get('/static/labs/003/nac-comparison.svg').status_code == 200
assert client.get('/static/labs/003/lab.js').status_code == 200
css = client.get('/static/css/styles.css')
assert css.status_code == 200
assert '--navy:' in css.text
assert client.get('/static/brand/from-my-desk-logo.webp').status_code == 200
assert client.get('/static/labs/001/architecture.svg').status_code == 200
assert client.get('/health').json()['status'] == 'ok'

paths = [getattr(r, 'path', None) for r in main.app.routes]
assert paths.count('/') == 1
assert paths.count('/labs') == 1
home_i = next(i for i, r in enumerate(main.app.routes) if getattr(r, 'name', None) == 'home')
static_i = next(i for i, r in enumerate(main.app.routes) if getattr(r, 'name', None) == 'static')
assert home_i < static_i
print('OK')
""".format(
        templates=REPO_ROOT / "website" / "app" / "templates",
        static=REPO_ROOT / "website" / "app" / "static",
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        env=env,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "OK" in result.stdout
