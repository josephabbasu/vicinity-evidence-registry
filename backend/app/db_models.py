from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    study_id: Mapped[str] = mapped_column(String(220), unique=True)
    title: Mapped[str] = mapped_column(Text)
    citation: Mapped[str] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(Integer, index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    age_range: Mapped[str] = mapped_column(Text)
    age_min: Mapped[float | None] = mapped_column(Float)
    age_max: Mapped[float | None] = mapped_column(Float)
    age_groups: Mapped[list[str]] = mapped_column(JSON)
    design_type: Mapped[str] = mapped_column(String(120), index=True)
    design_raw: Mapped[str] = mapped_column(Text)
    causal_tier: Mapped[str] = mapped_column(String(40), index=True)
    causal_tier_reason: Mapped[str] = mapped_column(Text)
    quality_tier: Mapped[str] = mapped_column(String(40), index=True)
    risk_of_bias_raw: Mapped[str] = mapped_column(Text)
    exposure_type: Mapped[str] = mapped_column(String(80), index=True)
    exposure_window: Mapped[str] = mapped_column(String(80), index=True)
    exposure_window_raw: Mapped[str] = mapped_column(Text)
    geographic_scale: Mapped[str] = mapped_column(String(100), index=True)
    outcome_type: Mapped[str] = mapped_column(String(100), index=True)
    outcomes: Mapped[str] = mapped_column(Text)
    outcome_measure: Mapped[str] = mapped_column(Text)
    outcome_unit_scale: Mapped[str] = mapped_column(Text)
    effect_direction: Mapped[str] = mapped_column(String(40), index=True)
    effect_direction_raw: Mapped[str] = mapped_column(Text)
    statistically_significant: Mapped[bool | None] = mapped_column(Boolean)
    statistically_significant_raw: Mapped[str] = mapped_column(Text)
    standardized_effect_size: Mapped[float | None] = mapped_column(Float)
    ci_lower: Mapped[float | None] = mapped_column(Float)
    ci_upper: Mapped[float | None] = mapped_column(Float)
    effect_size_note: Mapped[str] = mapped_column(Text)
    sample_size: Mapped[str] = mapped_column(Text)
    population_details: Mapped[str] = mapped_column(Text)
    data_source: Mapped[str] = mapped_column(Text)
    exposure_measure: Mapped[str] = mapped_column(Text)
    mediators_mechanisms: Mapped[str] = mapped_column(Text)
    moderators: Mapped[str] = mapped_column(Text)
    finding_summary: Mapped[str] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(Text)
    estimand: Mapped[str] = mapped_column(Text)
    estimator: Mapped[str] = mapped_column(Text)
    se_clustering: Mapped[str] = mapped_column(Text)
    outcome_timepoint: Mapped[str] = mapped_column(Text)
    missing_data_method: Mapped[str] = mapped_column(Text)
    multiple_testing_adjustment: Mapped[str] = mapped_column(Text)
    strengths_limitations: Mapped[str] = mapped_column(Text)
    policy_practice_implications: Mapped[str] = mapped_column(Text)
    reviewer_notes: Mapped[str] = mapped_column(Text)
    intervention_type: Mapped[str] = mapped_column(Text)
    is_intervention: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    doi: Mapped[str | None] = mapped_column(String(180))
    source_url: Mapped[str | None] = mapped_column(Text)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_flags: Mapped[list[str]] = mapped_column(JSON)
    raw_fields: Mapped[dict[str, str]] = mapped_column(JSON)

    # V2: stream classification and workflow
    registry_stream: Mapped[str] = mapped_column(
        String(40), default="exposure", index=True
    )  # exposure | intervention | implementation
    approval_status: Mapped[str] = mapped_column(
        String(40), default="approved", index=True
    )  # approved | pending | rejected
    registry_version: Mapped[int] = mapped_column(Integer, default=1)
    added_in_version: Mapped[str] = mapped_column(String(20), default="1.0")
    evidence_role: Mapped[str] = mapped_column(String(80), default="Exposure consequence")
    intervention_class: Mapped[str] = mapped_column(String(40), default="Not applicable")
    outcome_directness: Mapped[str] = mapped_column(
        String(80), default="Scope requires verification"
    )
    decision_relevance: Mapped[str] = mapped_column(
        String(120), default="Research context"
    )
    source_review: Mapped[str] = mapped_column(String(160), default="")
    search_coverage_end: Mapped[str] = mapped_column(String(10), default="2025-07-31")
    source_row: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    automation_status: Mapped[str] = mapped_column(
        String(40), default="manual", index=True
    )
    ingestion_candidate_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Scientific review status (distinct from normalization notes)
    verification_status: Mapped[str] = mapped_column(
        String(40), default="verified", index=True
    )  # verified | needs_review | in_extraction | excluded
    normalization_notes: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Design transparency and transferability
    identification_assumptions: Mapped[str] = mapped_column(Text, default="")
    diagnostics_reported: Mapped[str] = mapped_column(Text, default="")
    transferability_setting: Mapped[str] = mapped_column(String(80), default="Needs verification")
    transferability_population: Mapped[str] = mapped_column(String(80), default="Needs verification")
    transferability_feasibility: Mapped[str] = mapped_column(String(80), default="Needs verification")
    transferability_overall: Mapped[str] = mapped_column(String(40), default="Needs verification")

    effect_estimates: Mapped[list[EffectEstimate]] = relationship(
        "EffectEstimate", back_populates="study", cascade="all, delete-orphan"
    )


class EffectEstimate(Base):
    """One row per distinct effect reported in a study.

    A single study can report effects for multiple subpopulations, outcomes,
    and follow-up windows. Storing at this granularity prevents selective
    reporting and enables meta-analytic synthesis.
    """

    __tablename__ = "effect_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), index=True)
    outcome_label: Mapped[str] = mapped_column(String(200))
    outcome_instrument: Mapped[str] = mapped_column(Text, default="")
    population_subgroup: Mapped[str] = mapped_column(Text, default="Full sample")
    exposure_contrast: Mapped[str] = mapped_column(Text, default="")
    follow_up_period: Mapped[str] = mapped_column(String(120), default="")
    estimate_type: Mapped[str] = mapped_column(String(80), default="")  # β, OR, IRR, d
    point_estimate: Mapped[float | None] = mapped_column(Float)
    standard_error: Mapped[float | None] = mapped_column(Float)
    ci_lower: Mapped[float | None] = mapped_column(Float)
    ci_upper: Mapped[float | None] = mapped_column(Float)
    p_value: Mapped[float | None] = mapped_column(Float)
    adjustment_variables: Mapped[str] = mapped_column(Text, default="")
    causal_estimand: Mapped[str] = mapped_column(Text, default="")
    source_table: Mapped[str] = mapped_column(String(80), default="")
    rob_rating: Mapped[str] = mapped_column(String(40), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    study: Mapped[Study] = relationship("Study", back_populates="effect_estimates")


class Reviewer(Base):
    __tablename__ = "reviewers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(180))
    email: Mapped[str] = mapped_column(String(220), unique=True)
    role: Mapped[str] = mapped_column(String(40), default="reviewer")  # reviewer | lead
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SearchRun(Base):
    """Tracks each monthly automated literature surveillance run."""

    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    coverage_end_date: Mapped[date | None] = mapped_column(Date)
    databases_searched: Mapped[list[str]] = mapped_column(JSON)
    query_terms: Mapped[str] = mapped_column(Text)
    candidates_found: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_removed: Mapped[int] = mapped_column(Integer, default=0)
    new_candidates: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    notes: Mapped[str] = mapped_column(Text, default="")
    triggered_by: Mapped[str] = mapped_column(String(80), default="scheduled")

    candidates: Mapped[list[LiteratureCandidate]] = relationship(
        "LiteratureCandidate", back_populates="search_run"
    )


class LiteratureCandidate(Base):
    """A publication discovered through automated surveillance, awaiting dual review."""

    __tablename__ = "literature_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_run_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("search_runs.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    journal: Mapped[str] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(180))
    abstract: Mapped[str] = mapped_column(Text, default="")
    source_database: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str] = mapped_column(String(180), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    relevance_score: Mapped[float | None] = mapped_column(Float)
    # Workflow: discovered, screened, full text, extracted, approved or rejected.
    status: Mapped[str] = mapped_column(String(40), default="discovered", index=True)
    screen_decision: Mapped[str | None] = mapped_column(String(40))
    screen_reason: Mapped[str | None] = mapped_column(Text)
    screen_reviewer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("reviewers.id"), nullable=True
    )
    fulltext_decision: Mapped[str | None] = mapped_column(String(40))
    fulltext_reason: Mapped[str | None] = mapped_column(Text)
    fulltext_reviewer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("reviewers.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    search_run: Mapped[SearchRun | None] = relationship(
        "SearchRun", back_populates="candidates"
    )


class IngestionRun(Base):
    """One automated living-evidence ingestion run."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    triggered_by: Mapped[str] = mapped_column(String(80), default="scheduled")
    sources: Mapped[list[str]] = mapped_column(JSON, default=list)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    staged_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    eligible_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    ineligible_count: Mapped[int] = mapped_column(Integer, default=0)
    registered_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[dict]] = mapped_column(JSON, default=list)
    cursor_state: Mapped[dict] = mapped_column(JSON, default=dict)


class IngestionCursor(Base):
    """The last successfully processed cursor for one source."""

    __tablename__ = "ingestion_cursors"

    source: Mapped[str] = mapped_column(String(80), primary_key=True)
    cursor_value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class StudyCandidate(Base):
    """A normalized source record staged for automated eligibility screening."""

    __tablename__ = "study_candidates"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_study_candidate_source_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ingestion_runs.id"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str] = mapped_column(String(300))
    source_version: Mapped[int | None] = mapped_column(Integer)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    journal: Mapped[str] = mapped_column(Text, default="")
    doi: Mapped[str | None] = mapped_column(String(180), index=True)
    abstract: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_url: Mapped[str] = mapped_column(Text, default="")
    pdf_url: Mapped[str] = mapped_column(Text, default="")
    dedupe_key: Mapped[str] = mapped_column(String(500), index=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("study_candidates.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="staged", index=True)
    registered_study_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class EligibilityResult(Base):
    """A versioned automated or human eligibility decision."""

    __tablename__ = "eligibility_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_candidates.id"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    model_version: Mapped[str] = mapped_column(String(40))
    decision: Mapped[str] = mapped_column(String(40), index=True)
    relevance_score: Mapped[float] = mapped_column(Float)
    population_score: Mapped[float] = mapped_column(Float)
    exposure_score: Mapped[float] = mapped_column(Float)
    outcome_score: Mapped[float] = mapped_column(Float)
    design_score: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")
    rule_trace: Mapped[dict] = mapped_column(JSON, default=dict)
    overridden_by: Mapped[str | None] = mapped_column(String(180))
    override_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class IngestionEvent(Base):
    """A structured event emitted while an ingestion run executes."""

    __tablename__ = "ingestion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_runs.id"), index=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("study_candidates.id"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="")
    level: Mapped[str] = mapped_column(String(20), default="info", index=True)
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class ReviewDecision(Base):
    """One independent screening or full-text decision."""

    __tablename__ = "review_decisions"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "stage",
            "reviewer_name",
            name="uq_candidate_stage_reviewer",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("literature_candidates.id"),
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(40), index=True)
    decision: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    reviewer_name: Mapped[str] = mapped_column(String(180))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class ChangeLog(Base):
    """Public audit trail of every registry update, enabling reproducible citations."""

    __tablename__ = "changelog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(20))
    change_type: Mapped[str] = mapped_column(String(40))
    # addition | correction | retraction | methodology | surveillance
    summary: Mapped[str] = mapped_column(Text)
    affected_studies: Mapped[list[str]] = mapped_column(JSON, default=list)
    study_count_before: Mapped[int] = mapped_column(Integer, default=0)
    study_count_after: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Release(Base):
    """Versioned registry snapshot for stable citation."""

    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(20), unique=True)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    study_count: Mapped[int] = mapped_column(Integer, default=0)
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)
    intervention_count: Mapped[int] = mapped_column(Integer, default=0)
    credible_count: Mapped[int] = mapped_column(Integer, default=0)
    doi: Mapped[str | None] = mapped_column(String(200))
    zenodo_record_id: Mapped[str | None] = mapped_column(String(80))
    frozen_json: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citation: Mapped[str] = mapped_column(Text)
    doi: Mapped[str] = mapped_column(String(180))
    design_type: Mapped[str] = mapped_column(String(120))
    population: Mapped[str] = mapped_column(Text)
    exposure: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text)
    effect_size: Mapped[str] = mapped_column(Text)
    submitter_name: Mapped[str | None] = mapped_column(String(180))
    submitter_email: Mapped[str | None] = mapped_column(String(220))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RegistryUpdate(Base):
    __tablename__ = "updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
