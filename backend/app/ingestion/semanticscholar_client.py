from __future__ import annotations

import urllib.parse
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from .http import request_json
from .models import FetchBatch, NormalizedCandidate, normalize_doi


JsonRequester = Callable[[str, dict[str, str] | None], tuple[Any, dict[str, str]]]


class SemanticScholarClient:
    name = "semanticscholar"
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
        return True

    def fetch_new_items(self, cursor: str | None = None) -> FetchBatch:
        start = cursor or (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        start_year = int(start[:4])
        end_year = int(end[:4])
        params = {
            "query": self.query,
            "limit": str(self.max_results),
            "year": f"{start_year}-{end_year}",
            "fields": (
                "paperId,title,authors,year,venue,abstract,externalIds,url,"
                "openAccessPdf,publicationDate,fieldsOfStudy"
            ),
        }
        headers = {"x-api-key": self.api_key} if self.api_key else None
        payload, _ = self.requester(
            "https://api.semanticscholar.org/graph/v1/paper/search?"
            + urllib.parse.urlencode(params),
            headers,
        )
        items: list[NormalizedCandidate] = []
        for paper in payload.get("data") or []:
            publication_date = str(paper.get("publicationDate") or "")
            if publication_date and publication_date < start:
                continue
            source_id = str(paper.get("paperId") or "")
            title = str(paper.get("title") or "").strip()
            if not source_id or not title:
                continue
            external_ids = paper.get("externalIds") or {}
            items.append(
                NormalizedCandidate(
                    source=self.name,
                    source_id=source_id,
                    title=title,
                    authors="; ".join(
                        str(author.get("name"))
                        for author in paper.get("authors") or []
                        if author.get("name")
                    ),
                    year=paper.get("year"),
                    journal=str(paper.get("venue") or ""),
                    doi=normalize_doi(external_ids.get("DOI")),
                    abstract=str(paper.get("abstract") or ""),
                    keywords=[
                        str(value) for value in paper.get("fieldsOfStudy") or []
                    ],
                    source_url=str(paper.get("url") or ""),
                    pdf_url=str((paper.get("openAccessPdf") or {}).get("url") or ""),
                    raw_metadata=paper,
                )
            )
        return FetchBatch(items, end)
