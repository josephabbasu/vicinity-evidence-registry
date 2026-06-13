from __future__ import annotations

import re
import urllib.parse
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from .http import request_json
from .models import FetchBatch, NormalizedCandidate, normalize_doi


JsonRequester = Callable[[str, dict[str, str] | None], tuple[Any, dict[str, str]]]


class CrossrefClient:
    name = "crossref"
    query = (
        "community neighborhood violence youth adolescent mental health "
        "depression anxiety trauma intervention"
    )

    def __init__(
        self,
        mailto: str = "",
        requester: JsonRequester = request_json,
        max_results: int = 100,
    ) -> None:
        self.mailto = mailto
        self.requester = requester
        self.max_results = max_results

    @property
    def configured(self) -> bool:
        return True

    def fetch_new_items(self, cursor: str | None = None) -> FetchBatch:
        start = cursor or (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        params = {
            "query.bibliographic": self.query,
            "filter": f"from-pub-date:{start},until-pub-date:{end}",
            "rows": str(self.max_results),
            "select": (
                "DOI,title,author,published,container-title,abstract,URL,subject,type"
            ),
        }
        if self.mailto:
            params["mailto"] = self.mailto
        payload, _ = self.requester(
            "https://api.crossref.org/works?" + urllib.parse.urlencode(params),
            None,
        )
        works = (payload.get("message") or {}).get("items") or []
        items: list[NormalizedCandidate] = []
        for work in works:
            title = " ".join(work.get("title") or []).strip()
            doi = normalize_doi(work.get("DOI"))
            if not title or not doi:
                continue
            authors = []
            for author in work.get("author") or []:
                name = " ".join(
                    value
                    for value in [author.get("given"), author.get("family")]
                    if value
                )
                if name:
                    authors.append(name)
            date_parts = (work.get("published") or {}).get("date-parts") or []
            year = date_parts[0][0] if date_parts and date_parts[0] else None
            abstract = re.sub(r"<[^>]+>", " ", str(work.get("abstract") or ""))
            abstract = re.sub(r"\s+", " ", abstract).strip()
            items.append(
                NormalizedCandidate(
                    source=self.name,
                    source_id=doi,
                    title=title,
                    authors="; ".join(authors),
                    year=int(year) if year else None,
                    journal="; ".join(work.get("container-title") or []),
                    doi=doi,
                    abstract=abstract,
                    keywords=[str(value) for value in work.get("subject") or []],
                    source_url=str(work.get("URL") or f"https://doi.org/{doi}"),
                    raw_metadata=work,
                )
            )
        return FetchBatch(items, end)

