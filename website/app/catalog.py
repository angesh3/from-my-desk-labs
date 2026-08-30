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
    homepage_lead: Optional[str] = None
    homepage_detail: Optional[str] = None
    homepage_safety: Optional[str] = None
    reader_title: Optional[str] = None
    homepage_earlier_description: Optional[str] = None

    @property
    def edition_label(self) -> str:
        return "Lab {0:03d}".format(self.edition_number)

    @property
    def short_title(self) -> str:
        if ":" in self.title:
            return self.title.split(":", 1)[0].strip()
        return self.title

    @property
    def reader_title_text(self) -> str:
        if self.reader_title:
            return self.reader_title.strip()
        return self.short_title

    @property
    def homepage_earlier_text(self) -> str:
        if self.homepage_earlier_description:
            return self.homepage_earlier_description.strip()
        return self.subtitle

    @property
    def homepage_lead_text(self) -> str:
        return (self.homepage_lead or self.subtitle).strip()

    @property
    def homepage_detail_text(self) -> Optional[str]:
        detail = (self.homepage_detail or "").strip()
        if detail:
            return detail
        if self.summary != self.subtitle:
            return self.summary
        return None

    @property
    def homepage_safety_text(self) -> Optional[str]:
        safety = (self.homepage_safety or "").strip()
        if safety:
            return safety
        if self.disclaimer:
            return self.disclaimer
        return None


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
    homepage_lead = raw.get("homepage_lead")
    if homepage_lead is not None:
        homepage_lead = str(homepage_lead).strip() or None
    homepage_detail = raw.get("homepage_detail")
    if homepage_detail is not None:
        homepage_detail = str(homepage_detail).strip() or None
    homepage_safety = raw.get("homepage_safety")
    if homepage_safety is not None:
        homepage_safety = str(homepage_safety).strip() or None
    reader_title = raw.get("reader_title")
    if reader_title is not None:
        reader_title = str(reader_title).strip() or None
    homepage_earlier_description = raw.get("homepage_earlier_description")
    if homepage_earlier_description is not None:
        homepage_earlier_description = str(homepage_earlier_description).strip() or None
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
        homepage_lead=homepage_lead,
        homepage_detail=homepage_detail,
        homepage_safety=homepage_safety,
        reader_title=reader_title,
        homepage_earlier_description=homepage_earlier_description,
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


def published_labs(labs: List[LabEntry]) -> List[LabEntry]:
    return [item for item in labs if item.status == "published"]


def sort_labs_by_edition(labs: List[LabEntry], reverse: bool = True) -> List[LabEntry]:
    return sorted(labs, key=lambda item: item.edition_number, reverse=reverse)


def latest_lab(labs: List[LabEntry]) -> Optional[LabEntry]:
    """Return the newest published lab by edition_number."""
    published = published_labs(labs)
    if not published:
        return None
    return max(published, key=lambda item: item.edition_number)


def featured_lab(labs: List[LabEntry]) -> Optional[LabEntry]:
    """Legacy featured flag; prefer latest_lab for homepage promotion."""
    for item in labs:
        if item.featured and item.status == "published":
            return item
    return latest_lab(labs)
