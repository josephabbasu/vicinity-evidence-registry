from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db_models import (
    IngestionRun,
    LiteratureCandidate,
    SearchRun,
    Study,
    StudyCandidate,
)
from ..schemas import EvidenceBrief, InterventionSummary, PractitionerQuery


AGE_MAP = {
    "adolescent": ["Adolescents 10-17"],
    "child": ["Children 0-9"],
    "adult": ["Young adults 18-29", "Adults 30+"],
}


def match_exposure_studies(
    studies: list[Study],
    query: PractitionerQuery,
) -> list[Study]:
    matched = [study for study in studies if study.registry_stream == "exposure"]
    if query.age_group and query.age_group != "all":
        groups = AGE_MAP.get(query.age_group, [])
        if groups:
            matched = [
                study
                for study in matched
                if any(group in study.age_groups for group in groups)
            ]
    if query.exposure_type and query.exposure_type != "general":
        needle = query.exposure_type.casefold()
        matched = [
            study
            for study in matched
            if needle
            in (
                f"{study.exposure_type} {study.exposure_measure} "
                f"{study.exposure_window_raw}"
            ).casefold()
        ]
    if query.outcome_type:
        needle = query.outcome_type.casefold()
        matched = [
            study
            for study in matched
            if needle
            in f"{study.outcome_type} {study.outcomes} {study.outcome_measure}".casefold()
        ]
    if query.country:
        matched = [study for study in matched if study.country == query.country]
    if query.exposure_window:
        matched = [
            study
            for study in matched
            if query.exposure_window.casefold() in study.exposure_window.casefold()
        ]
    return matched


def compute_causal_certainty(
    matched: list[Study],
) -> tuple[list[Study], str, str]:
    credible = [study for study in matched if study.causal_tier == "Credible"]
    directions = [
        study.effect_direction
        for study in matched
        if study.effect_direction not in ("", "Needs verification")
    ]
    dominant = max(set(directions), key=directions.count) if directions else "Insufficient data"
    if not matched:
        certainty = "No directly matched evidence"
    elif len(credible) >= 3 and len(credible) >= len(matched) * 0.5:
        certainty = "Convergent credible evidence"
    elif credible:
        certainty = "Credible evidence with important limitations"
    else:
        certainty = "Associational evidence only"
    return credible, dominant, certainty


def list_available_interventions(
    studies: list[Study],
    query: PractitionerQuery,
) -> list[InterventionSummary]:
    intervention_studies = [
        study for study in studies if study.registry_stream == "intervention"
    ]
    if query.age_group and query.age_group != "all":
        groups = AGE_MAP.get(query.age_group, [])
        if groups:
            intervention_studies = [
                study
                for study in intervention_studies
                if any(group in study.age_groups for group in groups)
            ]
    if query.outcome_type:
        needle = query.outcome_type.casefold()
        direct_matches = [
            study
            for study in intervention_studies
            if needle
            in f"{study.outcome_type} {study.outcomes} {study.outcome_measure}".casefold()
        ]
        if direct_matches:
            intervention_studies = direct_matches
    intervention_studies.sort(
        key=lambda study: (
            study.outcome_directness != "Direct mental-health outcome",
            study.causal_tier != "Credible",
            -(study.publication_year or 0),
        )
    )
    return [
        InterventionSummary(
            citation=study.citation,
            title=study.title,
            intervention_type=study.intervention_type or "Not classified",
            effect_direction=study.effect_direction,
            causal_tier=study.causal_tier,
            slug=study.slug,
            evidence_role=study.evidence_role,
            outcome_directness=study.outcome_directness,
            decision_relevance=study.decision_relevance,
        )
        for study in intervention_studies[:10]
    ]


def identify_evidence_gaps(
    matched: list[Study],
    credible: list[Study],
) -> list[str]:
    gaps: list[str] = []
    if not matched:
        gaps.append("No approved exposure study matches this exact combination.")
    if not credible and matched:
        gaps.append("No credible-tier study matched. The result relies on associational evidence.")
    if matched and not any(
        study.country not in ("United States", "Multiple countries")
        for study in matched
    ):
        gaps.append("The matched evidence does not include a clearly identified non-US setting.")
    if not any("anxiety" in study.outcome_type.casefold() for study in matched):
        gaps.append("Anxiety outcomes are underrepresented in the matched set.")
    if not any("suicide" in study.outcomes.casefold() for study in matched):
        gaps.append("Suicidality outcomes are absent from matched studies.")
    return gaps


def _query_description(query: PractitionerQuery) -> str:
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
    return "Evidence for " + " ".join(parts)


def _freshness(session: Session) -> tuple[str | None, int]:
    legacy_run = session.scalar(
        select(SearchRun)
        .where(SearchRun.coverage_end_date.is_not(None))
        .order_by(SearchRun.coverage_end_date.desc())
    )
    ingestion_run = session.scalar(
        select(IngestionRun)
        .where(IngestionRun.completed_at.is_not(None))
        .order_by(IngestionRun.completed_at.desc())
    )
    dates = []
    if legacy_run and legacy_run.coverage_end_date:
        dates.append(legacy_run.coverage_end_date.isoformat())
    if ingestion_run and ingestion_run.completed_at:
        dates.append(ingestion_run.completed_at.date().isoformat())

    legacy_pending = session.scalar(
        select(func.count())
        .select_from(LiteratureCandidate)
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
    automated_pending = session.scalar(
        select(func.count())
        .select_from(StudyCandidate)
        .where(StudyCandidate.status == "review")
    ) or 0
    return (max(dates) if dates else None, legacy_pending + automated_pending)


def build_evidence_brief(
    session: Session,
    query: PractitionerQuery,
) -> EvidenceBrief:
    studies = list(
        session.scalars(
            select(Study).where(
                Study.approval_status == "approved",
                Study.is_active.is_(True),
            )
        ).all()
    )
    matched = match_exposure_studies(studies, query)
    credible, dominant, certainty = compute_causal_certainty(matched)
    interventions = list_available_interventions(studies, query)
    gaps = identify_evidence_gaps(matched, credible)
    last_searched, pending = _freshness(session)
    return EvidenceBrief(
        query_description=_query_description(query),
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
        available_interventions=interventions,
        evidence_gaps=gaps,
        last_searched=last_searched,
        pending_candidates=pending,
        studies_included=[study.citation for study in matched],
    )

