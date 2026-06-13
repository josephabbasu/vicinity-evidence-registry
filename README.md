# VICINITY

VICINITY is a Living Causal Evidence Observatory for neighborhood violence and youth mental health.

The registry connects two systematic-review streams. The first contains 32 studies about violence exposure and its consequences. The second contains 26 intervention studies. The combined Version 2 release contains 58 unique studies.

## Purpose

VICINITY serves four decision groups.

- Researchers can inspect design, appraisal, provenance, and evidence gaps.
- Practitioners can query evidence by population, exposure, and outcome.
- Policy makers can compare structural and psychosocial responses.
- Administrators can monitor search coverage, review status, and releases.

The system does not treat every outcome as a mental-health outcome. It distinguishes direct mental-health outcomes from exposure-reduction outcomes. It also identifies pathway outcomes and records that require verification.

## Attribution

Joseph Abbas conceived and developed VICINITY. He led the systematic reviews, data architecture, registry development, and scientific stewardship.

Joseph Abbas is a PhD Candidate in Prevention Science at Rutgers University-Camden.

OpenAI Codex provided software implementation support.

This repository does not imply institutional endorsement by Rutgers University.

## Evidence Base

The canonical source files are:

- `data/source/Synthesis_Systematic_Review_Extraction_Paper_1.xlsx`
- `data/source/Intervention_Systematic_Review_Extraction_Paper_2.xlsx`

The registered review protocol is PROSPERO CRD420251076481. The imported systematic-review search coverage ends July 31, 2025.

The generators preserve source fields. They add conservative normalized fields for search and decision support.

- `registry_stream`
- `evidence_role`
- `intervention_class`
- `outcome_directness`
- `decision_relevance`
- `source_review`
- `search_coverage_end`
- `source_row`

The seed process refuses to launch unless it finds exactly 32 exposure records and 26 intervention records.

## Integrity Rules

VICINITY applies the following rules.

1. The registry never fabricates effect estimates, confidence intervals, p-values, DOIs, or publications.
2. The registry preserves the raw extraction fields.
3. The registry labels derived fields.
4. The registry exposes verification flags.
5. Two named reviewers must agree at screening and full text.
6. Conflicting decisions remain unresolved.
7. Only approved studies appear in public evidence synthesis.
8. Every surveillance run records its date interval and completed sources.

## Living Surveillance

The surveillance service searches PubMed and Crossref. It can also search OpenAlex when `OPENALEX_API_KEY` is configured.

The service searches only the uncovered interval after the latest completed search. It deduplicates by DOI. It uses normalized title and year when a DOI is unavailable.

Automated relevance scoring prioritizes records for human review. Records below the priority threshold remain stored as `triage_low`. The score never determines eligibility or inclusion.

The scheduled endpoint is:

`POST /api/surveillance/run`

The request must include `X-Surveillance-Token`.

## Stack

- Frontend: React, Vite, and Tailwind CSS
- Backend: FastAPI and SQLAlchemy
- Development database: SQLite
- Production database: PostgreSQL
- Deployment: Render
- Scheduled surveillance: GitHub Actions

## Run Locally

Set two private environment variables.

```powershell
$env:REVIEWER_TOKEN = "replace-with-a-random-secret"
$env:SURVEILLANCE_TOKEN = "replace-with-another-random-secret"
```

Run the backend.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Run the frontend.

```powershell
cd frontend
npm install
npm run dev
```

The API runs at `http://localhost:8000`. The frontend runs at `http://localhost:5173`.

## Rebuild Data

```powershell
python scripts/generate_seed.py data/source/Synthesis_Systematic_Review_Extraction_Paper_1.xlsx --project-root .
python scripts/generate_intervention_seed.py data/source/Intervention_Systematic_Review_Extraction_Paper_2.xlsx --project-root .
```

## Verify

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm run lint
npm run build
```

## Current Limits

The source workbooks do not provide structured estimates for most records. VICINITY therefore does not present a pooled effect.

Many records lack verified DOIs. Many records also lack structured confidence intervals.

Scheduled surveillance does not make VICINITY a completed living systematic review by itself. The team must screen, extract, appraise, adjudicate, and publish eligible records.

Render free databases expire unless the owner upgrades them. The team must maintain database backups and a durable production plan.
