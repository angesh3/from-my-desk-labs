from pathlib import Path

import pytest
import yaml

from from_my_desk.catalog import CatalogError, latest_lab, load_catalog, published_labs, sort_labs_by_edition

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
    assert len(labs) == 5
    by_id = {lab.id: lab for lab in labs}
    assert by_id["001"].slug == "know-your-agent"
    assert by_id["001"].reader_title_text == "Know Your Agent"
    assert by_id["001"].featured is False
    assert by_id["001"].interactive is True
    assert by_id["001"].disclaimer
    assert "Authorization" in by_id["001"].tags
    assert by_id["002"].slug == "delegated-authority"
    assert by_id["002"].reader_title_text == "Delegated Authority"
    assert by_id["002"].featured is False
    assert by_id["002"].interactive is True
    assert by_id["002"].lab_url == "/labs/delegated-authority"
    assert by_id["003"].slug == "agent-access-control"
    assert by_id["003"].featured is False
    assert by_id["003"].interactive is True
    assert by_id["003"].lab_url == "/labs/agent-access-control"
    assert by_id["004"].slug == "agent-escalation-boundary"
    assert by_id["004"].lab_url == "/labs/agent-escalation-boundary"
    assert by_id["004"].newsletter_url == "[EDITION_4_NEWSLETTER_URL]"
    assert by_id["004"].newsletter_is_placeholder is True
    assert by_id["004"].published_newsletter_url is None
    assert by_id["004"].edition_number == 4
    assert by_id["005"].slug == "verifiable-action-receipts"
    assert by_id["005"].lab_url == "/labs/verifiable-action-receipts"
    assert by_id["005"].newsletter_url == "[EDITION_5_NEWSLETTER_URL]"
    assert by_id["005"].newsletter_is_placeholder is True
    assert by_id["005"].published_newsletter_url is None
    assert by_id["005"].edition_number == 5
    assert by_id["001"].newsletter_is_placeholder is False
    assert by_id["001"].published_newsletter_url is not None


def test_newsletter_placeholder_accepted(tmp_path):
    dump(
        tmp_path / "labs.yaml",
        [valid_lab(newsletter_url="[EDITION_9_NEWSLETTER_URL]")],
    )
    labs = load_catalog(tmp_path / "labs.yaml")
    assert labs[0].newsletter_is_placeholder is True
    assert labs[0].published_newsletter_url is None


def test_published_newsletter_url_requires_https(tmp_path):
    dump(
        tmp_path / "labs.yaml",
        [valid_lab(newsletter_url="http://example.com/newsletter")],
    )
    labs = load_catalog(tmp_path / "labs.yaml")
    assert labs[0].newsletter_is_placeholder is False
    assert labs[0].published_newsletter_url is None


def test_latest_lab_selects_highest_published_edition():
    labs = load_catalog(CATALOG)
    latest = latest_lab(labs)
    assert latest is not None
    assert latest.id == "005"
    assert latest.edition_number == 5
    assert latest.title == "Can We Prove What the Agent Actually Did?"


def test_latest_lab_excludes_draft_and_on_the_desk(tmp_path):
    dump(
        tmp_path / "labs.yaml",
        [
            valid_lab(id="001", edition_number=1, status="published", featured=False),
            valid_lab(
                id="004",
                edition_number=4,
                slug="future-lab",
                title="Future Lab",
                status="draft",
                featured=False,
            ),
            valid_lab(
                id="005",
                edition_number=5,
                slug="on-desk",
                title="On Desk Lab",
                status="on_the_desk",
                featured=False,
            ),
        ],
    )
    labs = load_catalog(tmp_path / "labs.yaml")
    assert latest_lab(labs).id == "001"


def test_latest_lab_returns_none_when_no_published_labs(tmp_path):
    dump(tmp_path / "labs.yaml", [valid_lab(status="draft")])
    labs = load_catalog(tmp_path / "labs.yaml")
    assert latest_lab(labs) is None


def test_published_labs_sorted_by_edition_number(tmp_path):
    dump(
        tmp_path / "labs.yaml",
        [
            valid_lab(id="001", edition_number=1, featured=False),
            valid_lab(
                id="002",
                edition_number=2,
                slug="delegated-authority",
                title="Lab Two",
                featured=False,
            ),
            valid_lab(
                id="003",
                edition_number=3,
                slug="agent-access-control",
                title="Lab Three",
                featured=False,
            ),
        ],
    )
    labs = load_catalog(tmp_path / "labs.yaml")
    ordered = sort_labs_by_edition(published_labs(labs))
    assert [item.id for item in ordered] == ["003", "002", "001"]


def test_latest_lab_prefers_edition_number_not_yaml_order(tmp_path):
    dump(
        tmp_path / "labs.yaml",
        [
            valid_lab(
                id="003",
                edition_number=3,
                slug="agent-access-control",
                title="Agent Access Control",
                featured=False,
            ),
            valid_lab(id="001", edition_number=1, featured=False),
            valid_lab(
                id="004",
                edition_number=4,
                slug="future-lab",
                title="Future Lab",
                featured=False,
            ),
        ],
    )
    labs = load_catalog(tmp_path / "labs.yaml")
    assert latest_lab(labs).id == "004"


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
