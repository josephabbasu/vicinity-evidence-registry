from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .db_models import (
    ChangeLog,
    EffectEstimate,
    LiteratureCandidate,
    RegistryUpdate,
    Release,
    SearchRun,
    Study,
)


DATA_DIR = Path(__file__).resolve().parent / "data"
EXPOSURE_SEED_PATH = DATA_DIR / "studies.json"
INTERVENTION_SEED_PATH = DATA_DIR / "intervention_studies.json"

SYNTHETIC_CANDIDATE_DOIS = {
    "10.1002/jts.23001",
    "10.1016/S2468-2667(24)00115-3",
    "10.1016/j.sleep.2024.03.021",
    "10.1176/appi.ps.20240118",
    "10.3102/00028312231159821",
    "10.1016/j.jue.2024.103592",
}


def _load_records(path: Path) -> list[dict]:
    if not path.exists():
        raise RuntimeError(f"Required seed file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _study_values(record: dict) -> dict:
    values = dict(record)
    values.pop("id", None)
    return values


def _upsert_study(session: Session, record: dict) -> Study:
    values = _study_values(record)
    study = session.scalar(
        select(Study).where(Study.study_id == values["study_id"])
    )
    if study is None:
        study = session.scalar(
            select(Study).where(Study.slug == values["slug"])
        )
    if study is None:
        study = Study(**values)
        session.add(study)
    else:
        for field, value in values.items():
            setattr(study, field, value)
    return study


def _replace_effect_estimates(session: Session, study: Study) -> None:
    """Store only effect statistics that are explicitly structured in the source."""

    session.execute(
        delete(EffectEstimate).where(EffectEstimate.study_id == study.id)
    )
    if (
        study.standardized_effect_size is None
        and study.ci_lower is None
        and study.ci_upper is None
    ):
        return
    session.add(
        EffectEstimate(
            study_id=study.id,
            outcome_label=study.outcome_type,
            outcome_instrument=study.outcome_measure,
            population_subgroup=study.age_range,
            exposure_contrast=study.exposure_measure,
            follow_up_period=study.outcome_timepoint,
            estimate_type="Standardized effect",
            point_estimate=study.standardized_effect_size,
            standard_error=None,
            ci_lower=study.ci_lower,
            ci_upper=study.ci_upper,
            p_value=None,
            adjustment_variables="",
            causal_estimand=study.estimand,
            source_table="Structured workbook field",
            rob_rating=study.quality_tier,
            is_primary=True,
        )
    )


def _upsert_changelog(session: Session) -> None:
    entries = [
        {
            "version": "2.0",
            "change_type": "addition",
            "summary": (
                "VICINITY Version 2.0 combined 32 exposure-consequence studies "
                "with 26 intervention studies. It added separate decision views, "
                "source provenance, an evidence-gap radar, independent review "
                "decisions, and literature surveillance."
            ),
            "affected_studies": ["26 intervention studies from Paper 2"],
            "study_count_before": 32,
            "study_count_after": 58,
        },
        {
            "version": "1.0",
            "change_type": "addition",
            "summary": (
                "VICINITY Version 1.0 launched with 32 studies from the "
                "causal-inference extraction workbook."
            ),
            "affected_studies": [],
            "study_count_before": 0,
            "study_count_after": 32,
        },
    ]
    for values in entries:
        existing = session.scalar(
            select(ChangeLog).where(
                ChangeLog.version == values["version"],
                ChangeLog.change_type == values["change_type"],
            )
        )
        if existing is None:
            session.add(ChangeLog(**values))
        else:
            for field, value in values.items():
                setattr(existing, field, value)


def _upsert_search_baseline(session: Session) -> None:
    existing = session.scalar(
        select(SearchRun).where(
            SearchRun.triggered_by == "systematic-review-import"
        )
    )
    values = {
        "coverage_end_date": date(2025, 7, 31),
        "databases_searched": [
            "PubMed",
            "Scopus",
            "Web of Science",
            "PsycINFO",
            "Google Scholar",
        ],
        "query_terms": (
            "Registered systematic-review strategies for youth, violence "
            "exposure, mental-health outcomes, and credible causal designs."
        ),
        "candidates_found": 0,
        "duplicates_removed": 0,
        "new_candidates": 0,
        "status": "completed",
        "notes": (
            "Historical search coverage imported from the two systematic "
            "reviews. Candidate counts remain in the PRISMA records."
        ),
        "triggered_by": "systematic-review-import",
    }
    if existing is None:
        session.add(SearchRun(**values))
    else:
        for field, value in values.items():
            setattr(existing, field, value)


def _snapshot(records: list[dict]) -> str:
    fields = (
        "study_id",
        "title",
        "citation",
        "publication_year",
        "country",
        "registry_stream",
        "evidence_role",
        "outcome_directness",
        "design_type",
        "causal_tier",
        "quality_tier",
        "outcome_type",
        "effect_direction",
        "doi",
    )
    return json.dumps(
        [{field: record.get(field) for field in fields} for record in records],
        indent=2,
        ensure_ascii=False,
    )


def _upsert_releases(
    session: Session,
    exposure_records: list[dict],
    intervention_records: list[dict],
) -> None:
    all_records = exposure_records + intervention_records
    releases = [
        {
            "version": "1.0",
            "study_count": 32,
            "exposure_count": 32,
            "intervention_count": 0,
            "credible_count": sum(
                record["causal_tier"] == "Credible"
                for record in exposure_records
            ),
            "frozen_json": _snapshot(exposure_records),
            "notes": (
                "Initial 32-study causal-exposure release. Search coverage "
                "ended July 31, 2025."
            ),
        },
        {
            "version": "2.0",
            "study_count": 58,
            "exposure_count": 32,
            "intervention_count": 26,
            "credible_count": sum(
                record["causal_tier"] == "Credible"
                for record in all_records
            ),
            "frozen_json": _snapshot(all_records),
            "notes": (
                "Combined evidence observatory release with 32 exposure studies "
                "and 26 intervention studies."
            ),
        },
    ]
    for values in releases:
        existing = session.scalar(
            select(Release).where(Release.version == values["version"])
        )
        if existing is None:
            session.add(Release(**values))
        else:
            for field, value in values.items():
                setattr(existing, field, value)


def _upsert_updates(session: Session) -> None:
    values = {
        "title": "Version 2.0: Combined Living Causal Evidence Observatory",
        "description": (
            "VICINITY now connects evidence about harm after violence exposure "
            "with evidence about structural and psychosocial responses. "
            "Scientific concept, development, and stewardship: Joseph Abbas, "
            "Rutgers University-Camden. Software implementation support: "
            "OpenAI Codex."
        ),
    }
    existing = session.scalar(
        select(RegistryUpdate).where(RegistryUpdate.title == values["title"])
    )
    if existing is None:
        session.add(RegistryUpdate(**values))
    else:
        existing.description = values["description"]


def seed_database(session: Session) -> None:
    exposure_records = _load_records(EXPOSURE_SEED_PATH)
    intervention_records = _load_records(INTERVENTION_SEED_PATH)
    if len(exposure_records) != 32 or len(intervention_records) != 26:
        raise RuntimeError("VICINITY requires exactly 32 exposure and 26 intervention records.")

    studies = [
        _upsert_study(session, record)
        for record in exposure_records + intervention_records
    ]
    session.flush()
    for study in studies:
        _replace_effect_estimates(session, study)

    session.execute(
        delete(LiteratureCandidate).where(
            LiteratureCandidate.doi.in_(SYNTHETIC_CANDIDATE_DOIS)
        )
    )
    _upsert_changelog(session)
    _upsert_search_baseline(session)
    _upsert_releases(session, exposure_records, intervention_records)
    _upsert_updates(session)
    session.commit()
