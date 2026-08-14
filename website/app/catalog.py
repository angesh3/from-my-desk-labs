"""Load and validate the editorial lab catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml

ALLOWED_STATUSES = {"published", "draft", "on_the_desk"}
REQUIRED_FIELDS = (
    "id",
    "edition_number",
    "slug",
    "title",
    "summary",
    "status",
    "tags",
    "lab_url",
    "newsletter_url",
    "github_url",
    "interactive",
    "featured",
)


class CatalogError(ValueError):
    """Raised when the lab catalog cannot be used safely."""


@dataclass(frozen=True)
class LabEntry:
    id: str
    edition_number: int
    slug: str
    title: str
    subtitle: str
    summary: str
    status: str
    tags: List[str]
    lab_url: str
    newsletter_url: str
    github_url: str
    interactive: bool
    featured: bool
    published_date: Optional[str] = None
    disclaimer: Optional[str] = None

    @property
    def edition_label(self) -> str:
        return "Lab {0:03d}".format(self.edition_number)


def _require(raw: Dict[str, Any], field: str) -> Any:
    if field not in raw or raw[field] in (None, ""):
        raise CatalogError("Catalog entry is missing '{0}'.".format(field))
    return raw[field]


def _valid_url(value: str) -> bool:
    if value.startswith("/"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_entry(raw: Any) -> LabEntry:
    if not isinstance(raw, dict):
        raise CatalogError("Each catalog lab must be a mapping.")
    for field in REQUIRED_FIELDS:
        _require(raw, field)
    edition = raw["edition_number"]
    if not isinstance(edition, int) or isinstance(edition, bool) or edition < 1:
        raise CatalogError("edition_number must be a positive integer.")
    status = str(raw["status"]).strip()
    if status not in ALLOWED_STATUSES:
        raise CatalogError("Unknown catalog status '{0}'.".format(status))
    tags = raw["tags"]
    if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
        raise CatalogError("tags must be a list of strings.")
    lab_url = str(raw["lab_url"]).strip()
    newsletter_url = str(raw["newsletter_url"]).strip()
    github_url = str(raw["github_url"]).strip()
    for label, url in (
        ("lab_url", lab_url),
        ("newsletter_url", newsletter_url),
        ("github_url", github_url),
    ):
        if not _valid_url(url):
            raise CatalogError("Invalid {0}.".format(label))
    subtitle = str(raw.get("subtitle") or raw["summary"]).strip()
    published = raw.get("published_date")
    if published is not None:
        published = str(published).strip() or None
    disclaimer = raw.get("disclaimer")
    if disclaimer is not None:
        disclaimer = str(disclaimer).strip() or None
    return LabEntry(
        id=str(raw["id"]).strip(),
        edition_number=edition,
        slug=str(raw["slug"]).strip(),
        title=str(raw["title"]).strip(),
        subtitle=subtitle,
        summary=str(raw["summary"]).strip(),
        status=status,
        tags=[item.strip() for item in tags],
        lab_url=lab_url,
        newsletter_url=newsletter_url,
        github_url=github_url,
        interactive=bool(raw["interactive"]),
        featured=bool(raw["featured"]),
        published_date=published,
        disclaimer=disclaimer,
    )


def load_catalog(path: Path) -> List[LabEntry]:
    if not path.exists():
        raise CatalogError("Lab catalog file is missing.")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogError("Lab catalog is not valid YAML.") from exc
    if not isinstance(data, dict) or "labs" not in data:
        raise CatalogError("Catalog must contain a 'labs' list.")
    labs_raw = data["labs"]
    if not isinstance(labs_raw, list) or not labs_raw:
        raise CatalogError("Catalog labs list must not be empty.")
    labs = [parse_entry(item) for item in labs_raw]
    ids = [item.id for item in labs]
    slugs = [item.slug for item in labs]
    if len(set(ids)) != len(ids):
        raise CatalogError("Duplicate lab ID in catalog.")
    if len(set(slugs)) != len(slugs):
        raise CatalogError("Duplicate lab slug in catalog.")
    return labs


def featured_lab(labs: List[LabEntry]) -> Optional[LabEntry]:
    for item in labs:
        if item.featured and item.status == "published":
            return item
    published = [item for item in labs if item.status == "published"]
    return published[0] if published else None
