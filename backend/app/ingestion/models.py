from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip().casefold()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.rstrip(" .") or None


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def make_dedupe_key(title: str, year: int | None, doi: str | None) -> str:
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return f"doi:{normalized_doi}"
    return f"title:{normalize_title(title)}|year:{year or 'unknown'}"


@dataclass(slots=True)
class NormalizedCandidate:
    source: str
    source_id: str
    title: str
    authors: str = ""
    year: int | None = None
    journal: str = ""
    doi: str | None = None
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)
    source_url: str = ""
    pdf_url: str = ""
    source_version: int | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def dedupe_key(self) -> str:
        return make_dedupe_key(self.title, self.year, self.doi)


@dataclass(slots=True)
class FetchBatch:
    items: list[NormalizedCandidate]
    next_cursor: str

