from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .admin_schemas import (
    CandidateDecisionRequest,
    CandidateListResponse,
    DeactivateStudyRequest,
    EligibilityResultOut,
    IngestionEventOut,
    IngestionRunOut,
    IngestionRunRequest,
    IngestionStatusOut,
    RegistryStudyAdminOut,
    StudyCandidateDetail,
    StudyCandidateOut,
)
from .database import SessionLocal
from .db_models import (
    ChangeLog,
    EligibilityResult,
    IngestionCursor,
    IngestionEvent,
    IngestionRun,
    Study,
    StudyCandidate,
)
from .ingestion.pipeline import (
    IngestionPipeline,
    build_default_clients,
    env_flag,
    utc_now,
)


REVIEWER_TOKEN = os.getenv("REVIEWER_TOKEN", "").strip()
INGESTION_TOKEN = (
    os.getenv("INGESTION_TOKEN", "").strip()
    or os.getenv("SURVEILLANCE_TOKEN", "").strip()
)


def get_admin_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def require_admin(
    authorization: Annotated[str | None, Header()] = None,
    ingestion_token: Annotated[
        str | None, Header(alias="X-Ingestion-Token")
    ] = None,
) -> None:
    bearer_valid = False
    if authorization and REVIEWER_TOKEN:
        scheme, _, token = authorization.partition(" ")
        bearer_valid = (
            scheme.casefold() == "bearer"
            and secrets.compare_digest(token, REVIEWER_TOKEN)
        )
    scheduler_valid = bool(
        ingestion_token
        and INGESTION_TOKEN
        and secrets.compare_digest(ingestion_token, INGESTION_TOKEN)
    )
    if not bearer_valid and not scheduler_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid administrator or ingestion credentials are required.",
        )


router = APIRouter(
    prefix="/admin",
    tags=["living evidence administration"],
    dependencies=[Depends(require_admin)],
)


def _current_result(
    session: Session,
    candidate_id: int,
) -> EligibilityResult | None:
    return session.scalar(
        select(EligibilityResult)
        .where(
            EligibilityResult.candidate_id == candidate_id,
            EligibilityResult.is_current.is_(True),
        )
        .order_by(EligibilityResult.created_at.desc())
    )


def _result_out(result: EligibilityResult | None) -> EligibilityResultOut | None:
    return EligibilityResultOut.model_validate(result) if result else None


def _candidate_out(
    session: Session,
    candidate: StudyCandidate,
) -> StudyCandidateOut:
    return StudyCandidateOut(
        id=candidate.id,
        source=candidate.source,
        source_id=candidate.source_id,
        title=candidate.title,
        authors=candidate.authors,
        year=candidate.year,
        journal=candidate.journal,
        doi=candidate.doi,
        abstract=candidate.abstract,
        source_url=candidate.source_url,
        pdf_url=candidate.pdf_url,
        status=candidate.status,
        duplicate_of_id=candidate.duplicate_of_id,
        registered_study_id=candidate.registered_study_id,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        eligibility=_result_out(_current_result(session, candidate.id)),
    )


@router.get("/ingestion/candidates", response_model=CandidateListResponse)
def list_candidates(
    decision: str | None = None,
    source: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_admin_session),
) -> CandidateListResponse:
    statement = select(StudyCandidate)
    if decision:
        statement = statement.join(
            EligibilityResult,
            (EligibilityResult.candidate_id == StudyCandidate.id)
            & EligibilityResult.is_current.is_(True),
        ).where(EligibilityResult.decision == decision)
    if source:
        statement = statement.where(StudyCandidate.source == source)
    if date_from:
        statement = statement.where(StudyCandidate.created_at >= date_from)
    if date_to:
        statement = statement.where(StudyCandidate.created_at <= date_to)
    candidates = list(
        session.scalars(
            statement.order_by(StudyCandidate.updated_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
    count_statement = select(func.count()).select_from(StudyCandidate)
    if decision:
        count_statement = count_statement.join(
            EligibilityResult,
            (EligibilityResult.candidate_id == StudyCandidate.id)
            & EligibilityResult.is_current.is_(True),
        ).where(EligibilityResult.decision == decision)
    if source:
        count_statement = count_statement.where(StudyCandidate.source == source)
    if date_from:
        count_statement = count_statement.where(StudyCandidate.created_at >= date_from)
    if date_to:
        count_statement = count_statement.where(StudyCandidate.created_at <= date_to)
    total = session.scalar(count_statement) or 0
    return CandidateListResponse(
        total=total,
        candidates=[_candidate_out(session, candidate) for candidate in candidates],
    )


@router.get(
    "/ingestion/candidates/{candidate_id}",
    response_model=StudyCandidateDetail,
)
def get_candidate(
    candidate_id: int,
    session: Session = Depends(get_admin_session),
) -> StudyCandidateDetail:
    candidate = session.get(StudyCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    summary = _candidate_out(session, candidate)
    history = list(
        session.scalars(
            select(EligibilityResult)
            .where(EligibilityResult.candidate_id == candidate.id)
            .order_by(EligibilityResult.created_at.desc())
        ).all()
    )
    return StudyCandidateDetail(
        **summary.model_dump(),
        keywords=candidate.keywords or [],
        raw_metadata=candidate.raw_metadata or {},
        history=[EligibilityResultOut.model_validate(item) for item in history],
    )


@router.post(
    "/ingestion/candidates/{candidate_id}/decision",
    response_model=StudyCandidateDetail,
)
def decide_candidate(
    candidate_id: int,
    payload: CandidateDecisionRequest,
    session: Session = Depends(get_admin_session),
) -> StudyCandidateDetail:
    candidate = session.get(StudyCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    pipeline = IngestionPipeline(session)
    pipeline.override_candidate(
        candidate,
        decision=payload.decision,
        reviewer=payload.reviewer,
        reason=payload.reason,
    )
    session.commit()
    return get_candidate(candidate_id, session)


@router.post(
    "/ingestion/candidates/{candidate_id}/rerun",
    response_model=StudyCandidateDetail,
)
def rerun_candidate(
    candidate_id: int,
    session: Session = Depends(get_admin_session),
) -> StudyCandidateDetail:
    candidate = session.get(StudyCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    IngestionPipeline(session).classify_candidate(candidate)
    session.commit()
    return get_candidate(candidate_id, session)


def _run_background_ingestion(
    run_id: int,
    triggered_by: str,
    sources: list[str] | None,
) -> None:
    with SessionLocal() as session:
        run = session.get(IngestionRun, run_id)
        if run is None:
            return
        try:
            IngestionPipeline(session).run(
                triggered_by=triggered_by,
                selected_sources=sources,
                existing_run=run,
            )
        except Exception as exc:
            session.rollback()
            failed_run = session.get(IngestionRun, run_id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.completed_at = utc_now()
                failed_run.error_count += 1
                failed_run.errors = [
                    *list(failed_run.errors or []),
                    {"source": "pipeline", "error": str(exc)[:1000]},
                ]
                session.commit()


@router.post("/ingestion/run", response_model=IngestionRunOut)
def run_ingestion(
    background_tasks: BackgroundTasks,
    payload: IngestionRunRequest | None = None,
    session: Session = Depends(get_admin_session),
) -> IngestionRun:
    active_run = session.scalar(
        select(IngestionRun)
        .where(
            IngestionRun.status.in_(["queued", "running"]),
            IngestionRun.started_at >= utc_now() - timedelta(hours=6),
        )
        .order_by(IngestionRun.started_at.desc())
    )
    if active_run is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ingestion run {active_run.id} is already in progress.",
        )
    request = payload or IngestionRunRequest()
    if request.background:
        sources = request.sources or list(build_default_clients())
        queued_run = IngestionRun(
            status="queued",
            triggered_by=request.triggered_by,
            sources=sources,
        )
        session.add(queued_run)
        session.commit()
        session.refresh(queued_run)
        background_tasks.add_task(
            _run_background_ingestion,
            queued_run.id,
            request.triggered_by,
            request.sources,
        )
        return queued_run
    pipeline = IngestionPipeline(session)
    return pipeline.run(
        triggered_by=request.triggered_by,
        selected_sources=request.sources,
    )


@router.get("/ingestion/runs", response_model=list[IngestionRunOut])
def list_ingestion_runs(
    limit: int = Query(default=25, ge=1, le=250),
    session: Session = Depends(get_admin_session),
) -> list[IngestionRun]:
    return list(
        session.scalars(
            select(IngestionRun)
            .order_by(IngestionRun.started_at.desc())
            .limit(limit)
        ).all()
    )


@router.get(
    "/ingestion/runs/{run_id}/events",
    response_model=list[IngestionEventOut],
)
def list_ingestion_events(
    run_id: int,
    session: Session = Depends(get_admin_session),
) -> list[IngestionEvent]:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found.")
    return list(
        session.scalars(
            select(IngestionEvent)
            .where(IngestionEvent.run_id == run_id)
            .order_by(IngestionEvent.created_at.asc())
        ).all()
    )


@router.get("/registry/studies/new", response_model=list[RegistryStudyAdminOut])
def list_new_registry_studies(
    limit: int = Query(default=50, ge=1, le=250),
    session: Session = Depends(get_admin_session),
) -> list[Study]:
    return list(
        session.scalars(
            select(Study)
            .where(Study.automation_status == "auto_registered")
            .order_by(Study.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.get(
    "/registry/studies/{study_id}",
    response_model=RegistryStudyAdminOut,
)
def get_registry_study(
    study_id: int,
    session: Session = Depends(get_admin_session),
) -> Study:
    study = session.get(Study, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found.")
    return study


@router.post(
    "/registry/studies/{study_id}/deactivate",
    response_model=RegistryStudyAdminOut,
)
def deactivate_registry_study(
    study_id: int,
    payload: DeactivateStudyRequest,
    session: Session = Depends(get_admin_session),
) -> Study:
    study = session.get(Study, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found.")
    if study.is_active:
        before = session.scalar(
            select(func.count())
            .select_from(Study)
            .where(Study.approval_status == "approved", Study.is_active.is_(True))
        ) or 0
        study.is_active = False
        study.updated_at = utc_now()
        session.add(
            ChangeLog(
                version=f"living-{utc_now().date().isoformat()}",
                change_type="retraction",
                summary=(
                    f"{payload.reviewer} deactivated {study.title}. "
                    f"Reason: {payload.reason}"
                ),
                affected_studies=[study.study_id],
                study_count_before=before,
                study_count_after=max(0, before - 1),
            )
        )
        session.commit()
        session.refresh(study)
    return study


@router.get("/status/ingestion", response_model=IngestionStatusOut)
def ingestion_status(
    session: Session = Depends(get_admin_session),
) -> IngestionStatusOut:
    latest_run = session.scalar(
        select(IngestionRun).order_by(IngestionRun.started_at.desc())
    )
    counts = {
        status_name: count
        for status_name, count in session.execute(
            select(StudyCandidate.status, func.count())
            .group_by(StudyCandidate.status)
        ).all()
    }
    cursors = {
        cursor.source: cursor.cursor_value
        for cursor in session.scalars(select(IngestionCursor)).all()
    }
    clients = build_default_clients()
    return IngestionStatusOut(
        latest_run=(
            IngestionRunOut.model_validate(latest_run) if latest_run else None
        ),
        candidate_counts=counts,
        cursors=cursors,
        source_configuration={
            source: bool(getattr(client, "configured", False))
            for source, client in clients.items()
        },
        auto_registration_enabled=env_flag("AUTO_REGISTER_ELIGIBLE", True),
    )
