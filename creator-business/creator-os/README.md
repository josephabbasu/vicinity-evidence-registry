# CreatorOS

The production system for the **Plain Money** YouTube business (Phase 6 of the project plan). It operationalizes the AI production pipeline designed in `../report/05-production-system.md`: an auditable idea → research → script → **fact-check gate** → production → publish → analyze workflow, with Claude doing the drafting and humans holding the trust gates.

## Modules

| Module | What it does |
|---|---|
| **Dashboard** | Channel KPIs (views, watch hours, CTR, retention, revenue) scored against the strategy's health targets, pipeline status, top videos |
| **Idea Bank** | Scored idea backlog (demand / evergreen / competition gap / monetization / ease → weighted opportunity score), AI idea generator |
| **Content Database** | Every video with its pipeline state, research brief, script, metadata, claims |
| **Pipeline state machine** | `idea → researched → scripted → fact_checked → voiced → edited → thumbnail → scheduled → published → analyzed` — advancing past `fact_checked` is **blocked while any claim is unverified**, and verifying a claim **requires a source URL** |
| **Research / Script / Fact-check** | Claude-powered generators (brand voice baked in, `[CLAIM]` markers enforced) with full offline fallbacks when no API key is set |
| **SEO Optimizer** | Deterministic 100-point metadata scorer (explainable checks) + AI suggestions |
| **Trend Detector** | Tracked keywords with interest history, growth %, and momentum classification (rising / evergreen / declining) |
| **Competitor Tracker** | Channels with subscriber snapshots and growth deltas |
| **Publishing Planner** | Calendar, Tue/Sat 14:00 UTC slot generator, 3-week batch-buffer health |
| **AI Assistant** | Claude chat grounded in the brand voice |
| **Library** | Versioned prompt library + knowledge base (voice guide, checklists, sponsor ethics screen) — seeded on first run |
| **Tasks & Workflows** | Task manager; `POST /workflows/produce/{idea_id}` runs the whole AI half of the pipeline and creates the human-gate checklist; `POST /workflows/weekly-ideation` tops up thin pillars |

## Stack

- **Backend:** FastAPI + SQLAlchemy 2 (SQLite dev / PostgreSQL prod), JWT auth (PBKDF2 password hashing), Anthropic SDK (`claude-opus-4-8` default, configurable)
- **Frontend:** React 18 + Vite + Tailwind (brand palette: ink/paper/verified-green/signal-amber/claret)
- **Tests:** pytest suite covering auth, the fact-check gate, scheduling rules, scoring, trends, analytics
- **CI:** GitHub Actions (`.github/workflows/creator-os-ci.yml` at the repo root) — backend tests + frontend build
- **Deploy:** Docker Compose (Postgres + API + nginx-served frontend)

## Run with Docker

```bash
cd creator-business/creator-os
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
# Frontend: http://localhost:5173   API docs: http://localhost:8000/docs
```

`ANTHROPIC_API_KEY` is optional — without it every AI feature degrades to a structured manual-mode template and the UI labels outputs `fallback mode`.

## Run natively

```bash
# backend
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload           # http://localhost:8000

# frontend (separate shell)
cd frontend
npm install && npm run dev                        # http://localhost:5173 (proxies /api → :8000)
```

First run seeds the prompt library, knowledge base, starter ideas, and tracked keywords. Create an account on the login screen (registration is open by default — front it with your own gate before public deployment).

## Tests

```bash
cd backend && .venv/bin/python -m pytest
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./creatoros.db` | SQLAlchemy URL (Postgres in prod) |
| `SECRET_KEY` | dev value | JWT signing — set a 32+ byte random secret in prod |
| `ANTHROPIC_API_KEY` | empty | Enables Claude; empty = offline fallback |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Model for all generators |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `SEED_DEMO_DATA` | `1` | Seed prompts/knowledge/ideas on startup |

## Design notes

- **The fact-check gate is the product.** The pipeline refuses to advance a video into production while any claim lacks a verified source — the same integrity discipline as an evidence registry, applied to creator content. This is what makes AI-assisted production compatible with a trust-first brand.
- **AI is assistive, never autonomous.** Generators draft; state transitions are explicit human actions; nothing publishes itself.
- **Offline-first fallbacks** mean the team's workflow (and the test suite) never depends on API availability.
