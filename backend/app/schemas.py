from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Study schemas ──────────────────────────────────────────────────────────────

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
    registry_stream: str
    is_intervention: bool
    evidence_role: str
    intervention_class: str
    outcome_directness: str
    decision_relevance: str


class TransferabilityScore(BaseModel):
    setting_score: float
    population_score: float
    feasibility_score: float
    total: float
    label: str


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
    doi: str | None
    source_url: str | None
    verification_flags: list[str]
    raw_fields: dict[str, str]
    added_in_version: str
    source_review: str
    search_coverage_end: str
    source_row: int | None
    verification_status: str = "verified"
    normalization_notes: list[str] = []
    identification_assumptions: str = ""
    diagnostics_reported: str = ""
    transferability_setting: str = "Needs verification"
    transferability_population: str = "Needs verification"
    transferability_feasibility: str = "Needs verification"
    transferability_overall: str = "Needs verification"
    effect_estimates: list[EffectEstimateOut]
    transferability: TransferabilityScore | None = None


class StudyListResponse(BaseModel):
    total: int
    studies: list[StudySummary]


# ── Effect estimate schemas ───────────────────────────────────────────────────

class EffectEstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    outcome_label: str
    outcome_instrument: str
    population_subgroup: str
    exposure_contrast: str
    follow_up_period: str
    estimate_type: str
    point_estimate: float | None
    standard_error: float | None
    ci_lower: float | None
    ci_upper: float | None
    p_value: float | None
    adjustment_variables: str
    causal_estimand: str
    source_table: str
    rob_rating: str
    is_primary: bool


# ── Stats schemas ─────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    study_count: int
    exposure_count: int
    intervention_count: int
    country_count: int
    credible_count: int
    associational_count: int
    latest_year: int | None
    updated_date: str
    last_search_date: str | None
    pending_candidates: int
    direct_mental_health_count: int
    structural_intervention_count: int
    psychosocial_intervention_count: int
    exposure_reduction_count: int
    countries: list[str]
    design_types: list[str]
    age_groups: list[str]
    outcome_types: list[str]
    exposure_windows: list[str]
    quality_tiers: list[str]
    causal_tiers: list[str]


# ── Practitioner query schemas ─────────────────────────────────────────────────

class PractitionerQuery(BaseModel):
    age_group: str | None = Field(default=None, description="adolescent | child | adult | all")
    exposure_type: str | None = Field(default=None, description="shooting | assault | property | general")
    exposure_window: str | None = None
    outcome_type: str | None = None
    country: str | None = None


class InterventionSummary(BaseModel):
    citation: str
    title: str
    intervention_type: str
    effect_direction: str
    causal_tier: str
    slug: str
    evidence_role: str
    outcome_directness: str
    decision_relevance: str


class EvidenceBrief(BaseModel):
    query_description: str
    study_count: int
    credible_count: int
    dominant_direction: str
    causal_certainty: str
    effect_note: str
    population_note: str
    limitations: str
    available_interventions: list[InterventionSummary]
    evidence_gaps: list[str]
    last_searched: str | None
    pending_candidates: int
    studies_included: list[str]


# ── Gap radar schemas ──────────────────────────────────────────────────────────

class GapItem(BaseModel):
    domain: str          # Geographic | Outcome | Method | Population
    label: str
    description: str
    n_studies: int
    priority: str        # High | Medium | Low
    suggested_action: str


class GapRadarResponse(BaseModel):
    computed_at: str
    total_studies: int
    gaps: list[GapItem]
    geographic_breakdown: dict[str, int]
    outcome_breakdown: dict[str, int]
    design_breakdown: dict[str, int]
    stream_breakdown: dict[str, int]
    directness_breakdown: dict[str, int]
    intervention_breakdown: dict[str, int]


# ── Reviewer / dashboard schemas ───────────────────────────────────────────────

class ReviewerAuthRequest(BaseModel):
    token: str


class ReviewerAuthResponse(BaseModel):
    authenticated: bool
    name: str
    role: str


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    authors: str
    year: int | None
    journal: str
    doi: str | None
    abstract: str
    source_database: str
    source_id: str
    source_url: str
    relevance_score: float | None
    status: str
    screen_decision: str | None
    screen_reason: str | None
    fulltext_decision: str | None
    fulltext_reason: str | None
    created_at: datetime


class ReviewDecisionCreate(BaseModel):
    stage: str = Field(pattern="^(screen|fulltext)$")
    decision: str = Field(pattern="^(include|exclude|uncertain)$")
    reason: str = Field(min_length=3, max_length=2000)
    reviewer_name: str = Field(min_length=2, max_length=180)


class SearchRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_date: datetime
    coverage_end_date: date | None
    databases_searched: list[str]
    candidates_found: int
    new_candidates: int
    status: str
    triggered_by: str


class DashboardResponse(BaseModel):
    total_studies: int
    exposure_count: int
    intervention_count: int
    pending_candidates: int
    awaiting_screen: int
    awaiting_fulltext: int
    approved_this_month: int
    recent_runs: list[SearchRunOut]
    recent_candidates: list[CandidateOut]


# ── Changelog schemas ──────────────────────────────────────────────────────────

class ChangeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    change_type: str
    summary: str
    affected_studies: list[str]
    study_count_before: int
    study_count_after: int
    created_at: datetime


# ── Submission schemas ─────────────────────────────────────────────────────────

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
