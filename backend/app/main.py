from __future__ import annotations

import csv
import io
import json
import os
import re
import secrets
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
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
    ReviewDecision,
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
    GapItem,
    GapRadarResponse,
    InterventionSummary,
    PractitionerQuery,
    ReviewerAuthRequest,
    ReviewerAuthResponse,
    ReviewDecisionCreate,
    SearchRunOut,
    StatsResponse,
    StudyDetail,
    StudyListResponse,
    StudySummary,
    SubmissionCreate,
    SubmissionCreated,
    UpdateOut,
)
from .migrations import run_additive_migrations
from .seed import seed_database


REVIEWER_TOKEN = os.getenv("REVIEWER_TOKEN", "").strip()
SURVEILLANCE_TOKEN = os.getenv("SURVEILLANCE_TOKEN", "").strip()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def require_reviewer(authorization: Annotated[str | None, Header()] = None):
    if not REVIEWER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reviewer access is not configured.",
        )
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token, REVIEWER_TOKEN):
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
    run_additive_migrations(engine)
    with SessionLocal() as session:
        seed_database(session)
    yield


app = FastAPI(
    title="VICINITY Registry API",
    version="2.0.0",
    description=(
        "Living Causal Evidence Observatory for neighborhood violence and youth mental health. "
        "Scientific concept, development, and stewardship by Joseph Abbas, "
        "Rutgers University-Camden. Software implementation supported by OpenAI Codex. "
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
        "developer": "Joseph Abbas, Rutgers University-Camden",
        "implementation_support": "OpenAI Codex",
        "docs": "/docs",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0"}


@app.get("/api/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session)) -> StatsResponse:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())
    years = [s.publication_year for s in studies if s.publication_year]
    last_run = session.scalar(
        select(SearchRun)
        .where(SearchRun.coverage_end_date.is_not(None))
        .order_by(SearchRun.coverage_end_date.desc())
    )
    pending_statuses = [
        "discovered",
        "awaiting_second_screen",
        "screened",
        "awaiting_second_fulltext",
        "conflict",
    ]
    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status.in_(pending_statuses))
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
        last_search_date=(
            last_run.coverage_end_date.isoformat()
            if last_run and last_run.coverage_end_date
            else None
        ),
        pending_candidates=pending,
        direct_mental_health_count=sum(
            s.outcome_directness == "Direct mental-health outcome"
            for s in studies
        ),
        structural_intervention_count=sum(
            s.intervention_class == "Structural"
            for s in studies
        ),
        psychosocial_intervention_count=sum(
            s.intervention_class == "Psychosocial"
            for s in studies
        ),
        exposure_reduction_count=sum(
            s.outcome_directness == "Exposure-reduction outcome"
            for s in studies
        ),
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
            "adolescent": ["Adolescents 10-17"],
            "child": ["Children 0-9"],
            "adult": ["Young adults 18-29", "Adults 30+"],
        }
        groups = age_map.get(query.age_group, [])
        if groups:
            matched = [s for s in matched if any(g in s.age_groups for g in groups)]

    if query.exposure_type and query.exposure_type != "general":
        needle = query.exposure_type.casefold()
        matched = [
            s for s in matched
            if needle in f"{s.exposure_type} {s.exposure_measure} {s.exposure_window_raw}".casefold()
        ]

    if query.outcome_type:
        needle = query.outcome_type.casefold()
        matched = [
            s for s in matched
            if needle in f"{s.outcome_type} {s.outcomes} {s.outcome_measure}".casefold()
        ]

    if query.country:
        matched = [s for s in matched if s.country == query.country]

    if query.exposure_window:
        matched = [s for s in matched if query.exposure_window.casefold() in s.exposure_window.casefold()]

    credible = [s for s in matched if s.causal_tier == "Credible"]
    directions = [s.effect_direction for s in matched if s.effect_direction not in ("", "Needs verification")]
    dominant = max(set(directions), key=directions.count) if directions else "Insufficient data"

    if not matched:
        certainty = "No directly matched evidence"
    elif len(credible) >= 3 and len(credible) >= len(matched) * 0.5:
        certainty = "Convergent credible evidence"
    elif credible:
        certainty = "Credible evidence with important limitations"
    else:
        certainty = "Associational evidence only"

    intervention_studies = [s for s in all_studies if s.registry_stream == "intervention"]
    if query.age_group and query.age_group != "all":
        groups = age_map.get(query.age_group, [])
        if groups:
            intervention_studies = [
                s for s in intervention_studies
                if any(g in s.age_groups for g in groups)
            ]
    if query.outcome_type:
        needle = query.outcome_type.casefold()
        direct_matches = [
            s for s in intervention_studies
            if needle in f"{s.outcome_type} {s.outcomes} {s.outcome_measure}".casefold()
        ]
        if direct_matches:
            intervention_studies = direct_matches
    intervention_studies.sort(
        key=lambda s: (
            s.outcome_directness != "Direct mental-health outcome",
            s.causal_tier != "Credible",
            -(s.publication_year or 0),
        )
    )
    interventions = [
        InterventionSummary(
            citation=s.citation,
            title=s.title,
            intervention_type=s.intervention_type or "Not classified",
            effect_direction=s.effect_direction,
            causal_tier=s.causal_tier,
            slug=s.slug,
            evidence_role=s.evidence_role,
            outcome_directness=s.outcome_directness,
            decision_relevance=s.decision_relevance,
        )
        for s in intervention_studies
    ]

    parts = []
    if query.age_group and query.age_group != "all":
        parts.append(query.age_group + "s")
    else:
        parts.append("youth and young adults")
    if query.exposure_type and query.exposure_type != "general":
        parts.append(f"exposed to {query.exposure_type}")
    if query.exposure_window:
        parts.append(f"with {query.exposure_window} exposure")
    if query.outcome_type:
        parts.append(f"on {query.outcome_type}")
    if query.country:
        parts.append(f"in {query.country}")
    description = "Evidence for " + " ".join(parts) if parts else "All matched evidence"

    gaps: list[str] = []
    if len(matched) == 0:
        gaps.append("No approved exposure study matches this exact combination.")
    if len(credible) == 0 and matched:
        gaps.append("No credible-tier study matched. The result relies on associational evidence.")
    if matched and not any(s.country not in ("United States", "Multiple countries") for s in matched):
        gaps.append("The matched evidence does not include a clearly identified non-US setting.")
    if not any("anxiety" in s.outcome_type.casefold() for s in matched):
        gaps.append("Anxiety outcomes are underrepresented in the matched set.")
    if not any("suicide" in s.outcomes.casefold() for s in matched):
        gaps.append("Suicidality outcomes are absent from matched studies.")

    last_run = session.scalar(
        select(SearchRun)
        .where(SearchRun.coverage_end_date.is_not(None))
        .order_by(SearchRun.coverage_end_date.desc())
    )
    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(
            LiteratureCandidate.status.in_(
                [
                    "discovered",
                    "awaiting_second_screen",
                    "screened",
                    "awaiting_second_fulltext",
                    "conflict",
                ]
            )
        )
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
            "The registry does not estimate a pooled effect. Publication bias remains possible."
        ),
        available_interventions=interventions[:10],
        evidence_gaps=gaps,
        last_searched=(
            last_run.coverage_end_date.isoformat()
            if last_run and last_run.coverage_end_date
            else None
        ),
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

    stream_counts: dict[str, int] = {}
    directness_counts: dict[str, int] = {}
    intervention_counts: dict[str, int] = {}
    for s in studies:
        stream_counts[s.registry_stream] = stream_counts.get(s.registry_stream, 0) + 1
        directness_counts[s.outcome_directness] = directness_counts.get(s.outcome_directness, 0) + 1
        if s.registry_stream == "intervention":
            intervention_counts[s.intervention_class] = intervention_counts.get(s.intervention_class, 0) + 1

    gaps: list[GapItem] = []

    # Geographic gaps
    us_count = geo.get("United States", 0)
    if us_count / max(n, 1) > 0.55:
        gaps.append(GapItem(
            domain="Geographic",
            label="US over-representation",
            description=f"{us_count} of {n} studies ({round(us_count/n*100)}%) are from the United States. "
                        "The registry cannot assume that these findings transfer to other policy settings.",
            n_studies=us_count,
            priority="High",
            suggested_action="Prioritize studies from low- and middle-income settings and test cross-setting transportability.",
        ))

    non_us = [c for c in geo if c != "United States"]
    if len(non_us) < 5:
        gaps.append(GapItem(
            domain="Geographic",
            label="Limited international replication",
            description=f"Only {len(non_us)} non-US countries represented. Causal mechanisms may differ by context.",
            n_studies=sum(geo[c] for c in non_us),
            priority="High",
            suggested_action="Prioritize replication in countries that are absent from the current registry.",
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
    if rct_n < 5:
        gaps.append(GapItem(
            domain="Method",
            label="Few randomized trials",
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

    direct_interventions = sum(
        1
        for s in studies
        if s.registry_stream == "intervention"
        and s.outcome_directness == "Direct mental-health outcome"
    )
    intervention_n = stream_counts.get("intervention", 0)
    if direct_interventions < intervention_n:
        gaps.append(GapItem(
            domain="Outcome",
            label="Intervention outcomes do not always measure mental health directly",
            description=(
                f"{direct_interventions} of {intervention_n} intervention records measure a direct "
                "mental-health outcome. The remaining records assess exposure reduction, pathways, "
                "or outcomes that require verification."
            ),
            n_studies=direct_interventions,
            priority="High",
            suggested_action=(
                "Commission intervention studies that measure both violence exposure and validated "
                "mental-health outcomes over time."
            ),
        ))

    county_n = sum(
        1
        for s in studies
        if "county" in s.geographic_scale.casefold()
        or "municipality" in s.geographic_scale.casefold()
    )
    unclear_scale_n = sum(
        1
        for s in studies
        if not s.geographic_scale
        or "unclear" in s.geographic_scale.casefold()
        or "variable" in s.geographic_scale.casefold()
        or "verification" in s.geographic_scale.casefold()
    )
    gaps.append(GapItem(
        domain="Geographic",
        label="Sub-city geographic precision varies",
        description=f"Only {county_n} studies use county or municipality-level exposure coding. "
                    f"{unclear_scale_n} studies have unclear or variable geographic scales.",
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
        stream_breakdown=stream_counts,
        directness_breakdown=directness_counts,
        intervention_breakdown=intervention_counts,
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
            "evidence_role": s.evidence_role,
            "intervention_class": s.intervention_class,
            "outcome_directness": s.outcome_directness,
            "decision_relevance": s.decision_relevance,
            "source_review": s.source_review,
            "search_coverage_end": s.search_coverage_end,
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
        "outcome_type", "effect_direction", "evidence_role", "intervention_class",
        "outcome_directness", "decision_relevance", "source_review",
        "search_coverage_end", "is_intervention", "doi", "added_in_version",
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
    # Tier 1: core population terms.
    (0.25, ["youth", "adolescent", "adolescents", "children", "child", "teen", "teenager",
            "young people", "pediatric", "school-age"]),
    # Tier 2: violence exposure terms.
    (0.25, ["neighborhood violence", "community violence", "gun violence", "shooting",
            "street violence", "violent crime", "exposure to violence", "witnessing violence",
            "violence exposure", "urban violence"]),
    # Tier 3: mental health outcome terms.
    (0.20, ["mental health", "depression", "depressive", "anxiety", "ptsd", "post-traumatic",
            "stress", "trauma", "behavioral", "sleep", "internalizing", "externalizing",
            "suicide", "self-harm", "psychological"]),
    # Tier 4: stronger causal design terms.
    (0.15, ["randomized", "rct", "difference-in-differences", "natural experiment",
            "instrumental variable", "fixed effects", "quasi-experimental", "longitudinal",
            "causal", "exogenous"]),
    # Tier 5: place and neighborhood context.
    (0.10, ["neighborhood", "community", "urban", "place-based", "census tract",
            "block group", "poverty", "disadvantaged", "concentrated disadvantage"]),
    # Tier 6: intervention terms.
    (0.05, ["intervention", "program", "treatment", "therapy", "cbt", "prevention",
            "counseling", "housing", "voucher", "greening"]),
]


def _score_relevance(title: str, abstract: str) -> float:
    """Score a candidate from 0 to 1 with tiered title and abstract terms."""
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
        "% VICINITY Evidence Registry: BibTeX export\n"
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
                "title": f"VICINITY Evidence Registry: Version {version}",
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
    if not REVIEWER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reviewer access is not configured.",
        )
    if not secrets.compare_digest(payload.token, REVIEWER_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return ReviewerAuthResponse(
        authenticated=True,
        name="Registry reviewer",
        role="reviewer",
    )


# ── Reviewer dashboard ────────────────────────────────────────────────────────

@app.get("/api/reviewer/dashboard", response_model=DashboardResponse)
def reviewer_dashboard(
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> DashboardResponse:
    studies = list(session.scalars(select(Study).where(Study.approval_status == "approved")).all())

    pending_statuses = [
        "discovered",
        "awaiting_second_screen",
        "screened",
        "awaiting_second_fulltext",
        "conflict",
    ]
    pending = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(LiteratureCandidate.status.in_(pending_statuses))
    ) or 0
    awaiting_screen = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(
            LiteratureCandidate.status.in_(
                ["discovered", "awaiting_second_screen", "conflict"]
            )
        )
    ) or 0
    awaiting_fulltext = session.scalar(
        select(func.count()).select_from(LiteratureCandidate)
        .where(
            LiteratureCandidate.status.in_(
                ["screened", "awaiting_second_fulltext"]
            )
        )
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
            .where(LiteratureCandidate.status.in_(pending_statuses))
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


def _aggregate_decisions(
    candidate: LiteratureCandidate,
    stage: str,
    decisions: list[ReviewDecision],
) -> str:
    latest_by_reviewer: dict[str, ReviewDecision] = {}
    for decision in decisions:
        latest_by_reviewer[decision.reviewer_name.casefold()] = decision

    independent = list(latest_by_reviewer.values())
    if len(independent) < 2:
        status_value = (
            "awaiting_second_screen"
            if stage == "screen"
            else "awaiting_second_fulltext"
        )
    else:
        values = {decision.decision for decision in independent}
        if values == {"include"}:
            status_value = "screened" if stage == "screen" else "full_text"
        elif values == {"exclude"}:
            status_value = "rejected"
        else:
            status_value = "conflict"

    combined_reason = " | ".join(
        f"{decision.reviewer_name}: {decision.reason}"
        for decision in independent
    )
    combined_decision = (
        independent[0].decision
        if independent and len({item.decision for item in independent}) == 1
        else "conflict"
    )
    if stage == "screen":
        candidate.screen_decision = combined_decision
        candidate.screen_reason = combined_reason
    else:
        candidate.fulltext_decision = combined_decision
        candidate.fulltext_reason = combined_reason
    candidate.status = status_value
    candidate.updated_at = datetime.now(timezone.utc)
    return status_value


@app.post(
    "/api/reviewer/candidates/{candidate_id}/decisions",
    status_code=status.HTTP_200_OK,
)
def record_review_decision(
    candidate_id: int,
    payload: ReviewDecisionCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_reviewer),
) -> dict:
    candidate = session.get(LiteratureCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if payload.stage == "fulltext" and candidate.status not in {
        "screened",
        "awaiting_second_fulltext",
        "conflict",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Two screen reviewers must include the record before full-text review.",
        )

    normalized_reviewer = " ".join(payload.reviewer_name.split())
    existing = session.scalar(
        select(ReviewDecision).where(
            ReviewDecision.candidate_id == candidate_id,
            ReviewDecision.stage == payload.stage,
            func.lower(ReviewDecision.reviewer_name) == normalized_reviewer.casefold(),
        )
    )
    if existing:
        existing.decision = payload.decision
        existing.reason = payload.reason.strip()
        existing.reviewer_name = normalized_reviewer
        existing.created_at = datetime.now(timezone.utc)
    else:
        session.add(
            ReviewDecision(
                candidate_id=candidate_id,
                stage=payload.stage,
                decision=payload.decision,
                reason=payload.reason.strip(),
                reviewer_name=normalized_reviewer,
            )
        )
    session.flush()

    decisions = list(
        session.scalars(
            select(ReviewDecision)
            .where(
                ReviewDecision.candidate_id == candidate_id,
                ReviewDecision.stage == payload.stage,
            )
            .order_by(ReviewDecision.created_at.asc())
        ).all()
    )
    aggregate_status = _aggregate_decisions(candidate, payload.stage, decisions)
    session.commit()
    return {
        "status": aggregate_status,
        "stage": payload.stage,
        "decision_count": len(
            {decision.reviewer_name.casefold() for decision in decisions}
        ),
        "message": "Independent review decision recorded.",
    }


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
    Run source-derived literature surveillance for the uncovered date interval.
    """
    return run_surveillance(session, triggered_by="manual")


SURVEILLANCE_QUERY = (
    '("neighborhood violence" OR "community violence" OR "gun violence" '
    'OR "violent crime" OR "exposure to violence") '
    'AND (youth OR adolescent OR adolescents OR child OR children) '
    'AND ("mental health" OR depression OR anxiety OR PTSD OR trauma '
    'OR intervention OR prevention)'
)


def _normalize_doi(value: str | None) -> str:
    doi = (value or "").strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip()


def _title_key(title: str, year: int | None) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
    return f"{normalized}|{year or ''}"


def _xml_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def _http_json(url: str, user_agent: str = "VICINITY/2.0") -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_pubmed_candidates(
    start_date: date,
    end_date: date,
    limit: int = 200,
) -> list[dict]:
    search_params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "term": SURVEILLANCE_QUERY,
            "retmode": "json",
            "retmax": limit,
            "datetype": "pdat",
            "mindate": start_date.isoformat(),
            "maxdate": end_date.isoformat(),
        }
    )
    search_data = _http_json(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{search_params}",
        "VICINITY/2.0 (j.abbas@rutgers.edu)",
    )
    identifiers = search_data.get("esearchresult", {}).get("idlist", [])
    if not identifiers:
        return []

    fetch_params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": ",".join(identifiers),
            "retmode": "xml",
        }
    )
    request = urllib.request.Request(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{fetch_params}",
        headers={"User-Agent": "VICINITY/2.0 (j.abbas@rutgers.edu)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())

    records: list[dict] = []
    for article in root.findall(".//PubmedArticle"):
        citation = article.find("./MedlineCitation")
        article_node = citation.find("./Article") if citation is not None else None
        if article_node is None:
            continue
        pmid = _xml_text(citation.find("./PMID"))
        title = _xml_text(article_node.find("./ArticleTitle"))
        if not title:
            continue
        abstract = " ".join(
            _xml_text(node)
            for node in article_node.findall("./Abstract/AbstractText")
        ).strip()
        authors = []
        for author in article_node.findall("./AuthorList/Author"):
            collective = _xml_text(author.find("./CollectiveName"))
            personal = " ".join(
                part
                for part in (
                    _xml_text(author.find("./ForeName")),
                    _xml_text(author.find("./LastName")),
                )
                if part
            )
            if collective or personal:
                authors.append(collective or personal)
        journal = _xml_text(article_node.find("./Journal/Title"))
        year_text = (
            _xml_text(article_node.find("./Journal/JournalIssue/PubDate/Year"))
            or _xml_text(article_node.find("./Journal/JournalIssue/PubDate/MedlineDate"))
        )
        year_match = re.search(r"(19|20)\d{2}", year_text)
        doi = ""
        for identifier in article.findall("./PubmedData/ArticleIdList/ArticleId"):
            if identifier.attrib.get("IdType") == "doi":
                doi = _xml_text(identifier)
                break
        records.append(
            {
                "title": title,
                "authors": "; ".join(authors[:8]) + (" et al." if len(authors) > 8 else ""),
                "year": int(year_match.group()) if year_match else None,
                "journal": journal,
                "doi": _normalize_doi(doi),
                "abstract": abstract,
                "source_database": "PubMed",
                "source_id": pmid,
                "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            }
        )
    return records


def _fetch_crossref_candidates(
    start_date: date,
    end_date: date,
    limit: int = 200,
) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "query.bibliographic": (
                "neighborhood community violence youth adolescent mental health "
                "depression anxiety trauma intervention"
            ),
            "filter": (
                f"from-pub-date:{start_date.isoformat()},"
                f"until-pub-date:{end_date.isoformat()},type:journal-article"
            ),
            "rows": limit,
            "select": "DOI,title,author,published,container-title,abstract,URL",
            "mailto": "j.abbas@rutgers.edu",
        }
    )
    data = _http_json(
        f"https://api.crossref.org/works?{params}",
        "VICINITY/2.0 (mailto:j.abbas@rutgers.edu)",
    )
    records: list[dict] = []
    for item in data.get("message", {}).get("items", []):
        title = " ".join(item.get("title") or []).strip()
        if not title:
            continue
        authors = "; ".join(
            " ".join(part for part in (author.get("given", ""), author.get("family", "")) if part)
            for author in (item.get("author") or [])[:8]
        )
        date_parts = (item.get("published") or {}).get("date-parts") or []
        year = date_parts[0][0] if date_parts and date_parts[0] else None
        abstract = re.sub(r"<[^>]+>", " ", item.get("abstract") or "")
        records.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": " ".join(item.get("container-title") or []),
                "doi": _normalize_doi(item.get("DOI")),
                "abstract": " ".join(abstract.split()),
                "source_database": "Crossref",
                "source_id": item.get("DOI") or "",
                "source_url": item.get("URL") or "",
            }
        )
    return records


def _fetch_openalex_interval(
    start_date: date,
    end_date: date,
    limit: int = 200,
) -> list[dict]:
    api_key = os.getenv("OPENALEX_API_KEY", "").strip()
    if not api_key:
        return []
    params = urllib.parse.urlencode(
        {
            "search": "neighborhood violence youth mental health intervention",
            "filter": (
                f"from_publication_date:{start_date.isoformat()},"
                f"to_publication_date:{end_date.isoformat()}"
            ),
            "per-page": limit,
            "api_key": api_key,
            "select": (
                "id,title,authorships,publication_year,primary_location,"
                "doi,abstract_inverted_index"
            ),
        }
    )
    data = _http_json(f"https://api.openalex.org/works?{params}")
    records: list[dict] = []
    for work in data.get("results", []):
        title = work.get("title") or ""
        if not title:
            continue
        authorships = work.get("authorships") or []
        authors = "; ".join(
            entry.get("author", {}).get("display_name", "")
            for entry in authorships[:8]
            if entry.get("author", {}).get("display_name")
        )
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        records.append(
            {
                "title": title,
                "authors": authors,
                "year": work.get("publication_year"),
                "journal": source.get("display_name") or "",
                "doi": _normalize_doi(work.get("doi")),
                "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
                "source_database": "OpenAlex",
                "source_id": work.get("id") or "",
                "source_url": work.get("id") or "",
            }
        )
    return records


def run_surveillance(session: Session, triggered_by: str) -> dict:
    latest_coverage = session.scalar(
        select(func.max(SearchRun.coverage_end_date))
        .where(SearchRun.status == "completed")
    )
    start_date = (latest_coverage or date(2025, 7, 31)) + timedelta(days=1)
    end_date = date.today()
    if start_date > end_date:
        return {
            "run_id": None,
            "databases_searched": [],
            "candidates_found": 0,
            "duplicates_removed": 0,
            "new_candidates": 0,
            "status": "up_to_date",
            "coverage_start": start_date.isoformat(),
            "coverage_end": end_date.isoformat(),
            "source": "No uncovered date interval",
        }

    source_fetchers = [
        ("PubMed", _fetch_pubmed_candidates),
        ("Crossref", _fetch_crossref_candidates),
    ]
    if os.getenv("OPENALEX_API_KEY", "").strip():
        source_fetchers.append(("OpenAlex", _fetch_openalex_interval))

    raw_records: list[dict] = []
    searched: list[str] = []
    errors: list[str] = []
    for source_name, fetcher in source_fetchers:
        try:
            raw_records.extend(fetcher(start_date, end_date))
            searched.append(source_name)
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as error:
            errors.append(f"{source_name}: {type(error).__name__}")
        except Exception as error:
            errors.append(f"{source_name}: {type(error).__name__}")

    unique_records: dict[str, dict] = {}
    for record in raw_records:
        doi = _normalize_doi(record.get("doi"))
        key = f"doi:{doi}" if doi else f"title:{_title_key(record['title'], record.get('year'))}"
        existing = unique_records.get(key)
        if not existing or len(record.get("abstract") or "") > len(existing.get("abstract") or ""):
            record["doi"] = doi
            unique_records[key] = record

    existing_keys: set[str] = set()
    for doi, title, year in session.execute(
        select(LiteratureCandidate.doi, LiteratureCandidate.title, LiteratureCandidate.year)
    ):
        normalized_doi = _normalize_doi(doi)
        existing_keys.add(
            f"doi:{normalized_doi}"
            if normalized_doi
            else f"title:{_title_key(title, year)}"
        )
    for doi, title, year in session.execute(select(Study.doi, Study.title, Study.publication_year)):
        normalized_doi = _normalize_doi(doi)
        existing_keys.add(
            f"doi:{normalized_doi}"
            if normalized_doi
            else f"title:{_title_key(title, year)}"
        )

    new_records: list[dict] = []
    existing_duplicates = 0
    for key, record in unique_records.items():
        if key in existing_keys:
            existing_duplicates += 1
            continue
        score = _score_relevance(record["title"], record.get("abstract") or "")
        record["relevance_score"] = score
        new_records.append(record)

    duplicates_removed = (
        len(raw_records) - len(unique_records) + existing_duplicates
    )
    if len(searched) == len(source_fetchers):
        run_status = "completed"
    elif searched:
        run_status = "partial"
    else:
        run_status = "failed"
    run = SearchRun(
        coverage_end_date=end_date if run_status == "completed" else None,
        databases_searched=searched,
        query_terms=SURVEILLANCE_QUERY,
        candidates_found=len(raw_records),
        duplicates_removed=duplicates_removed,
        new_candidates=len(new_records),
        status=run_status,
        notes="; ".join(errors),
        triggered_by=triggered_by,
    )
    session.add(run)
    session.flush()

    for record in new_records:
        session.add(
            LiteratureCandidate(
                search_run_id=run.id,
                title=record["title"][:1000],
                authors=(record.get("authors") or "")[:1000],
                year=record.get("year"),
                journal=(record.get("journal") or "")[:500],
                doi=record.get("doi") or None,
                abstract=(record.get("abstract") or "")[:10000],
                source_database=record["source_database"],
                source_id=(record.get("source_id") or "")[:180],
                source_url=(record.get("source_url") or "")[:2000],
                relevance_score=record["relevance_score"],
                status="discovered",
            )
        )

    session.add(
        ChangeLog(
            version="2.0",
            change_type="surveillance",
            summary=(
                f"Surveillance covered {start_date.isoformat()} through {end_date.isoformat()}. "
                f"{len(raw_records)} source records yielded {len(new_records)} review candidates."
            ),
            affected_studies=[],
            study_count_before=0,
            study_count_after=0,
        )
    )
    session.commit()
    return {
        "run_id": run.id,
        "databases_searched": searched,
        "candidates_found": len(raw_records),
        "duplicates_removed": duplicates_removed,
        "new_candidates": len(new_records),
        "status": run_status,
        "coverage_start": start_date.isoformat(),
        "coverage_end": end_date.isoformat(),
        "source": ", ".join(searched) if searched else "No source completed",
        "errors": errors,
    }


def require_surveillance_token(
    x_surveillance_token: Annotated[str | None, Header()] = None,
) -> None:
    if not SURVEILLANCE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduled surveillance is not configured.",
        )
    if not x_surveillance_token or not secrets.compare_digest(
        x_surveillance_token,
        SURVEILLANCE_TOKEN,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid surveillance token.",
        )


@app.post("/api/surveillance/run", status_code=status.HTTP_201_CREATED)
def scheduled_surveillance(
    session: Session = Depends(get_session),
    _: None = Depends(require_surveillance_token),
) -> dict:
    return run_surveillance(session, triggered_by="scheduled")
