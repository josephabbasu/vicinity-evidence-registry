# VICINITY Living Evidence System

## Purpose

VICINITY now supports continuous evidence discovery. The system stages source records. It scores eligibility. It registers strict matches. It also preserves a human review path.

The system does not treat automated metadata as completed evidence extraction. Every automated study carries verification flags. The registry does not invent effect estimates. A reviewer can deactivate an incorrect record without deleting its audit history.

## Architecture

The ingestion pipeline has five source adapters:

- Zotero Web API v3
- PubMed E-utilities
- Crossref REST API
- OpenAlex API
- Semantic Scholar Graph API

Each adapter returns the same normalized record. The record contains citation metadata, an abstract, keywords, source links, and PDF attachment information when available.

The pipeline deduplicates records by normalized DOI. It uses normalized title and year when a DOI is missing. It retains duplicate source records and links them to a canonical candidate.

## Screening

The baseline classifier is transparent. It reports five scores from 0 to 1:

- Relevance
- Population fit
- Violence exposure fit
- Mental health outcome fit
- Causal or intervention design fit

The classifier marks a record `eligible` only when every core domain crosses its strict threshold. It marks a clear mismatch `ineligible`. It sends all other records to `review`.

The `StudyClassifier` interface separates the classifier from the pipeline. A validated statistical or language model can replace the baseline later. The database will still retain model names, versions, scores, reasons, and overrides.

## Registration

An eligible candidate enters the registry when `AUTO_REGISTER_ELIGIBLE=true`. The mapper checks the current registry for a DOI or exact normalized title and year before it creates a study.

An automated record uses conservative values:

- The system labels effect direction as `Needs verification`.
- The system does not create an effect estimate.
- The system labels quality as `Needs verification`.
- The system records the source and classifier trace.
- The system marks the record as `auto_registered`.

The public Ask engine uses active approved records. Consequently, a new eligible study becomes available to public queries without a code release.

## Human Control

All administration endpoints require a reviewer bearer token or an ingestion scheduler token.

```text
GET  /admin/ingestion/candidates
GET  /admin/ingestion/candidates/{id}
POST /admin/ingestion/candidates/{id}/decision
POST /admin/ingestion/candidates/{id}/rerun
POST /admin/ingestion/run
GET  /admin/ingestion/runs
GET  /admin/ingestion/runs/{id}/events
GET  /admin/registry/studies/new
GET  /admin/registry/studies/{id}
POST /admin/registry/studies/{id}/deactivate
GET  /admin/status/ingestion
```

A human decision creates a new current eligibility result. The original classifier result remains in history. Deactivation removes a study from public synthesis. It does not delete the study.

## Configuration

The API reads these environment variables:

```text
REVIEWER_TOKEN=
INGESTION_TOKEN=
AUTO_REGISTER_ELIGIBLE=true
INGESTION_LOOKBACK_DAYS=7

ZOTERO_API_KEY=
ZOTERO_LIBRARY_TYPE=user
ZOTERO_LIBRARY_ID=
ZOTERO_COLLECTION_ID=

NCBI_API_KEY=
CROSSREF_MAILTO=
OPENALEX_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
```

Zotero requires all four Zotero values. PubMed and Crossref can run without keys. OpenAlex requires an API key. Semantic Scholar can run without a key, but the service may apply a lower rate limit.

## Scheduling

GitHub Actions calls the ingestion endpoint every Monday at 12:17 UTC. The workflow uses the existing `VICINITY_SURVEILLANCE_TOKEN` repository secret as the scheduler credential. The endpoint queues the scheduled work as a FastAPI background task.

The API records each run. It stores source cursors only after a source succeeds. A failed source does not stop the remaining sources.

## Governance

The project should validate the classifier against a dual-screened sample before it relies on automatic registration at scale. The validation report should include sensitivity, specificity, positive predictive value, and false-negative review.

The project should audit automated additions on a fixed schedule. Reviewers should prioritize records with incomplete abstracts and uncertain designs. The registry should publish corrections through its existing change log.

## Attribution

Joseph Abbas developed the VICINITY scientific concept and registry at Rutgers University-Camden. OpenAI Codex supported the software implementation.

## Source Documentation

- [Zotero Web API v3](https://www.zotero.org/support/dev/web_api/v3/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- [OpenAlex API](https://developers.openalex.org/)
- [Semantic Scholar API](https://api.semanticscholar.org/api-docs/graph)
