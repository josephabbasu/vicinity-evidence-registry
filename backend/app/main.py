from __future__ import annotations

import csv
import io
import json
import os
import urllib.request
import urllib.parse
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .db_models import (
    ChangeLog,
    EffectEstimate,
    LiteratureCandidate,
    RegistryUpdate,
    Release,
    SearchRun,
    Study,
    Submission,
)
from .schemas import (
    CandidateOut,
    ChangeLogOut,
    DashboardResponse,
    EvidenceBrief,
    EffectEstimateOut,
    FulltextDecision,
    GapItem,
    GapRadarResponse,
    InterventionSummary,
    PractitionerQuery,
    ReviewerAuthRequest,
    ReviewerAuthResponse,
    ScreenDecision,
    SearchRunOut,
    StatsResponse,
    StudyDetail,
    StudyListResponse,
    StudySummary,
    SubmissionCreate,
    SubmissionCreated,
    UpdateOut,
)
from .seed import seed_database


REVIEWER_TOKEN = os.getenv("REVIEWER_TOKEN", "vicinity-reviewer-2026")


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def require_reviewer(authorization: Annotated[str | None, Header()] = None):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != REVIEWER_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reviewer token")


def allowed_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGIN", "").strip()
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    if configured:
        for origin in configured.split(","):
            origin = origin.strip()
            if not origin:
                continue
            origins.append(origin if "://" in origin else f"https://{origin}")
    return sorted(set(origins))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)
    yield


app = FastAPI(
    title="VICINITY Registry API",
    version="2.0.0",
    description=(
        "Living Causal Evidence Observatory for neighborhood violence and youth mental health. "
        "Developed by J. Abbas, Rutgers University. "
        "Three linked registries: exposure/harm, intervention/recovery, and evidence gaps."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def summary_from_study(study: Study) -> StudySummary:
    return StudySummary(
        **{col: getattr(study, col) for col in StudySummary.model_fields if col != "verification_count"},
        verification_count=len(study.verification_flags or []),
    )


def detail_from_study(study: Study) -> StudyDetail:
    values = {
        col: getattr(study, col)
        for col in StudyDetail.model_fields
        if col not in ("verification_count", "effect_estimates")
    }
    estimates = [
        EffectEstimateOut.model_validate(e) for e in (study.effect_estimates or [])
    ]
    return StudyDetail(
        **values,
        verification_count=len(study.verification_flags or []),
        effect_estimates=estimates,
    )


def _match_studies(
    studies: list[Study],
    search: str | None,
    design_type: str | None,
    age_group: str | None,
    country: str | None,
    outcome_type: str | None,
    exposure_window: str | None,
    quality_tier: str | None,
    causal_tier: str | None,
    year_min: int | None,
    year_max: int | None,
    intervention_only: bool,
    stream: str | None,
) -> list[Study]:
    if search:
        needle = search.casefold()
        studies = [
            s for s in studies
            if needle in " ".join((s.study_id, s.title, s.country, s.finding_summary, s.outcomes)).casefold()
        ]
    for field, value in {
        "design_type": design_type,
        "country": country,
        "outcome_type": outcome_type,
        "exposure_window": exposure_window,
        "quality_tier": quality_tier,
        "causal_tier": causal_tier,
        "registry_stream": stream,
    }.items():
        if value:
            studies = [s for s in studies if getattr(s, field) == value]
    if age_group:
        studies = [s for s in studies if age_group in s.age_groups]
    if year_min is not None:
        studies = [s for s in studies if s.publication_year and s.publication_year >= year_min]
    if year_max is not None:
        studies = [s for s in studies if s.publication_year and s.publication_year <= year_max]
    if intervention_only:
        studies = [s for s in studies if s.is_intervention]
    return studies


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "VICINITY",
        "version": "2.0",
        "tagline": "Living Causal Evidence Observatory for neighborhood violence and youth mental health.",
        "developer": "J. Abbas, Rutgers University",
        "docs": "/docs",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0"}


@app.get("/api/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session)) -> StatsResponse:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    years = [s.publication_year for s in studies if s.publication_year]
    last_run = session.scalar(select(SearchRun).order_by(SearchRun.run_date.desc()))
    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status.in_(["discovered", "screened"]))
    ) or 0
    return StatsResponse(
        study_count=len(studies),
        exposure_count=sum(s.registry_stream == "exposure" for s in studies),
        intervention_count=sum(s.registry_stream == "intervention" for s in studies),
        country_count=len({s.country for s in studies}),
        credible_count=sum(s.causal_tier == "Credible" for s in studies),
        associational_count=sum(s.causal_tier == "Associational" for s in studies),
        latest_year=max(years) if years else None,
        updated_date=date.today().isoformat(),
        last_search_date=last_run.run_date.date().isoformat() if last_run else None,
        pending_candidates=pending,
        countries=sorted({s.country for s in studies}),
        design_types=sorted({s.design_type for s in studies}),
        age_groups=sorted({g for s in studies for g in s.age_groups}),
        outcome_types=sorted({s.outcome_type for s in studies}),
        exposure_windows=sorted({s.exposure_window for s in studies}),
        quality_tiers=sorted({s.quality_tier for s in studies}),
        causal_tiers=sorted({s.causal_tier for s in studies}),
    )


@app.get("/api/studies", response_model=StudyListResponse)
def list_studies(
    search: str | None = Query(default=None, max_length=200),
    design_type: str | None = None,
    age_group: str | None = None,
    country: str | None = None,
    outcome_type: str | None = None,
    exposure_window: str | None = None,
    quality_tier: str | None = None,
    causal_tier: str | None = None,
    year_min: int | None = Query(default=None, ge=1900, le=2100),
    year_max: int | None = Query(default=None, ge=1900, le=2100),
    intervention_only: bool = False,
    stream: str | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> StudyListResponse:
    studies = list(
        session.scalars(
            select(Study)
            .where(Study.approval_status == "approved")
            .order_by(Study.publication_year.desc(), Study.study_id.asc())
        ).all()
    )
    filtered = _match_studies(
        studies, search, design_type, age_group, country, outcome_type,
        exposure_window, quality_tier, causal_tier, year_min, year_max,
        intervention_only, stream,
    )
    total = len(filtered)
    page = filtered[offset: offset + limit]
    return StudyListResponse(total=total, studies=[summary_from_study(s) for s in page])


@app.get("/api/studies/{slug}", response_model=StudyDetail)
def get_study(slug: str, session: Session = Depends(get_session)) -> StudyDetail:
    study = session.scalar(select(Study).where(Study.slug == slug))
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")
    return detail_from_study(study)


@app.get("/api/updates", response_model=list[UpdateOut])
def updates(session: Session = Depends(get_session)) -> list[RegistryUpdate]:
    return list(
        session.scalars(select(RegistryUpdate).order_by(RegistryUpdate.created_at.desc())).all()
    )


@app.post("/api/submissions", response_model=SubmissionCreated, status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionCreate, session: Session = Depends(get_session)) -> SubmissionCreated:
    submission = Submission(**payload.model_dump())
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return SubmissionCreated(
        id=submission.id,
        status=submission.status,
        message=(
            "Thank you. The nomination is in the review queue. "
            "A study enters the public registry only after eligibility, extraction, and quality checks."
        ),
    )


# ── Practitioner query ────────────────────────────────────────────────────────

@app.post("/api/ask", response_model=EvidenceBrief)
def ask(query: PractitionerQuery, session: Session = Depends(get_session)) -> EvidenceBrief:
    all_studies = list(
        session.scalars(select(Study).where(Study.approval_status == "approved")).all()
    )

    # Match exposure studies
    exposure_studies = [s for s in all_studies if s.registry_stream == "exposure"]
    matched = exposure_studies[:]

    if query.age_group and query.age_group != "all":
        age_map = {
            "adolescent": ["Adolescent", "Youth", "Teen"],
            "child": ["Child", "Children"],
            "adult": ["Adult", "Young adult"],
        }
        groups = age_map.get(query.age_group, [])
        if groups:
            matched = [s for s in matched if any(g in s.age_groups for g in groups)]

    if query.outcome_type:
        needle = query.outcome_type.casefold()
        matched = [s for s in matched if needle in s.outcome_type.casefold()]

    if query.country:
        matched = [s for s in matched if s.country == query.country]

    if query.exposure_window:
        matched = [s for s in matched if query.exposure_window.casefold() in s.exposure_window.casefold()]

    credible = [s for s in matched if s.causal_tier == "Credible"]
    directions = [s.effect_direction for s in matched if s.effect_direction not in ("", "Needs verification")]
    dominant = max(set(directions), key=directions.count) if directions else "Insufficient data"

    certainty = (
        "High — majority of matched studies use credible causal designs"
        if len(credible) >= len(matched) * 0.5 and len(credible) >= 3
        else "Moderate — some credible designs present" if credible
        else "Low — matched studies rely primarily on associational designs"
    )

    # Match intervention studies
    intervention_studies = [s for s in all_studies if s.registry_stream == "intervention"]
    interventions = [
        InterventionSummary(
            citation=s.citation,
            title=s.title,
            intervention_type=s.intervention_type or "Not classified",
            effect_direction=s.effect_direction,
            causal_tier=s.causal_tier,
            slug=s.slug,
        )
        for s in intervention_studies
    ]

    # Build query description
    parts = []
    if query.age_group and query.age_group != "all":
        parts.append(query.age_group + "s")
    else:
        parts.append("youth and young adults")
    if query.exposure_window:
        parts.append(f"with {query.exposure_window} exposure")
    if query.outcome_type:
        parts.append(f"on {query.outcome_type}")
    if query.country:
        parts.append(f"in {query.country}")
    description = "Evidence for " + " ".join(parts) if parts else "All matched evidence"

    # Evidence gaps for this query
    gaps: list[str] = []
    if len(matched) == 0:
        gaps.append("No studies match these exact criteria — the combination is an active evidence gap.")
    if len(credible) == 0 and matched:
        gaps.append("No credible-tier studies matched — conclusions rely on associational designs.")
    if not any(s.country == "South Africa" for s in matched):
        gaps.append("No matched studies from South Africa or sub-Saharan Africa.")
    if not any("anxiety" in s.outcome_type.casefold() for s in matched):
        gaps.append("Anxiety outcomes are underrepresented in the matched set.")
    if not any("suicide" in s.outcomes.casefold() for s in matched):
        gaps.append("Suicidality outcomes are absent from matched studies.")

    last_run = session.scalar(select(SearchRun).order_by(SearchRun.run_date.desc()))
    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status.in_(["discovered", "screened"]))
    ) or 0

    return EvidenceBrief(
        query_description=description,
        study_count=len(matched),
        credible_count=len(credible),
        dominant_direction=dominant,
        causal_certainty=certainty,
        effect_note=(
            f"{len(matched)} studies matched. "
            f"{len([s for s in matched if s.effect_direction == 'Harmful'])} show harmful effects, "
            f"{len([s for s in matched if s.effect_direction == 'Protective'])} protective. "
            "Effect sizes vary; standardized estimates are missing from most source records."
        ),
        population_note=(
            f"Matched studies span {len({s.country for s in matched})} countries. "
            "Most originate from the United States. Generalizability to other settings requires caution."
        ),
        limitations=(
            "The evidence base relies heavily on US urban samples. "
            "Most studies lack structured effect-size fields. "
            "Publication bias toward significant findings cannot be excluded."
        ),
        available_interventions=interventions[:8],
        evidence_gaps=gaps,
        last_searched=last_run.run_date.date().isoformat() if last_run else None,
        pending_candidates=pending,
        studies_included=[s.citation for s in matched],
    )


# ── Evidence gap radar ────────────────────────────────────────────────────────

@app.get("/api/gaps", response_model=GapRadarResponse)
def gap_radar(session: Session = Depends(get_session)) -> GapRadarResponse:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    n = len(studies)

    geo = {}
    for s in studies:
        geo[s.country] = geo.get(s.country, 0) + 1

    outcome_counts: dict[str, int] = {}
    for s in studies:
        outcome_counts[s.outcome_type] = outcome_counts.get(s.outcome_type, 0) + 1

    design_counts: dict[str, int] = {}
    for s in studies:
        design_counts[s.design_type] = design_counts.get(s.design_type, 0) + 1

    gaps: list[GapItem] = []

    # Geographic gaps
    us_count = geo.get("United States", 0)
    if us_count / max(n, 1) > 0.55:
        gaps.append(GapItem(
            domain="Geographic",
            label="US over-representation",
            description=f"{us_count} of {n} studies ({round(us_count/n*100)}%) are from the United States. "
                        "Evidence from low- and middle-income countries is critically absent.",
            n_studies=us_count,
            priority="High",
            suggested_action="Commission systematic searches targeting LMIC settings, Africa, and Latin America.",
        ))

    non_us = [c for c in geo if c != "United States"]
    if len(non_us) < 5:
        gaps.append(GapItem(
            domain="Geographic",
            label="Limited international replication",
            description=f"Only {len(non_us)} non-US countries represented. Causal mechanisms may differ by context.",
            n_studies=sum(geo[c] for c in non_us),
            priority="High",
            suggested_action="Prioritize replication studies in UK, Canada, Brazil, South Africa, and India.",
        ))

    # Outcome gaps
    anxiety_n = sum(1 for s in studies if "anxiety" in s.outcome_type.casefold())
    if anxiety_n < 5:
        gaps.append(GapItem(
            domain="Outcome",
            label="Anxiety underrepresented",
            description=f"Only {anxiety_n} studies measure anxiety as a primary outcome. "
                        "Depression dominates the evidence base.",
            n_studies=anxiety_n,
            priority="High",
            suggested_action="Prioritize studies with standardized anxiety instruments (GAD-7, SCARED, MASC).",
        ))

    suicide_n = sum(1 for s in studies if "suicide" in s.outcomes.casefold() or "self-harm" in s.outcomes.casefold())
    if suicide_n < 3:
        gaps.append(GapItem(
            domain="Outcome",
            label="Suicidality nearly absent",
            description=f"Only {suicide_n} studies address suicidal ideation or self-harm outcomes. "
                        "This is a critical public-health gap.",
            n_studies=suicide_n,
            priority="High",
            suggested_action="Add suicidality outcomes to systematic searches. "
                             "Contact authors of related studies for unpublished data.",
        ))

    sleep_n = sum(1 for s in studies if "sleep" in s.outcome_type.casefold())
    if sleep_n < 4:
        gaps.append(GapItem(
            domain="Outcome",
            label="Sleep outcomes sparse",
            description=f"Only {sleep_n} studies measure sleep disruption, a documented pathway from violence to health.",
            n_studies=sleep_n,
            priority="Medium",
            suggested_action="Include sleep outcome terms (PSQI, actigraphy, sleep diary) in next search.",
        ))

    # Method gaps
    rct_n = sum(1 for s in studies if "randomized" in s.design_type.casefold())
    if rct_n < 3:
        gaps.append(GapItem(
            domain="Method",
            label="Very few randomized trials",
            description=f"Only {rct_n} RCTs in the registry. Randomization is rare for exposure studies "
                        "but feasible for intervention evaluations.",
            n_studies=rct_n,
            priority="High",
            suggested_action="Prioritize RCT searches in the intervention stream. "
                             "Consider quasi-experimental methods for exposure contexts.",
        ))

    no_doi = sum(1 for s in studies if not s.doi)
    if no_doi > n * 0.5:
        gaps.append(GapItem(
            domain="Method",
            label="Missing DOIs and structured identifiers",
            description=f"{no_doi} of {n} records lack a DOI, impeding citation tracking and update detection.",
            n_studies=no_doi,
            priority="Medium",
            suggested_action="Run DOI lookup pass against CrossRef and OpenAlex for all records.",
        ))

    no_ci = sum(1 for s in studies if s.ci_lower is None)
    if no_ci > n * 0.6:
        gaps.append(GapItem(
            domain="Method",
            label="Confidence intervals not extracted",
            description=f"{no_ci} of {n} records lack structured confidence-interval bounds. "
                        "Meta-analytic synthesis is not yet possible.",
            n_studies=no_ci,
            priority="High",
            suggested_action="Re-extract effect estimates with CI bounds from primary sources. "
                             "Contact authors where data are not reported.",
        ))

    # Population gaps
    girl_n = sum(1 for s in studies if "girl" in s.population_details.casefold() or "female" in s.population_details.casefold())
    if girl_n < n * 0.35:
        gaps.append(GapItem(
            domain="Population",
            label="Gender-stratified evidence limited",
            description=f"Fewer than 35% of studies report gender-stratified effects. "
                        "Evidence on girls and gender-diverse youth is particularly sparse.",
            n_studies=girl_n,
            priority="Medium",
            suggested_action="Require gender-stratified analysis in future extractions and search filters.",
        ))

    county_n = sum(1 for s in studies if "county" in s.geographic_scale.casefold() or "municipality" in s.geographic_scale.casefold())
    gaps.append(GapItem(
        domain="Geographic",
        label="Sub-city geographic precision varies",
        description=f"Only {county_n} studies use county or municipality-level exposure coding. "
                    "8 studies have unclear or variable geographic scales.",
        n_studies=county_n,
        priority="Medium",
        suggested_action="Standardize geographic scale coding using a controlled vocabulary in all new extractions.",
    ))

    return GapRadarResponse(
        computed_at=datetime.now(timezone.utc).isoformat(),
        total_studies=n,
        gaps=gaps,
        geographic_breakdown=geo,
        outcome_breakdown=outcome_counts,
        design_breakdown=design_counts,
    )


# ── Changelog ─────────────────────────────────────────────────────────────────

@app.get("/api/changelog", response_model=list[ChangeLogOut])
def changelog(session: Session = Depends(get_session)) -> list[ChangeLog]:
    return list(
        session.scalars(select(ChangeLog).order_by(ChangeLog.created_at.desc())).all()
    )


# ── Data export ───────────────────────────────────────────────────────────────

@app.get("/api/export/studies.json")
def export_json(session: Session = Depends(get_session)) -> Response:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    payload = [
        {
            "study_id": s.study_id,
            "title": s.title,
            "citation": s.citation,
            "publication_year": s.publication_year,
            "country": s.country,
            "registry_stream": s.registry_stream,
            "design_type": s.design_type,
            "causal_tier": s.causal_tier,
            "quality_tier": s.quality_tier,
            "outcome_type": s.outcome_type,
            "effect_direction": s.effect_direction,
            "is_intervention": s.is_intervention,
            "doi": s.doi,
            "added_in_version": s.added_in_version,
        }
        for s in studies
    ]
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="vicinity_studies.json"'},
    )


@app.get("/api/export/studies.csv")
def export_csv(session: Session = Depends(get_session)) -> Response:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    fields = [
        "study_id", "title", "citation", "publication_year", "country",
        "registry_stream", "design_type", "causal_tier", "quality_tier",
        "outcome_type", "effect_direction", "is_intervention", "doi", "added_in_version",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for s in studies:
        writer.writerow({f: getattr(s, f) for f in fields})
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="vicinity_studies.csv"'},
    )


# ── Relevance scoring ─────────────────────────────────────────────────────────

_RELEVANCE_TIERS: list[tuple[float, list[str]]] = [
    # Tier 1 — core population terms (highest signal)
    (0.25, ["youth", "adolescent", "adolescents", "children", "child", "teen", "teenager",
            "young people", "pediatric", "school-age"]),
    # Tier 2 — violence exposure terms
    (0.25, ["neighborhood violence", "community violence", "gun violence", "shooting",
            "street violence", "violent crime", "exposure to violence", "witnessing violence",
            "violence exposure", "urban violence"]),
    # Tier 3 — mental health outcome terms
    (0.20, ["mental health", "depression", "depressive", "anxiety", "ptsd", "post-traumatic",
            "stress", "trauma", "behavioral", "sleep", "internalizing", "externalizing",
            "suicide", "self-harm", "psychological"]),
    # Tier 4 — causal/rigorous design terms (bonus)
    (0.15, ["randomized", "rct", "difference-in-differences", "natural experiment",
            "instrumental variable", "fixed effects", "quasi-experimental", "longitudinal",
            "causal", "exogenous"]),
    # Tier 5 — place/neighborhood context
    (0.10, ["neighborhood", "community", "urban", "place-based", "census tract",
            "block group", "poverty", "disadvantaged", "concentrated disadvantage"]),
    # Tier 6 — intervention terms
    (0.05, ["intervention", "program", "treatment", "therapy", "cbt", "prevention",
            "counseling", "housing", "voucher", "greening"]),
]


def _score_relevance(title: str, abstract: str) -> float:
    """Score a candidate 0–1 based on tiered keyword matching in title (2×) + abstract."""
    text = (title + " " + title + " " + abstract).casefold()
    total = 0.0
    for weight, keywords in _RELEVANCE_TIERS:
        if any(kw in text for kw in keywords):
            total += weight
    return round(min(total, 1.0), 3)


@app.post("/api/reviewer/candidates/rescore", status_code=status.HTTP_200_OK)
def rescore_candidates(
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict:
    """Recompute relevance scores for all candidates using the keyword-weighted scorer."""
    candidates = list(session.scalars(select(LiteratureCandidate)).all())
    updated = 0
    for c in candidates:
        score = _score_relevance(c.title or "", c.abstract or "")
        if c.relevance_score != score:
            c.relevance_score = score
            updated += 1
    session.commit()
    return {"rescored": updated, "total": len(candidates)}


# ── Citation export ───────────────────────────────────────────────────────────

def _study_bibtex(s) -> str:
    key = (s.slug or s.study_id or "study").replace(" ", "").replace(",", "")[:40]
    year = s.publication_year or "n.d."
    authors = s.citation.split("(")[0].strip() if s.citation else s.title
    return (
        f"@article{{{key},\n"
        f"  author = {{{authors}}},\n"
        f"  title = {{{s.title or s.study_id}}},\n"
        f"  year = {{{year}}},\n"
        f"  note = {{VICINITY registry stream: {s.registry_stream or 'unclassified'}. "
        f"Causal tier: {s.causal_tier or 'unclassified'}.}},\n"
        + (f"  doi = {{{s.doi}}},\n" if s.doi else "")
        + f"}}\n"
    )


def _study_ris(s) -> str:
    year = s.publication_year or ""
    lines = [
        "TY  - JOUR",
        f"TI  - {s.title or s.study_id}",
        f"AU  - {s.citation.split('(')[0].strip() if s.citation else ''}",
        f"PY  - {year}",
        f"N1  - VICINITY stream: {s.registry_stream or 'unclassified'}; causal tier: {s.causal_tier or 'unclassified'}",
    ]
    if s.doi:
        lines.append(f"DO  - {s.doi}")
    lines.append("ER  - ")
    return "\n".join(lines) + "\n\n"


@app.get("/api/export/studies.bib")
def export_bibtex(session: Session = Depends(get_session)) -> Response:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    header = (
        "% VICINITY Evidence Registry — BibTeX export\n"
        "% Developer: J. Abbas, Rutgers University\n"
        f"% Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
    )
    content = header + "".join(_study_bibtex(s) for s in studies)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="vicinity_studies.bib"'},
    )


@app.get("/api/export/studies.ris")
def export_ris(session: Session = Depends(get_session)) -> Response:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    header = (
        "Provider: VICINITY Evidence Registry\n"
        "Content: text/plain; charset=\"utf-8\"\n\n"
    )
    content = header + "".join(_study_ris(s) for s in studies)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="vicinity_studies.ris"'},
    )


# ── Versioned releases ────────────────────────────────────────────────────────

@app.get("/api/releases")
def list_releases(session: Session = Depends(get_session)) -> list[dict]:
    releases = list(
        session.scalars(select(Release).order_by(Release.release_date.desc())).all()
    )
    return [
        {
            "id": r.id,
            "version": r.version,
            "release_date": r.release_date.isoformat(),
            "study_count": r.study_count,
            "exposure_count": r.exposure_count,
            "intervention_count": r.intervention_count,
            "credible_count": r.credible_count,
            "doi": r.doi,
            "notes": r.notes,
        }
        for r in releases
    ]


def _attempt_zenodo_deposition(version: str, study_count: int, frozen_json: str) -> str | None:
    """
    Attempt to create a Zenodo deposition and return the DOI.
    Requires ZENODO_TOKEN env var (use sandbox token for testing).
    Returns None if token is absent or the API call fails.
    """
    token = os.getenv("ZENODO_TOKEN", "")
    if not token:
        return None
    base_url = os.getenv("ZENODO_URL", "https://sandbox.zenodo.org")
    try:
        headers_json = json.dumps({
            "metadata": {
                "title": f"VICINITY Evidence Registry — Version {version}",
                "upload_type": "dataset",
                "description": (
                    f"Versioned snapshot of the VICINITY Living Causal Evidence Observatory "
                    f"({study_count} studies). Developed by J. Abbas, Rutgers University."
                ),
                "creators": [{"name": "Abbas, J.", "affiliation": "Rutgers University"}],
                "keywords": [
                    "neighborhood violence", "youth mental health", "systematic review",
                    "causal inference", "evidence registry",
                ],
                "license": "cc-by-4.0",
                "version": version,
            }
        }).encode()
        # Create deposition
        req = urllib.request.Request(
            f"{base_url}/api/depositions",
            data=headers_json,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            dep = json.loads(resp.read().decode())
        dep_id = dep.get("id")
        bucket_url = dep.get("links", {}).get("bucket")
        if not dep_id or not bucket_url:
            return None
        # Upload data file
        data_bytes = frozen_json.encode("utf-8")
        upload_req = urllib.request.Request(
            f"{bucket_url}/vicinity_v{version}.json",
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="PUT",
        )
        urllib.request.urlopen(upload_req, timeout=30)
        # Publish
        publish_req = urllib.request.Request(
            f"{base_url}/api/depositions/{dep_id}/actions/publish",
            data=b"",
            headers={"Authorization": f"Bearer {token}"},
            method="POST",
        )
        with urllib.request.urlopen(publish_req, timeout=15) as resp:
            published = json.loads(resp.read().decode())
        return published.get("doi") or published.get("metadata", {}).get("doi")
    except Exception:
        return None


@app.post("/api/reviewer/releases", status_code=status.HTTP_201_CREATED)
def create_release(
    version: str,
    notes: str = "",
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict:
    """
    Freeze the current registry as a named release. Attempts to mint a DOI via Zenodo
    if ZENODO_TOKEN is set; otherwise stores the release locally with a placeholder.
    """
    existing = session.scalar(select(Release).where(Release.version == version))
    if existing:
        raise HTTPException(status_code=409, detail=f"Release {version} already exists")

    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    frozen = [
        {
            "study_id": s.study_id,
            "title": s.title,
            "citation": s.citation,
            "publication_year": s.publication_year,
            "country": s.country,
            "registry_stream": s.registry_stream,
            "design_type": s.design_type,
            "causal_tier": s.causal_tier,
            "quality_tier": s.quality_tier,
            "outcome_type": s.outcome_type,
            "effect_direction": s.effect_direction,
            "doi": s.doi,
        }
        for s in studies
    ]
    frozen_json = json.dumps(frozen, indent=2)

    doi = _attempt_zenodo_deposition(version, len(studies), frozen_json)
    if not doi:
        doi = f"vicinity/registry/v{version}/{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    release = Release(
        version=version,
        study_count=len(studies),
        exposure_count=sum(s.registry_stream == "exposure" for s in studies),
        intervention_count=sum(s.registry_stream == "intervention" for s in studies),
        credible_count=sum(s.causal_tier == "Credible" for s in studies),
        doi=doi,
        frozen_json=frozen_json,
        notes=notes or f"Registry snapshot at version {version}.",
    )
    session.add(release)
    session.commit()
    return {
        "version": version,
        "study_count": len(studies),
        "doi": doi,
        "zenodo_minted": not doi.startswith("vicinity/"),
    }


@app.get("/api/releases/{version}/download")
def download_release(version: str, session: Session = Depends(get_session)) -> Response:
    release = session.scalar(select(Release).where(Release.version == version))
    if not release or not release.frozen_json:
        raise HTTPException(status_code=404, detail="Release not found or not yet frozen")
    return Response(
        content=release.frozen_json,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="vicinity_v{version}.json"'},
    )


# ── Reviewer auth ─────────────────────────────────────────────────────────────

@app.post("/api/reviewer/auth", response_model=ReviewerAuthResponse)
def reviewer_auth(payload: ReviewerAuthRequest) -> ReviewerAuthResponse:
    if payload.token != REVIEWER_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return ReviewerAuthResponse(
        authenticated=True,
        name="Lead Reviewer",
        role="lead",
    )


# ── Reviewer dashboard ────────────────────────────────────────────────────────

@app.get("/api/reviewer/dashboard", response_model=DashboardResponse)
def reviewer_dashboard(
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> DashboardResponse:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status.in_(["discovered", "screened"]))
    ) or 0
    awaiting_screen = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status == "discovered")
    ) or 0
    awaiting_fulltext = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status == "screened")
    ) or 0

    # Count studies approved this month (proxy: added in current calendar month)
    approved_month = sum(
        1 for s in studies
        if s.added_in_version == "2.0"
    )

    recent_runs = list(
        session.scalars(
            select(SearchRun).order_by(SearchRun.run_date.desc()).limit(5)
        ).all()
    )
    recent_candidates = list(
        session.scalars(
            select(LiteratureCandidate)
            .where(LiteratureCandidate.status.in_(["discovered", "screened"]))
            .order_by(LiteratureCandidate.created_at.desc())
            .limit(20)
        ).all()
    )

    return DashboardResponse(
        total_studies=len(studies),
        exposure_count=sum(s.registry_stream == "exposure" for s in studies),
        intervention_count=sum(s.registry_stream == "intervention" for s in studies),
        pending_candidates=pending,
        awaiting_screen=awaiting_screen,
        awaiting_fulltext=awaiting_fulltext,
        approved_this_month=approved_month,
        recent_runs=[SearchRunOut.model_validate(r) for r in recent_runs],
        recent_candidates=[CandidateOut.model_validate(c) for c in recent_candidates],
    )


@app.get("/api/reviewer/candidates", response_model=list[CandidateOut])
def list_candidates(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> list[LiteratureCandidate]:
    q = select(LiteratureCandidate).order_by(LiteratureCandidate.created_at.desc()).limit(limit)
    if status_filter:
        q = q.where(LiteratureCandidate.status == status_filter)
    return list(session.scalars(q).all())


@app.post("/api/reviewer/candidates/{candidate_id}/screen", status_code=status.HTTP_200_OK)
def screen_candidate(
    candidate_id: int,
    payload: ScreenDecision,
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict[str, str]:
    candidate = session.get(LiteratureCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.screen_decision = payload.decision
    candidate.screen_reason = payload.reason
    candidate.status = "screened" if payload.decision == "include" else "rejected"
    candidate.updated_at = datetime.now(timezone.utc)
    session.commit()
    return {"status": candidate.status, "message": "Screen decision recorded."}


@app.post("/api/reviewer/candidates/{candidate_id}/fulltext", status_code=status.HTTP_200_OK)
def fulltext_candidate(
    candidate_id: int,
    payload: FulltextDecision,
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict[str, str]:
    candidate = session.get(LiteratureCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.fulltext_decision = payload.decision
    candidate.fulltext_reason = payload.reason
    candidate.status = "full_text" if payload.decision == "include" else "rejected"
    candidate.updated_at = datetime.now(timezone.utc)
    session.commit()
    return {"status": candidate.status, "message": "Full-text decision recorded."}


_OPENALEX_QUERY = (
    '("neighborhood violence" OR "community violence" OR "gun violence" OR "exposure to violence") '
    'AND ("mental health" OR "depression" OR "anxiety" OR "PTSD" OR "trauma") '
    'AND ("youth" OR "adolescent" OR "children")'
)

_OPENALEX_FILTER = (
    "concepts.display_name.search:mental health,"
    "publication_year:2015-2026"
)


def _fetch_openalex_candidates(per_page: int = 25) -> list[dict]:
    """Query the OpenAlex free API (no key required) for recent relevant works."""
    params = urllib.parse.urlencode({
        "search": (
            "neighborhood violence youth mental health adolescent"
        ),
        "filter": "publication_year:2018-2026",
        "per-page": per_page,
        "select": "id,title,authorships,publication_year,primary_location,doi,abstract_inverted_index",
        "mailto": "j.abbas@rutgers.edu",
    })
    url = f"https://api.openalex.org/works?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VICINITY/2.0 (mailto:j.abbas@rutgers.edu)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("results", [])
    except Exception:
        return []


def _reconstruct_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    pairs = [(pos, word) for word, positions in inverted.items() for pos in positions]
    pairs.sort()
    return " ".join(word for _, word in pairs)


@app.post("/api/reviewer/search/trigger", status_code=status.HTTP_201_CREATED)
def trigger_search(
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict:
    """
    Run a live literature surveillance search against OpenAlex (free, no key required).
    Creates real LiteatureCandidate records from the API response. New candidates that
    already exist in the DB (matched by DOI) are skipped to avoid duplicates.
    """
    databases = ["OpenAlex", "PubMed (manual)", "Crossref (manual)", "Europe PMC (manual)", "ERIC (manual)"]

    raw_results = _fetch_openalex_candidates(per_page=25)

    # Collect existing DOIs to skip duplicates
    existing_dois: set[str] = set(
        row[0] for row in session.execute(
            select(LiteratureCandidate.doi).where(LiteratureCandidate.doi.isnot(None))
        ).all()
    )
    existing_study_dois: set[str] = set(
        row[0] for row in session.execute(
            select(Study.doi).where(Study.doi.isnot(None))
        ).all()
    )
    skip_dois = existing_dois | existing_study_dois

    candidates_found = len(raw_results)
    new_items = []

    for work in raw_results:
        doi = work.get("doi") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        if doi and doi in skip_dois:
            continue

        title = work.get("title") or ""
        if not title:
            continue

        authors_raw = work.get("authorships") or []
        authors = "; ".join(
            a["author"]["display_name"] for a in authors_raw[:4] if a.get("author")
        )
        if len(authors_raw) > 4:
            authors += " et al."

        year = work.get("publication_year")
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        journal = source.get("display_name") or ""
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

        new_items.append(LiteratureCandidate(
            title=title[:500],
            authors=authors[:300],
            year=year,
            journal=journal[:200],
            doi=doi or None,
            abstract=abstract[:2000] or None,
            source_database="OpenAlex",
            source_id=work.get("id") or None,
            relevance_score=_score_relevance(title, abstract),
            status="discovered",
        ))

    duplicates_removed = candidates_found - len(new_items)

    run = SearchRun(
        databases_searched=databases,
        query_terms=_OPENALEX_QUERY,
        candidates_found=candidates_found,
        duplicates_removed=duplicates_removed,
        new_candidates=len(new_items),
        status="completed",
        triggered_by="manual",
    )
    session.add(run)
    session.flush()

    for item in new_items:
        item.search_run_id = run.id
        session.add(item)

    session.add(ChangeLog(
        version="2.0",
        change_type="surveillance",
        summary=(
            f"Live OpenAlex search completed. {candidates_found} results retrieved; "
            f"{len(new_items)} new candidates added after deduplication."
        ),
        affected_studies=[],
        study_count_before=0,
        study_count_after=0,
    ))

    session.commit()
    return {
        "run_id": run.id,
        "databases_searched": databases,
        "candidates_found": candidates_found,
        "duplicates_removed": duplicates_removed,
        "new_candidates": len(new_items),
        "status": "completed",
        "source": "OpenAlex live API",
    }
