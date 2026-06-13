from __future__ import annotations

import re
import urllib.parse
from collections.abc import Callable
from typing import Any

from .http import request_json
from .models import FetchBatch, NormalizedCandidate, normalize_doi


JsonRequester = Callable[[str, dict[str, str] | None], tuple[Any, dict[str, str]]]


class ZoteroClient:
    name = "zotero"

    def __init__(
        self,
        api_key: str,
        library_type: str,
        library_id: str,
        collection_id: str,
        requester: JsonRequester = request_json,
    ) -> None:
        if library_type not in {"user", "group"}:
            raise ValueError("ZOTERO_LIBRARY_TYPE must be 'user' or 'group'.")
        self.api_key = api_key
        self.library_type = library_type
        self.library_id = library_id
        self.collection_id = collection_id
        self.requester = requester

    @property
    def configured(self) -> bool:
        return all(
            [self.api_key, self.library_id, self.collection_id, self.library_type]
        )

    def fetch_new_items(self, cursor: str | None = None) -> FetchBatch:
        if not self.configured:
            return FetchBatch([], cursor or "0")

        plural = "users" if self.library_type == "user" else "groups"
        base = (
            f"https://api.zotero.org/{plural}/{self.library_id}/collections/"
            f"{self.collection_id}/items"
        )
        headers = {
            "Zotero-API-Key": self.api_key,
            "Zotero-API-Version": "3",
        }
        start = 0
        limit = 100
        wrappers: list[dict[str, Any]] = []
        latest_version = int(cursor or 0)

        while True:
            params = {"format": "json", "limit": str(limit), "start": str(start)}
            if cursor:
                params["since"] = cursor
            payload, response_headers = self.requester(
                f"{base}?{urllib.parse.urlencode(params)}",
                headers,
            )
            page = payload if isinstance(payload, list) else []
            wrappers.extend(page)
            latest_version = max(
                latest_version,
                int(response_headers.get("last-modified-version", latest_version)),
                *(int(item.get("version") or 0) for item in page),
            )
            total = int(response_headers.get("total-results", len(wrappers)))
            start += len(page)
            if not page or len(page) < limit or start >= total:
                break

        pdf_by_parent: dict[str, str] = {}
        for wrapper in wrappers:
            data = wrapper.get("data") or {}
            if data.get("itemType") != "attachment":
                continue
            if data.get("contentType") != "application/pdf":
                continue
            parent = str(data.get("parentItem") or "")
            if parent:
                pdf_by_parent[parent] = str(
                    data.get("url")
                    or (wrapper.get("links") or {}).get("enclosure", {}).get("href")
                    or ""
                )

        items: list[NormalizedCandidate] = []
        for wrapper in wrappers:
            data = wrapper.get("data") or {}
            if data.get("itemType") in {"attachment", "note", "annotation"}:
                continue
            title = str(data.get("title") or "").strip()
            if not title:
                continue
            creators = []
            for creator in data.get("creators") or []:
                name = creator.get("name") or " ".join(
                    value
                    for value in [creator.get("firstName"), creator.get("lastName")]
                    if value
                )
                if name:
                    creators.append(str(name))
            date_text = str(data.get("date") or "")
            year_match = re.search(r"\b(19|20)\d{2}\b", date_text)
            key = str(wrapper.get("key") or data.get("key") or "")
            doi = normalize_doi(str(data.get("DOI") or ""))
            items.append(
                NormalizedCandidate(
                    source=self.name,
                    source_id=key,
                    source_version=int(wrapper.get("version") or 0),
                    title=title,
                    authors="; ".join(creators),
                    year=int(year_match.group()) if year_match else None,
                    journal=str(
                        data.get("publicationTitle")
                        or data.get("conferenceName")
                        or data.get("publisher")
                        or ""
                    ),
                    doi=doi,
                    abstract=str(data.get("abstractNote") or ""),
                    keywords=[
                        str(tag.get("tag"))
                        for tag in data.get("tags") or []
                        if tag.get("tag")
                    ],
                    source_url=str(
                        data.get("url")
                        or (wrapper.get("links") or {}).get("alternate", {}).get("href")
                        or ""
                    ),
                    pdf_url=pdf_by_parent.get(key, ""),
                    raw_metadata=wrapper,
                )
            )
        return FetchBatch(items, str(latest_version))

