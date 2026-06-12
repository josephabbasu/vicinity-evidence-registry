# VICINITY

VICINITY is the Causal Evidence Registry for Neighborhood Violence and Youth Mental Health.

**Tagline:** What the best evidence actually shows. Updated as it happens.

The MVP includes a searchable registry, study detail pages, a transparent coding protocol, and a structured study nomination queue. It uses 32 studies from the supplied systematic-review extraction workbook.

## Current Data

The project brief referred to a structured CSV. The supplied folder did not contain that CSV. It contained an Excel workbook with exactly 32 complete study rows:

`data/source/Synthesis_Systematic_Review_Extraction_Paper_1.xlsx`

The seed generator preserves all 32 raw fields. It exports:

- `backend/app/data/studies.csv`
- `backend/app/data/studies.json`
- `VALIDATION_REPORT.md`

The current normalization yields 26 credible-tier studies and 6 associational studies. The application displays all field-level verification flags.

## Stack

- Frontend: React, Vite, and Tailwind CSS
- Backend: FastAPI and SQLAlchemy
- Development database: SQLite
- Production database: PostgreSQL
- Deployment: Render Blueprint

## Run Locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

Set `VITE_API_URL` when the API uses another origin.

## Validate and Rebuild Seed Data

The seed generator requires `openpyxl`.

```powershell
python scripts/generate_seed.py data/source/Synthesis_Systematic_Review_Extraction_Paper_1.xlsx --project-root .
```

The command fails if it does not find exactly 32 complete study rows or if generated slugs are not unique.

## API

- `GET /api/health`
- `GET /api/stats`
- `GET /api/studies`
- `GET /api/studies/{slug}`
- `GET /api/updates`
- `POST /api/submissions`

Study filters include design, age group, country, outcome, exposure window, quality tier, causal tier, publication year, intervention status, and free-text search.

## Data Schema

The `studies` table stores the raw extraction fields and normalized registry fields. Core normalized fields include:

- Study ID, title, year, and country
- Age range and age-group categories
- Design type and causal tier
- Exposure type, window, and geographic scale
- Outcome type, measure, and scale
- Effect direction and significance
- Risk-of-bias tier
- Verification flags

The `submissions` table stores incoming nominations with a pending status. The `updates` table stores the registry changelog.

## Causal Tier Rule

The credible tier requires clear source support for at least one of these designs:

- Randomized controlled trial
- Difference-in-differences
- Natural experiment
- Instrumental variables
- Within-person fixed effects
- Within-family sibling or twin fixed effects

Other designs remain associational. The registry does not promote uncertain designs.

## Add a Study

1. Submit the study through the public form.
2. Confirm the study meets the population, exposure, and outcome criteria.
3. Verify the causal design against the full article.
4. Extract all source fields.
5. Complete the risk-of-bias appraisal.
6. Add the approved record to the source workbook or canonical data pipeline.
7. Regenerate the seed files and review `VALIDATION_REPORT.md`.
8. Run the backend tests and frontend build.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm run lint
npm run build
```

## Render Deployment

`render.yaml` defines:

- A free Render static site for the frontend
- A free Render Python web service for the API
- A free Render Postgres database

Render spins down free web services after 15 minutes without traffic. A cold start can take about one minute.

Render free Postgres databases expire 30 days after creation as of June 12, 2026. The initial free launch therefore needs a database upgrade before day 30 to preserve submissions and changelog entries. The 32-study seed can always rebuild the studies table.

## Roadmap

### Phase 2

- Data-driven synthesis dashboard
- Effect-size distribution chart
- Subgroup panels by design and age
- Summary statistics table
- Manually curated narrative synthesis container
- Interactive forest plot

### Phase 3

- Dynamic narrative generation
- Bayesian updating module

Phase 2 and Phase 3 are not part of the MVP.
