from pathlib import Path

import pytest
import yaml

from from_my_desk.catalog import CatalogError, load_catalog

CATALOG = Path(__file__).resolve().parents[1] / "catalog" / "labs.yaml"


def dump(path: Path, labs):
    path.write_text(yaml.safe_dump({"labs": labs}, sort_keys=False), encoding="utf-8")


def valid_lab(**overrides):
    entry = {
        "id": "001",
        "edition_number": 1,
        "slug": "know-your-agent",
        "title": "Know Your Agent: Identity Is Only the Beginning",
        "subtitle": "Identity can establish which agent is acting.",
        "summary": "Identity can establish which agent is acting. Authority, scope, limits, and context determine whether its requested action should proceed.",
        "status": "published",
        "tags": ["AI Agents", "Identity"],
        "lab_url": "/labs/know-your-agent",
        "newsletter_url": "https://www.linkedin.com/newsletters/from-my-desk-7492634647890341890/",
        "github_url": "https://github.com/angesh3/from-my-desk-labs",
        "interactive": True,
        "featured": True,
    }
    entry.update(overrides)
    return entry


def test_published_catalog_loads():
    labs = load_catalog(CATALOG)
    assert len(labs) == 1
    lab = labs[0]
    assert lab.id == "001"
    assert lab.slug == "know-your-agent"
    assert lab.featured is True
    assert lab.interactive is True
    assert lab.published_date is None
    assert lab.disclaimer
    assert "Authorization" in lab.tags


def test_duplicate_id_rejected(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(), valid_lab(slug="other")])
    with pytest.raises(CatalogError, match="Duplicate lab ID"):
        load_catalog(tmp_path / "labs.yaml")


def test_duplicate_slug_rejected(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(), valid_lab(id="002", edition_number=2)])
    with pytest.raises(CatalogError, match="Duplicate lab slug"):
        load_catalog(tmp_path / "labs.yaml")


def test_missing_required_field_rejected(tmp_path):
    entry = valid_lab()
    del entry["title"]
    dump(tmp_path / "labs.yaml", [entry])
    with pytest.raises(CatalogError, match="title"):
        load_catalog(tmp_path / "labs.yaml")


def test_invalid_status_rejected(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(status="shipping-soon")])
    with pytest.raises(CatalogError, match="Unknown catalog status"):
        load_catalog(tmp_path / "labs.yaml")


def test_invalid_url_rejected(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(github_url="javascript:alert(1)")])
    with pytest.raises(CatalogError, match="Invalid github_url"):
        load_catalog(tmp_path / "labs.yaml")


def test_invalid_edition_number_rejected(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(edition_number=0)])
    with pytest.raises(CatalogError, match="edition_number"):
        load_catalog(tmp_path / "labs.yaml")
