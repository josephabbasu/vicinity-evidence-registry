import json

from app.ingestion.crossref_client import CrossrefClient
from app.ingestion.openalex_client import OpenAlexClient
from app.ingestion.pubmed_client import PubMedClient
from app.ingestion.semanticscholar_client import SemanticScholarClient
from app.ingestion.zotero_client import ZoteroClient


def test_zotero_client_maps_article_and_pdf_attachment() -> None:
    payload = [
        {
            "key": "ITEM1",
            "version": 12,
            "data": {
                "itemType": "journalArticle",
                "title": "Neighborhood violence and adolescent depression",
                "creators": [{"firstName": "A", "lastName": "Author"}],
                "date": "2026-02-01",
                "publicationTitle": "Journal",
                "DOI": "https://doi.org/10.1000/test",
                "abstractNote": "Community violence and mental health.",
                "tags": [{"tag": "youth"}],
            },
            "links": {"alternate": {"href": "https://www.zotero.org/item1"}},
        },
        {
            "key": "PDF1",
            "version": 13,
            "data": {
                "itemType": "attachment",
                "parentItem": "ITEM1",
                "contentType": "application/pdf",
                "url": "https://example.org/paper.pdf",
            },
        },
    ]

    def requester(url, headers):
        assert headers["Zotero-API-Version"] == "3"
        assert "since=4" in url
        return payload, {"last-modified-version": "13", "total-results": "2"}

    client = ZoteroClient("key", "user", "1", "COLL", requester=requester)
    batch = client.fetch_new_items("4")
    assert batch.next_cursor == "13"
    assert len(batch.items) == 1
    assert batch.items[0].doi == "10.1000/test"
    assert batch.items[0].pdf_url == "https://example.org/paper.pdf"


def test_pubmed_client_maps_efetch_record() -> None:
    xml = b"""
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>123</PMID>
          <Article>
            <ArticleTitle>Youth community violence and depression</ArticleTitle>
            <Abstract><AbstractText>Adolescent mental health study.</AbstractText></Abstract>
            <AuthorList><Author><ForeName>A</ForeName><LastName>Author</LastName></Author></AuthorList>
            <Journal><Title>Journal</Title><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue></Journal>
            <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
          </Article>
          <KeywordList><Keyword>violence</Keyword></KeywordList>
        </MedlineCitation>
        <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/pubmed</ArticleId></ArticleIdList></PubmedData>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    def requester(url, headers):
        if "esearch.fcgi" in url:
            return json.dumps({"esearchresult": {"idlist": ["123"]}}).encode(), {}
        return xml, {}

    batch = PubMedClient(requester=requester).fetch_new_items("2026-01-01")
    assert len(batch.items) == 1
    assert batch.items[0].source_id == "123"
    assert batch.items[0].doi == "10.1000/pubmed"


def test_crossref_client_maps_work() -> None:
    def requester(url, headers):
        return {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/crossref",
                        "title": ["Youth violence and anxiety"],
                        "author": [{"given": "A", "family": "Author"}],
                        "published": {"date-parts": [[2026, 1, 1]]},
                        "container-title": ["Journal"],
                        "abstract": "<jats:p>Mental health abstract.</jats:p>",
                        "URL": "https://doi.org/10.1000/crossref",
                        "subject": ["Mental health"],
                    }
                ]
            }
        }, {}

    batch = CrossrefClient(requester=requester).fetch_new_items("2026-01-01")
    assert len(batch.items) == 1
    assert batch.items[0].abstract == "Mental health abstract."


def test_openalex_client_restores_abstract_and_pdf() -> None:
    def requester(url, headers):
        return {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "Community violence and youth trauma",
                    "publication_year": 2026,
                    "doi": "https://doi.org/10.1000/openalex",
                    "authorships": [{"author": {"display_name": "A Author"}}],
                    "abstract_inverted_index": {"Youth": [0], "trauma": [1]},
                    "primary_location": {
                        "landing_page_url": "https://example.org/work",
                        "source": {"display_name": "Journal"},
                    },
                    "best_oa_location": {"pdf_url": "https://example.org/work.pdf"},
                    "topics": [{"display_name": "Mental health"}],
                }
            ]
        }, {}

    batch = OpenAlexClient("key", requester=requester).fetch_new_items("2026-01-01")
    assert batch.items[0].abstract == "Youth trauma"
    assert batch.items[0].pdf_url.endswith(".pdf")


def test_semantic_scholar_client_maps_graph_record() -> None:
    def requester(url, headers):
        return {
            "data": [
                {
                    "paperId": "S1",
                    "title": "Neighborhood shootings and adolescent PTSD",
                    "authors": [{"name": "A Author"}],
                    "year": 2026,
                    "venue": "Journal",
                    "abstract": "A youth mental health study.",
                    "externalIds": {"DOI": "10.1000/semantic"},
                    "url": "https://www.semanticscholar.org/paper/S1",
                    "openAccessPdf": {"url": "https://example.org/s1.pdf"},
                    "publicationDate": "2026-02-01",
                    "fieldsOfStudy": ["Medicine"],
                }
            ]
        }, {}

    batch = SemanticScholarClient(
        "key", requester=requester
    ).fetch_new_items("2026-01-01")
    assert len(batch.items) == 1
    assert batch.items[0].doi == "10.1000/semantic"
    assert batch.items[0].source_id == "S1"
