from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .db_models import RegistryUpdate, Study, Submission
from .schemas import (
    StatsResponse,
    StudyDetail,
    StudyListResponse,
    StudySummary,
    SubmissionCreate,
    SubmissionCreated,
    UpdateOut,
)
from .seed import seed_database


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def allowed_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGIN", "").strip()
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
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
    version="1.0.0",
    description="Causal evidence registry for neighborhood violence and youth mental health.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def summary_from_study(study: Study) -> StudySummary:
    return StudySummary(
        **{
            column: getattr(study, column)
            for column in StudySummary.model_fields
            if column != "verification_count"
        },
        verification_count=len(study.verification_flags or []),
    )


def detail_from_study(study: Study) -> StudyDetail:
    values = {
        column: getattr(study, column)
        for column in StudyDetail.model_fields
        if column != "verification_count"
    }
    return StudyDetail(
        **values,
        verification_count=len(study.verification_flags or []),
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "VICINITY",
        "tagline": "What the best evidence actually shows. Updated as it happens.",
        "docs": "/docs",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session)) -> StatsResponse:
    studies = list(session.scalars(select(Study)).all())
    years = [study.publication_year for study in studies if study.publication_year]
    return StatsResponse(
        study_count=len(studies),
        country_count=len({study.country for study in studies}),
        credible_count=sum(study.causal_tier == "Credible" for study in studies),
        associational_count=sum(study.causal_tier == "Associational" for study in studies),
        intervention_count=sum(study.is_intervention for study in studies),
        latest_year=max(years) if years else None,
        updated_date=date.today().isoformat(),
        countries=sorted({study.country for study in studies}),
        design_types=sorted({study.design_type for study in studies}),
        age_groups=sorted({group for study in studies for group in study.age_groups}),
        outcome_types=sorted({study.outcome_type for study in studies}),
        exposure_windows=sorted({study.exposure_window for study in studies}),
        quality_tiers=sorted({study.quality_tier for study in studies}),
        causal_tiers=sorted({study.causal_tier for study in studies}),
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
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> StudyListResponse:
    studies = list(
        session.scalars(
            select(Study).order_by(Study.publication_year.desc(), Study.study_id.asc())
        ).all()
    )

    if search:
        needle = search.casefold()
        studies = [
            study
            for study in studies
            if needle
            in " ".join(
                (
                    study.study_id,
                    study.title,
                    study.country,
                    study.finding_summary,
                    study.outcomes,
                )
            ).casefold()
        ]
    exact_filters = {
        "design_type": design_type,
        "country": country,
        "outcome_type": outcome_type,
        "exposure_window": exposure_window,
        "quality_tier": quality_tier,
        "causal_tier": causal_tier,
    }
    for field, value in exact_filters.items():
        if value:
            studies = [study for study in studies if getattr(study, field) == value]
    if age_group:
        studies = [study for study in studies if age_group in study.age_groups]
    if year_min is not None:
        studies = [
            study
            for study in studies
            if study.publication_year is not None and study.publication_year >= year_min
        ]
    if year_max is not None:
        studies = [
            study
            for study in studies
            if study.publication_year is not None and study.publication_year <= year_max
        ]
    if intervention_only:
        studies = [study for study in studies if study.is_intervention]

    total = len(studies)
    page = studies[offset : offset + limit]
    return StudyListResponse(total=total, studies=[summary_from_study(study) for study in page])


@app.get("/api/studies/{slug}", response_model=StudyDetail)
def get_study(slug: str, session: Session = Depends(get_session)) -> StudyDetail:
    study = session.scalar(select(Study).where(Study.slug == slug))
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")
    return detail_from_study(study)


@app.get("/api/updates", response_model=list[UpdateOut])
def updates(session: Session = Depends(get_session)) -> list[RegistryUpdate]:
    return list(
        session.scalars(
            select(RegistryUpdate).order_by(RegistryUpdate.created_at.desc())
        ).all()
    )


@app.post(
    "/api/submissions",
    response_model=SubmissionCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    payload: SubmissionCreate,
    session: Session = Depends(get_session),
) -> SubmissionCreated:
    submission = Submission(**payload.model_dump())
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return SubmissionCreated(
        id=submission.id,
        status=submission.status,
        message=(
            "Thank you. The nomination is in the review queue. A study enters the public "
            "registry only after eligibility, extraction, and quality checks."
        ),
    )
