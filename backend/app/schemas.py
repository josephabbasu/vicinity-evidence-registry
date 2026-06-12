from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    study_id: str
    title: str
    citation: str
    publication_year: int | None
    country: str
    age_range: str
    age_groups: list[str]
    design_type: str
    causal_tier: str
    quality_tier: str
    exposure_type: str
    exposure_window: str
    geographic_scale: str
    outcome_type: str
    effect_direction: str
    effect_direction_raw: str
    statistically_significant: bool | None
    finding_summary: str
    effect_size_note: str
    featured: bool
    verification_count: int


class StudyDetail(StudySummary):
    design_raw: str
    causal_tier_reason: str
    risk_of_bias_raw: str
    exposure_window_raw: str
    outcomes: str
    outcome_measure: str
    outcome_unit_scale: str
    statistically_significant_raw: str
    standardized_effect_size: float | None
    ci_lower: float | None
    ci_upper: float | None
    sample_size: str
    population_details: str
    data_source: str
    exposure_measure: str
    mediators_mechanisms: str
    moderators: str
    methodology: str
    estimand: str
    estimator: str
    se_clustering: str
    outcome_timepoint: str
    missing_data_method: str
    multiple_testing_adjustment: str
    strengths_limitations: str
    policy_practice_implications: str
    reviewer_notes: str
    intervention_type: str
    is_intervention: bool
    doi: str | None
    source_url: str | None
    verification_flags: list[str]
    raw_fields: dict[str, str]


class StudyListResponse(BaseModel):
    total: int
    studies: list[StudySummary]


class StatsResponse(BaseModel):
    study_count: int
    country_count: int
    credible_count: int
    associational_count: int
    intervention_count: int
    latest_year: int | None
    updated_date: str
    countries: list[str]
    design_types: list[str]
    age_groups: list[str]
    outcome_types: list[str]
    exposure_windows: list[str]
    quality_tiers: list[str]
    causal_tiers: list[str]


class SubmissionCreate(BaseModel):
    citation: str = Field(min_length=3, max_length=2000)
    doi: str = Field(min_length=3, max_length=180)
    design_type: str = Field(min_length=2, max_length=120)
    population: str = Field(min_length=3, max_length=2000)
    exposure: str = Field(min_length=3, max_length=2000)
    outcome: str = Field(min_length=3, max_length=2000)
    effect_size: str = Field(min_length=1, max_length=1000)
    submitter_name: str | None = Field(default=None, max_length=180)
    submitter_email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=4000)


class SubmissionCreated(BaseModel):
    id: int
    status: str
    message: str


class UpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    created_at: datetime
