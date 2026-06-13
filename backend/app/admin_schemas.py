from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EligibilityResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    decision: str
    relevance_score: float
    population_score: float
    exposure_score: float
    outcome_score: float
    design_score: float
    notes: str
    rule_trace: dict
    model_name: str
    model_version: str
    overridden_by: str | None
    override_reason: str | None
    created_at: datetime


class StudyCandidateOut(BaseModel):
    id: int
    source: str
    source_id: str
    title: str
    authors: str
    year: int | None
    journal: str
    doi: str | None
    abstract: str
    source_url: str
    pdf_url: str
    status: str
    duplicate_of_id: int | None
    registered_study_id: int | None
    created_at: datetime
    updated_at: datetime
    eligibility: EligibilityResultOut | None


class StudyCandidateDetail(StudyCandidateOut):
    keywords: list[str]
    raw_metadata: dict
    history: list[EligibilityResultOut]


class CandidateListResponse(BaseModel):
    total: int
    candidates: list[StudyCandidateOut]


class CandidateDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(eligible|ineligible|review)$")
    reviewer: str = Field(min_length=2, max_length=180)
    reason: str = Field(min_length=5, max_length=4000)


class IngestionRunRequest(BaseModel):
    sources: list[str] | None = None
    triggered_by: str = Field(default="manual", min_length=2, max_length=80)
    background: bool = False


class IngestionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    triggered_by: str
    sources: list[str]
    discovered_count: int
    staged_count: int
    duplicate_count: int
    eligible_count: int
    review_count: int
    ineligible_count: int
    registered_count: int
    error_count: int
    errors: list[dict]
    cursor_state: dict


class IngestionEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    candidate_id: int | None
    source: str
    level: str
    message: str
    details: dict
    created_at: datetime


class RegistryStudyAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    study_id: str
    title: str
    citation: str
    publication_year: int | None
    registry_stream: str
    approval_status: str
    is_active: bool
    automation_status: str
    ingestion_candidate_id: int | None
    source_url: str | None
    created_at: datetime
    updated_at: datetime


class DeactivateStudyRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=180)
    reason: str = Field(min_length=5, max_length=4000)


class IngestionStatusOut(BaseModel):
    latest_run: IngestionRunOut | None
    candidate_counts: dict[str, int]
    cursors: dict[str, str]
    source_configuration: dict[str, bool]
    auto_registration_enabled: bool
