from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
    intervention_type: Mapped[str] = mapped_column(String(80))
    is_intervention: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    doi: Mapped[str | None] = mapped_column(String(180))
    source_url: Mapped[str | None] = mapped_column(Text)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_flags: Mapped[list[str]] = mapped_column(JSON)
    raw_fields: Mapped[dict[str, str]] = mapped_column(JSON)


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
