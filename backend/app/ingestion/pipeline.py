from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db_models import (
    ChangeLog,
    EligibilityResult,
    IngestionCursor,
    IngestionEvent,
    IngestionRun,
    Study,
    StudyCandidate,
)
from ..eligibility.classifier import (
    ClassificationResult,
    RuleBasedStudyClassifier,
    StudyClassifier,
)
from .crossref_client import CrossrefClient
from .models import NormalizedCandidate, normalize_doi, normalize_title
from .openalex_client import OpenAlexClient
from .pubmed_client import PubMedClient
from .semanticscholar_client import SemanticScholarClient
from .zotero_client import ZoteroClient


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def build_default_clients() -> dict[str, object]:
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user").strip().casefold()
    return {
        "zotero": ZoteroClient(
            api_key=os.getenv("ZOTERO_API_KEY", "").strip(),
            library_type=library_type,
            library_id=os.getenv("ZOTERO_LIBRARY_ID", "").strip(),
            collection_id=os.getenv("ZOTERO_COLLECTION_ID", "").strip(),
        ),
        "pubmed": PubMedClient(api_key=os.getenv("NCBI_API_KEY", "").strip()),
        "crossref": CrossrefClient(
            mailto=os.getenv("CROSSREF_MAILTO", "").strip()
        ),
        "openalex": OpenAlexClient(
            api_key=os.getenv("OPENALEX_API_KEY", "").strip()
        ),
        "semanticscholar": SemanticScholarClient(
            api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
        ),
    }


def _candidate_from_row(row: StudyCandidate) -> NormalizedCandidate:
    return NormalizedCandidate(
        source=row.source,
        source_id=row.source_id,
        source_version=row.source_version,
        title=row.title,
        authors=row.authors,
        year=row.year,
        journal=row.journal,
        doi=row.doi,
        abstract=row.abstract,
        keywords=row.keywords or [],
        source_url=row.source_url,
        pdf_url=row.pdf_url,
        raw_metadata=row.raw_metadata or {},
    )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:150] or "automated-study"


def _unique_slug(session: Session, candidate: StudyCandidate) -> str:
    base = _slugify(
        f"{candidate.authors.split(';')[0]}-{candidate.year}-{candidate.title[:70]}"
    )
    slug = base
    suffix = 2
    while session.scalar(select(Study.id).where(Study.slug == slug)):
        slug = f"{base[:165]}-{suffix}"
        suffix += 1
    return slug


def _find_existing_study(
    session: Session,
    candidate: StudyCandidate,
) -> Study | None:
    normalized_candidate_doi = normalize_doi(candidate.doi)
    studies = list(session.scalars(select(Study)).all())
    if normalized_candidate_doi:
        for study in studies:
            if normalize_doi(study.doi) == normalized_candidate_doi:
                return study
    normalized_candidate_title = normalize_title(candidate.title)
    for study in studies:
        if study.publication_year != candidate.year:
            continue
        if normalize_title(study.title) == normalized_candidate_title:
            return study
    return None


def _citation(candidate: StudyCandidate) -> str:
    author = candidate.authors.split(";")[0].strip() or "Author not reported"
    year = candidate.year or "n.d."
    journal = f" {candidate.journal}." if candidate.journal else ""
    return f"{author} ({year}). {candidate.title}.{journal}".strip()


def register_study_from_candidate(
    session: Session,
    candidate: StudyCandidate,
    result: EligibilityResult,
) -> tuple[Study, bool]:
    existing = _find_existing_study(session, candidate)
    if existing is not None:
        candidate.registered_study_id = existing.id
        candidate.status = "existing_study"
        return existing, False

    inferred = (result.rule_trace or {}).get("inferred") or {}
    registry_stream = inferred.get("registry_stream", "exposure")
    is_intervention = registry_stream == "intervention"
    age_groups = inferred.get("age_groups") or ["Scope requires verification"]
    before = session.scalar(
        select(func.count())
        .select_from(Study)
        .where(Study.approval_status == "approved", Study.is_active.is_(True))
    ) or 0
    study = Study(
        slug=_unique_slug(session, candidate),
        study_id=f"AUTO-{candidate.source.upper()}-{candidate.source_id}"[:220],
        title=candidate.title,
        citation=_citation(candidate),
        publication_year=candidate.year,
        country="Not reported",
        age_range="; ".join(age_groups),
        age_min=None,
        age_max=None,
        age_groups=age_groups,
        design_type=inferred.get("design_type", "Design not reported"),
        design_raw=inferred.get("design_type", "Design not reported"),
        causal_tier="Associational",
        causal_tier_reason=(
            "The automated classifier inferred the design from title, abstract, "
            "and keywords. VICINITY does not assign a credible causal tier until "
            "a reviewer verifies the full text."
        ),
        quality_tier="Needs verification",
        risk_of_bias_raw="Risk of bias has not yet been extracted.",
        exposure_type=inferred.get("exposure_type", "Community violence"),
        exposure_window="Not reported",
        exposure_window_raw="The source metadata did not establish an exposure window.",
        geographic_scale="Neighborhood or community",
        outcome_type=inferred.get("outcome_type", "Mental health"),
        outcomes=inferred.get("outcome_type", "Mental health"),
        outcome_measure="Outcome instrument has not yet been extracted.",
        outcome_unit_scale="Not reported",
        effect_direction="Needs verification",
        effect_direction_raw="Effect estimates have not yet been extracted.",
        statistically_significant=None,
        statistically_significant_raw="Not extracted",
        standardized_effect_size=None,
        ci_lower=None,
        ci_upper=None,
        effect_size_note="The living-evidence pipeline registered metadata only.",
        sample_size="Not extracted",
        population_details="Population details require full-text verification.",
        data_source=candidate.source,
        exposure_measure="Exposure measurement requires full-text verification.",
        mediators_mechanisms="Not extracted",
        moderators="Not extracted",
        finding_summary=(
            candidate.abstract[:1800]
            if candidate.abstract
            else "The source record did not include an abstract."
        ),
        methodology="Automated metadata ingestion followed by rule-based screening.",
        estimand="Not extracted",
        estimator="Not extracted",
        se_clustering="Not extracted",
        outcome_timepoint="Not extracted",
        missing_data_method="Not extracted",
        multiple_testing_adjustment="Not extracted",
        strengths_limitations=(
            "The record passed strict automated relevance and design thresholds. "
            "Full-text extraction and risk-of-bias review remain outstanding."
        ),
        policy_practice_implications=(
            "The registry exposes this record for discovery. Users should not base "
            "decisions on unverified effect estimates."
        ),
        reviewer_notes=result.notes,
        intervention_type=(
            "Automated intervention classification pending extraction"
            if is_intervention
            else "Not applicable"
        ),
        is_intervention=is_intervention,
        doi=normalize_doi(candidate.doi),
        source_url=candidate.source_url,
        featured=False,
        verification_flags=[
            "Automated eligibility decision requires periodic validation.",
            "Full-text extraction has not been completed.",
            "Effect estimates and risk of bias require reviewer verification.",
        ],
        raw_fields={
            "ingestion_source": candidate.source,
            "source_id": candidate.source_id,
            "pdf_url": candidate.pdf_url,
            "abstract": candidate.abstract,
        },
        registry_stream=registry_stream,
        approval_status="approved",
        registry_version=3,
        added_in_version="living",
        evidence_role=(
            "Intervention or recovery evidence"
            if is_intervention
            else "Exposure consequence"
        ),
        intervention_class=inferred.get("intervention_class", "Not applicable"),
        outcome_directness="Direct mental-health outcome",
        decision_relevance="Automated discovery. Full-text verification required.",
        source_review="VICINITY automated living-evidence ingestion",
        search_coverage_end=date.today().isoformat(),
        source_row=None,
        is_active=True,
        automation_status="auto_registered",
        ingestion_candidate_id=candidate.id,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session.add(study)
    session.flush()
    candidate.registered_study_id = study.id
    candidate.status = "registered"
    session.add(
        ChangeLog(
            version=f"living-{date.today().isoformat()}",
            change_type="addition",
            summary=(
                f"Automated ingestion added {candidate.title} from {candidate.source}. "
                "The record is marked for full-text verification."
            ),
            affected_studies=[study.study_id],
            study_count_before=before,
            study_count_after=before + 1,
        )
    )
    return study, True


class IngestionPipeline:
    def __init__(
        self,
        session: Session,
        classifier: StudyClassifier | None = None,
        clients: dict[str, object] | None = None,
        auto_register: bool | None = None,
    ) -> None:
        self.session = session
        self.classifier = classifier or RuleBasedStudyClassifier()
        self.clients = clients or build_default_clients()
        self.auto_register = (
            env_flag("AUTO_REGISTER_ELIGIBLE", True)
            if auto_register is None
            else auto_register
        )

    def _event(
        self,
        run: IngestionRun,
        message: str,
        source: str = "",
        level: str = "info",
        candidate_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        self.session.add(
            IngestionEvent(
                run_id=run.id,
                candidate_id=candidate_id,
                source=source,
                level=level,
                message=message,
                details=details or {},
            )
        )

    def _cursor(self, source: str) -> str:
        row = self.session.get(IngestionCursor, source)
        if row is not None:
            return row.cursor_value
        if source == "zotero":
            return "0"
        lookback = int(os.getenv("INGESTION_LOOKBACK_DAYS", "7"))
        return (date.today() - timedelta(days=lookback)).isoformat()

    def _set_cursor(self, source: str, value: str) -> None:
        row = self.session.get(IngestionCursor, source)
        if row is None:
            self.session.add(IngestionCursor(source=source, cursor_value=value))
        else:
            row.cursor_value = value
            row.updated_at = utc_now()

    def _upsert_candidate(
        self,
        run: IngestionRun,
        item: NormalizedCandidate,
    ) -> tuple[StudyCandidate, bool]:
        row = self.session.scalar(
            select(StudyCandidate).where(
                StudyCandidate.source == item.source,
                StudyCandidate.source_id == item.source_id,
            )
        )
        created = row is None
        if row is None:
            row = StudyCandidate(
                source=item.source,
                source_id=item.source_id,
                title=item.title,
                dedupe_key=item.dedupe_key,
            )
            self.session.add(row)
        row.ingestion_run_id = run.id
        row.source_version = item.source_version
        row.raw_metadata = item.raw_metadata
        row.title = item.title
        row.authors = item.authors
        row.year = item.year
        row.journal = item.journal
        row.doi = normalize_doi(item.doi)
        row.abstract = item.abstract
        row.keywords = item.keywords
        row.source_url = item.source_url
        row.pdf_url = item.pdf_url
        row.dedupe_key = item.dedupe_key
        row.updated_at = utc_now()
        if created:
            row.status = "staged"
        self.session.flush()
        return row, created

    def _mark_duplicate(self, candidate: StudyCandidate) -> StudyCandidate | None:
        canonical = self.session.scalar(
            select(StudyCandidate)
            .where(
                StudyCandidate.dedupe_key == candidate.dedupe_key,
                StudyCandidate.id != candidate.id,
                StudyCandidate.duplicate_of_id.is_(None),
            )
            .order_by(
                StudyCandidate.registered_study_id.is_(None),
                StudyCandidate.created_at.asc(),
            )
        )
        if canonical is None:
            return None
        candidate.duplicate_of_id = canonical.id
        candidate.registered_study_id = canonical.registered_study_id
        candidate.status = "duplicate"
        return canonical

    def classify_candidate(
        self,
        candidate: StudyCandidate,
        allow_registration: bool = True,
    ) -> EligibilityResult:
        result = self.classifier.classify(_candidate_from_row(candidate))
        self.session.execute(
            update(EligibilityResult)
            .where(
                EligibilityResult.candidate_id == candidate.id,
                EligibilityResult.is_current.is_(True),
            )
            .values(is_current=False)
        )
        row = EligibilityResult(
            candidate_id=candidate.id,
            source=candidate.source,
            is_current=True,
            model_name=result.model_name,
            model_version=result.model_version,
            decision=result.decision,
            relevance_score=result.relevance_score,
            population_score=result.population_score,
            exposure_score=result.exposure_score,
            outcome_score=result.outcome_score,
            design_score=result.design_score,
            notes=result.notes,
            rule_trace=result.rule_trace,
        )
        self.session.add(row)
        self.session.flush()
        candidate.status = result.decision
        if (
            result.decision == "eligible"
            and allow_registration
            and self.auto_register
        ):
            register_study_from_candidate(self.session, candidate, row)
        return row

    def override_candidate(
        self,
        candidate: StudyCandidate,
        decision: str,
        reviewer: str,
        reason: str,
    ) -> EligibilityResult:
        current = self.session.scalar(
            select(EligibilityResult)
            .where(
                EligibilityResult.candidate_id == candidate.id,
                EligibilityResult.is_current.is_(True),
            )
            .order_by(EligibilityResult.created_at.desc())
        )
        if current is None:
            current = self.classify_candidate(candidate, allow_registration=False)
        current.is_current = False
        override = EligibilityResult(
            candidate_id=candidate.id,
            source=candidate.source,
            is_current=True,
            model_name=current.model_name,
            model_version=current.model_version,
            decision=decision,
            relevance_score=current.relevance_score,
            population_score=current.population_score,
            exposure_score=current.exposure_score,
            outcome_score=current.outcome_score,
            design_score=current.design_score,
            notes=f"Human override: {reason}",
            rule_trace=current.rule_trace,
            overridden_by=reviewer,
            override_reason=reason,
        )
        self.session.add(override)
        self.session.flush()
        candidate.status = decision
        if decision == "eligible":
            register_study_from_candidate(self.session, candidate, override)
        return override

    def run(
        self,
        triggered_by: str = "scheduled",
        selected_sources: list[str] | None = None,
        existing_run: IngestionRun | None = None,
    ) -> IngestionRun:
        configured_sources = [
            source
            for source in (selected_sources or self.clients.keys())
            if source in self.clients
        ]
        run = existing_run or IngestionRun()
        run.status = "running"
        run.triggered_by = triggered_by
        run.sources = configured_sources
        run.started_at = utc_now()
        if existing_run is None:
            self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        cursor_state: dict[str, str] = {}
        errors: list[dict] = []
        for source in configured_sources:
            client = self.clients[source]
            if not getattr(client, "configured", False):
                self._event(
                    run,
                    "Source skipped because required configuration is missing.",
                    source=source,
                )
                continue
            cursor = self._cursor(source)
            try:
                batch = client.fetch_new_items(cursor)
                run.discovered_count += len(batch.items)
                for item in batch.items:
                    candidate, created = self._upsert_candidate(run, item)
                    if created:
                        run.staged_count += 1
                    canonical = self._mark_duplicate(candidate)
                    if canonical is not None:
                        run.duplicate_count += 1
                        self._event(
                            run,
                            "Candidate matched an existing normalized record.",
                            source=source,
                            candidate_id=candidate.id,
                            details={"duplicate_of_id": canonical.id},
                        )
                        continue
                    result = self.classify_candidate(candidate)
                    if result.decision == "eligible":
                        run.eligible_count += 1
                        if candidate.status in {"registered", "existing_study"}:
                            run.registered_count += int(
                                candidate.status == "registered"
                            )
                    elif result.decision == "review":
                        run.review_count += 1
                    else:
                        run.ineligible_count += 1
                self._set_cursor(source, batch.next_cursor)
                cursor_state[source] = batch.next_cursor
                self._event(
                    run,
                    f"Source completed with {len(batch.items)} discovered records.",
                    source=source,
                )
                self.session.commit()
            except Exception as exc:
                self.session.rollback()
                run = self.session.get(IngestionRun, run.id)
                error = {"source": source, "error": str(exc)[:1000]}
                errors.append(error)
                run.error_count += 1
                self._event(
                    run,
                    "Source failed.",
                    source=source,
                    level="error",
                    details=error,
                )
                self.session.commit()

        run = self.session.get(IngestionRun, run.id)
        run.completed_at = utc_now()
        run.status = "completed_with_errors" if errors else "completed"
        run.errors = errors
        run.cursor_state = cursor_state
        self.session.commit()
        self.session.refresh(run)
        return run
