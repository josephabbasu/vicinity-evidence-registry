# Phase 5 — AI Production System (Claude Code + CreatorOS)

## Design principles

1. **AI drafts, humans decide.** Every stage produces an artifact a human approves, edits, or rejects. Nothing auto-publishes.
2. **Verification is a gate, not a step.** A script cannot advance to voiceover until every factual claim has a source and a status of `verified` (enforced in CreatorOS — same discipline as an evidence registry).
3. **Everything is an auditable record.** Ideas, research memos, scripts, claims, sources, SEO metadata, and publish decisions live in one database (CreatorOS), so quality is inspectable and improvable.
4. **The pipeline is a state machine:** `idea → researched → scripted → fact_checked → voiced → edited → thumbnail → scheduled → published → analyzed`.

## Pipeline diagram

```
            ┌─────────────────────── CreatorOS (this repo) ───────────────────────┐
            │                                                                     │
 Trends ──▶ │ IDEA BANK ──▶ RESEARCH ──▶ SCRIPT ──▶ FACT-CHECK ──▶ PRODUCTION ──▶ │ ──▶ YouTube
 Comments ▶ │  (scored)     (Claude +    (Claude,    (claim-by-     (VO, edit,    │      │
 Search  ─▶ │               sources)     brand       claim gate,    thumbnail)    │      ▼
            │                            voice)      human ✓)                     │  ANALYTICS
            │        ▲                                                            │      │
            │        └────────────── FEEDBACK LOOP (retention, CTR, comments) ◀───┼──────┘
            └─────────────────────────────────────────────────────────────────────┘
```

## Stage-by-stage workflow

### 1. Research automation
- **Inputs:** trend keywords (CreatorOS Trend Detector), competitor gaps (Competitor Tracker), comment mining, seasonal calendar.
- **Claude Code tasks:** weekly batch job produces per-idea research memos: the question people are asking, top existing videos + their gaps, 8–15 candidate sources (official statistics, academic work, regulator publications, reputable journalism), key numbers with citations, localization notes ("this concept is called X in the UK, Y in India").
- **Human gate:** editor approves the memo, flags weak sources.
- **CreatorOS module:** Research Engine (stores memos, links sources to claims).

### 2. Script generation
- **Claude prompt stack (Prompt Library in CreatorOS):** brand-voice system prompt (Phase 3 voice table baked in) + video-type template (foundations / anatomy / verdict) + the approved research memo + retention structure: cold open hook (from hook bank) → stakes → 3-act explanation with a visual beat every 20–30s → "what we don't know" honesty beat → actionable takeaway → sequel hook.
- **Output:** two-column script (VO line | visual direction), timed, with `[CLAIM:n]` markers bound to sources.
- **Human gate:** editor rewrites for voice; host reads aloud once for cadence.

### 3. Fact verification (the moat)
- Every `[CLAIM:n]` becomes a row: claim text, source, quote/figure, verifier, status (`unverified → verified / corrected / cut`).
- A second Claude pass runs *adversarially*: "find any claim that is overstated, outdated, US-specific without labeling, or unsupported by its source."
- **Hard rule:** script blocked from production while any claim is `unverified`. Corrections post-publish go to pinned comment + description + a public corrections page.

### 4. Image / visual generation
- Chart data → chart specs rendered with the brand palette (paper/ink/green/amber); diagrams and object illustrations generated to a locked style prompt ("flat editorial illustration, ink on paper, single accent color"), then human-curated into an asset library for reuse (consistency + speed).
- B-roll: licensed stock only from an approved list; no AI photorealistic people (trust + policy safety).

### 5. Voiceover workflow
- **Primary (recommended):** human host records VO from final script — strongest authenticity, policy-proof, and the brand's voice asset. Target: 1 recording session covers 2 videos.
- **Assist:** Claude generates the read-optimized script (pronunciation notes, emphasis marks); a TTS scratch track is used for edit timing before the human record. Any synthetic voice use in published Shorts is disclosed per YouTube's altered-content rules.

### 6. Editing workflow
- Editor assembles against the two-column script (visual beats pre-decided = 40–60% edit time reduction).
- Checklist enforced in CreatorOS tasks: hook ≤ 5s to first payoff · pattern interrupt every 25–35s · numbers always shown in Plex Mono motif · citation footer on-screen per claim · end screen to the next Foundations episode.
- Shorts derived per long-form (3–5 vertical cutdowns) during the same edit session.

### 7. Thumbnail generation
- CreatorOS produces a thumbnail brief (template choice from the Phase 4 table + ≤4-word text + object). 2–3 variants produced; legibility check at 160×90; A/B via YouTube's Test & Compare.

### 8. Metadata optimization
- SEO Optimizer module scores titles (length, hook word, keyword position), writes descriptions (first 150 chars = search snippet; includes source list), tags, chapter markers, and hreflang-friendly multi-language titles/descriptions when auto-dub is enabled.

### 9. Scheduling
- Publishing Planner holds the calendar (Tue/Sat 14:00 UTC anchor), enforces series cadence and 3-week batch buffer, and tracks per-video status.

### 10. Analytics & feedback loops
- Weekly ingest of per-video metrics (CTR, average view duration, retention curve breakpoints, traffic sources, geo mix) into CreatorOS Analytics.
- Claude reviews the retention curves and comments monthly and writes a "what to change" memo: hooks that held, drop-off patterns, requested topics (fed back into Idea Bank with scores).
- Experiment log: every title/thumbnail test recorded with outcome → the title-template table gets empirical weights over time.

## Weekly operating rhythm (2-person team + pipeline)

| Day | Editor/Host | Pipeline (Claude Code, via CreatorOS) |
|---|---|---|
| Mon | Approve research memos; record VO ×2 | Generate next week's memos; adversarial fact-check pass |
| Tue | **Publish**; community post | Metadata + Shorts cutdown briefs |
| Wed | Edit video A | Script drafts for week+2 |
| Thu | Edit video B; thumbnail review | Trend scan; competitor deltas |
| Fri | Fact-check sign-offs; schedule | Analytics ingest; feedback memo |
| Sat | **Publish**; engage comments 60 min | Comment mining → Idea Bank |

## Compliance & disclosure

- On-video and channel-level disclosure: "Research and production assisted by AI; every video is human-verified and human-voiced."
- No individualized financial advice; education framing with jurisdiction disclaimer template in every description.
- Sponsor ethics screen (published): no payday lenders, no CFD/forex brokers, no crypto exchanges, no MLMs.
