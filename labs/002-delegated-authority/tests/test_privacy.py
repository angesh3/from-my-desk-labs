"""Privacy and documentation presence for Lab 002."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LAB = REPO / "labs" / "002-delegated-authority"
SITE_JS = REPO / "website" / "app" / "static" / "js" / "site.js"
LAB_JS = LAB / "static" / "lab.js"

REQUIRED_DOCS = [
    "README.md",
    "docs/architecture.md",
    "docs/component-contracts.md",
    "docs/evaluation-sequence.md",
    "docs/delegation-model.md",
    "docs/profile-model.md",
    "docs/posture-model.md",
    "docs/decision-semantics.md",
    "docs/fallback-model.md",
    "docs/audit-evidence.md",
    "docs/security-and-privacy.md",
    "docs/limitations-and-evolution.md",
    "docs/animation-storyboard.md",
    "docs/demo-guide.md",
    "docs/ASSETS.md",
]

REQUIRED_DIAGRAMS = [
    "diagrams/delegated-authority-workflow.mmd",
    "diagrams/delegated-authority-workflow.svg",
    "diagrams/evaluation-flow.mmd",
    "diagrams/evaluation-flow.svg",
    "diagrams/revocation-flow.mmd",
    "diagrams/revocation-flow.svg",
    "diagrams/fallback-flow.mmd",
    "diagrams/fallback-flow.svg",
    "diagrams/system-architecture.mmd",
    "diagrams/system-architecture.svg",
    "diagrams/lab-runtime.mmd",
    "static/delegated-authority-workflow.svg",
    "static/system-architecture.svg",
    "static/evaluation-flow.svg",
    "static/fallback-flow.svg",
    "static/revocation-flow.svg",
]

FORBIDDEN = (
    "phx_",
    "principal_id",
    "agent_id",
    "delegation_id",
    "account_id",
    "audit_id",
    "identify(",
)


def test_docs_and_diagrams_exist_utf8():
    for rel in REQUIRED_DOCS + REQUIRED_DIAGRAMS:
        path = LAB / rel
        assert path.is_file(), rel
        text = path.read_text(encoding="utf-8")
        assert text.strip()
        assert "/Users/" not in text
    # Served teaching SVGs must be well-formed XML (no control characters).
    import xml.etree.ElementTree as ET

    for name in (
        "delegated-authority-workflow.svg",
        "system-architecture.svg",
        "evaluation-flow.svg",
        "fallback-flow.svg",
        "revocation-flow.svg",
    ):
        ET.fromstring((LAB / "static" / name).read_text(encoding="utf-8"))


def test_lab_js_privacy_allowlist_only():
    lab = LAB_JS.read_text(encoding="utf-8")
    site = SITE_JS.read_text(encoding="utf-8")
    assert "lab_opened" in lab
    assert "fallback_previewed" in lab
    assert "architecture_viewed" in lab
    assert "posthog.identify" not in lab
    assert "lab_slug" in site
    assert "scenario_category" in site
    assert "fallback_type" in site
    assert "architecture_type" in site
    for needle in ("phx_", "phc_"):
        assert needle not in lab
        assert not re.search(r"phc_[A-Za-z0-9]", lab)


def test_storyboard_matches_deny_execution_theme():
    story = (LAB / "docs" / "animation-storyboard.md").read_text(encoding="utf-8")
    assert "Execution is not delegated" in story or "execution" in story.lower()
    assert "DENY" in story
    assert "not_performed" in story or "Not performed" in story
    assert "Fallback" in story
