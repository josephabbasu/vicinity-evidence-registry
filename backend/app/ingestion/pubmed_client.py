from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date, timedelta

from .http import request_bytes
from .models import FetchBatch, NormalizedCandidate, normalize_doi


BytesRequester = Callable[[str, dict[str, str] | None], tuple[bytes, dict[str, str]]]


class PubMedClient:
    name = "pubmed"
    query = (
        '("community violence" OR "neighborhood violence" OR "gun violence" '
        'OR shooting OR homicide OR "violent crime") AND '
        '(adolescent OR youth OR child OR "young adult") AND '
        '("mental health" OR depression OR anxiety OR trauma OR PTSD '
        'OR resilience OR recovery OR intervention)'
    )

    def __init__(
        self,
        api_key: str = "",
        requester: BytesRequester = request_bytes,
        max_results: int = 200,
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
        search_params = {
            "db": "pubmed",
            "retmode": "json",
            "retmax": str(self.max_results),
            "term": self.query,
            "mindate": start,
            "maxdate": end,
            "datetype": "pdat",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key
        search_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            + urllib.parse.urlencode(search_params)
        )
        body, _ = self.requester(search_url, None)
        import json

        ids = json.loads(body.decode("utf-8")).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return FetchBatch([], end)

        fetch_params = {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(ids),
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key
        fetch_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
            + urllib.parse.urlencode(fetch_params)
        )
        xml_body, _ = self.requester(fetch_url, None)
        root = ET.fromstring(xml_body)
        items: list[NormalizedCandidate] = []
        for article_node in root.findall(".//PubmedArticle"):
            citation = article_node.find("./MedlineCitation")
            article = citation.find("./Article") if citation is not None else None
            if citation is None or article is None:
                continue
            pmid = (citation.findtext("./PMID") or "").strip()
            title_node = article.find("./ArticleTitle")
            if title_node is None:
                continue
            title = "".join(title_node.itertext()).strip()
            if not pmid or not title:
                continue
            authors = []
            for author in article.findall("./AuthorList/Author"):
                name = " ".join(
                    value
                    for value in [
                        author.findtext("./ForeName"),
                        author.findtext("./LastName"),
                    ]
                    if value
                )
                if name:
                    authors.append(name)
            abstract = " ".join(
                "".join(node.itertext()).strip()
                for node in article.findall("./Abstract/AbstractText")
            ).strip()
            journal = article.findtext("./Journal/Title") or ""
            year_text = (
                article.findtext("./Journal/JournalIssue/PubDate/Year")
                or article.findtext("./ArticleDate/Year")
                or ""
            )
            year_match = re.search(r"\b(19|20)\d{2}\b", year_text)
            article_ids = {
                node.attrib.get("IdType", ""): (node.text or "")
                for node in article_node.findall("./PubmedData/ArticleIdList/ArticleId")
            }
            doi = normalize_doi(article_ids.get("doi"))
            keywords = [
                "".join(node.itertext()).strip()
                for node in citation.findall("./KeywordList/Keyword")
                if "".join(node.itertext()).strip()
            ]
            items.append(
                NormalizedCandidate(
                    source=self.name,
                    source_id=pmid,
                    title=title,
                    authors="; ".join(authors),
                    year=int(year_match.group()) if year_match else None,
                    journal=journal,
                    doi=doi,
                    abstract=abstract,
                    keywords=keywords,
                    source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    raw_metadata={
                        "pmid": pmid,
                        "article_ids": article_ids,
                        "publication_types": [
                            node.text or ""
                            for node in article.findall("./PublicationTypeList/PublicationType")
                        ],
                    },
                )
            )
        return FetchBatch(items, end)
