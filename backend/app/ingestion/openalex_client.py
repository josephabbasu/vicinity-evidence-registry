from __future__ import annotations

import urllib.parse
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from .http import request_json
from .models import FetchBatch, NormalizedCandidate, normalize_doi


JsonRequester = Callable[[str, dict[str, str] | None], tuple[Any, dict[str, str]]]


def _restore_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positioned = [
        (position, word)
        for word, positions in inverted_index.items()
        for position in positions
    ]
    return " ".join(word for _, word in sorted(positioned))


class OpenAlexClient:
    name = "openalex"
    query = "community violence youth mental health intervention"

    def __init__(
        self,
        api_key: str = "",
        requester: JsonRequester = request_json,
        max_results: int = 100,
    ) -> None:
        self.api_key = api_key
        self.requester = requester
        self.max_results = max_results

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def fetch_new_items(self, cursor: str | None = None) -> FetchBatch:
        start = cursor or (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        if not self.configured:
            return FetchBatch([], cursor or start)
        params = {
            "search": self.query,
            "filter": f"from_publication_date:{start},to_publication_date:{end}",
            "per-page": str(self.max_results),
            "api_key": self.api_key,
        }
        payload, _ = self.requester(
            "https://api.openalex.org/works?" + urllib.parse.urlencode(params),
            None,
        )
        items: list[NormalizedCandidate] = []
        for work in payload.get("results") or []:
            title = str(work.get("title") or "").strip()
            source_id = str(work.get("id") or "").rsplit("/", 1)[-1]
            if not title or not source_id:
                continue
            primary = work.get("primary_location") or {}
            source = primary.get("source") or {}
            authors = [
                str((authorship.get("author") or {}).get("display_name"))
                for authorship in work.get("authorships") or []
                if (authorship.get("author") or {}).get("display_name")
            ]
            doi = normalize_doi(work.get("doi"))
            best_oa = work.get("best_oa_location") or {}
            items.append(
                NormalizedCandidate(
                    source=self.name,
                    source_id=source_id,
                    title=title,
                    authors="; ".join(authors),
                    year=work.get("publication_year"),
                    journal=str(source.get("display_name") or ""),
                    doi=doi,
                    abstract=_restore_abstract(work.get("abstract_inverted_index")),
                    keywords=[
                        str(topic.get("display_name"))
                        for topic in work.get("topics") or []
                        if topic.get("display_name")
                    ],
                    source_url=str(
                        primary.get("landing_page_url")
                        or work.get("doi")
                        or work.get("id")
                        or ""
                    ),
                    pdf_url=str(
                        best_oa.get("pdf_url") or primary.get("pdf_url") or ""
                    ),
                    raw_metadata=work,
                )
            )
        return FetchBatch(items, end)

