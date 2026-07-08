# Plain Money — A YouTube Creator Business

**A complete, production-ready YouTube creator business: strategy, brand, content system, AI production pipeline, and software.**

This directory is self-contained and independent of the VICINITY evidence registry that lives at the repository root.

## What's here

| Path | Contents |
|---|---|
| `report/00-executive-summary.md` | Executive summary and final recommendation |
| `report/01-market-research.md` | Phase 1 — market analysis, evidence tables, rankings, decision matrix |
| `report/02-recommendation.md` | Phase 2 — the recommended business and why |
| `report/03-brand.md` | Phase 3 — full brand system |
| `report/04-content-strategy.md` | Phase 4 — pillars, 100 video ideas, 100 Shorts, hooks, titles, schedule |
| `report/05-production-system.md` | Phase 5 — AI production workflow built on Claude Code |
| `report/06-business-model.md` | Phase 7 — revenue streams and unit economics |
| `report/07-roadmap-and-risk.md` | Phase 8 — 30-day / 90-day / 1-year / 3-year roadmaps, KPIs, risks |
| `creator-os/` | Phase 6 — **CreatorOS**, the production application (FastAPI + React + Docker + tests + CI) |

## The one-paragraph version

Only about a third of adults worldwide are financially literate, money questions are among the most persistently searched topics on Earth, finance is the highest-CPM category on YouTube — and almost all finance content is US-centric, personality-driven, and untrustworthy at the margins. **Plain Money** is a principles-first, country-agnostic, evidence-cited money education channel for the global 90% that US finance YouTube ignores, produced by a human-reviewed AI pipeline (CreatorOS) that makes weekly long-form + daily Shorts sustainable for a small team.

## Quick start (the software)

```bash
cd creator-business/creator-os
docker compose up --build
# Frontend: http://localhost:5173   API: http://localhost:8000/docs
```

Or run natively — see `creator-os/README.md`.
