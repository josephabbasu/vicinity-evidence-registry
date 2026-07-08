from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth ----
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    email: str
    name: str


# ---- ideas ----
class IdeaIn(BaseModel):
    title: str
    pillar: str = ""
    format: str = "long"
    notes: str = ""
    demand: int = Field(5, ge=1, le=10)
    evergreen: int = Field(5, ge=1, le=10)
    competition_gap: int = Field(5, ge=1, le=10)
    monetization: int = Field(5, ge=1, le=10)
    production_ease: int = Field(5, ge=1, le=10)


class IdeaOut(ORMModel):
    id: int
    title: str
    pillar: str
    format: str
    notes: str
    demand: int
    evergreen: int
    competition_gap: int
    monetization: int
    production_ease: int
    status: str
    score: float


class IdeaGenIn(BaseModel):
    pillar: str = ""
    topic_hint: str = ""
    count: int = Field(5, ge=1, le=20)


# ---- content / videos ----
class VideoIn(BaseModel):
    title: str
    pillar: str = ""
    format: str = "long"
    idea_id: int | None = None


class VideoUpdate(BaseModel):
    title: str | None = None
    pillar: str | None = None
    research_brief: str | None = None
    script: str | None = None
    description: str | None = None
    tags: str | None = None
    thumbnail_brief: str | None = None
    scheduled_at: datetime | None = None
    youtube_url: str | None = None


class ClaimIn(BaseModel):
    text: str
    source_url: str = ""
    source_note: str = ""


class ClaimUpdate(BaseModel):
    status: str | None = None
    source_url: str | None = None
    source_note: str | None = None
    verified_by: str | None = None


class ClaimOut(ORMModel):
    id: int
    video_id: int
    text: str
    source_url: str
    source_note: str
    status: str
    verified_by: str


class VideoOut(ORMModel):
    id: int
    idea_id: int | None
    title: str
    pillar: str
    format: str
    status: str
    research_brief: str
    script: str
    description: str
    tags: str
    thumbnail_brief: str
    scheduled_at: datetime | None
    published_at: datetime | None
    youtube_url: str
    claims: list[ClaimOut] = []


# ---- seo ----
class SeoScoreIn(BaseModel):
    title: str
    description: str = ""
    tags: str = ""


class SeoScoreOut(BaseModel):
    score: int
    checks: list[dict]
    suggestions: list[str]


# ---- trends ----
class TrendKeywordIn(BaseModel):
    keyword: str
    category: str = ""


class TrendPointIn(BaseModel):
    interest: float = Field(ge=0, le=100)
    date: datetime | None = None


class TrendOut(BaseModel):
    id: int
    keyword: str
    category: str
    latest: float
    growth_pct: float
    momentum: str
    points: list[dict]


# ---- competitors ----
class CompetitorIn(BaseModel):
    name: str
    channel_url: str = ""
    niche_overlap: str = ""
    notes: str = ""


class SnapshotIn(BaseModel):
    subscribers: int = 0
    total_views: int = 0
    videos: int = 0
    date: datetime | None = None


class CompetitorOut(ORMModel):
    id: int
    name: str
    channel_url: str
    niche_overlap: str
    notes: str


# ---- analytics ----
class MetricIn(BaseModel):
    video_id: int
    views: int = 0
    watch_hours: float = 0.0
    ctr: float = 0.0
    avg_percentage_viewed: float = 0.0
    subscribers_gained: int = 0
    revenue: float = 0.0
    date: datetime | None = None


# ---- assistant ----
class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


class ChatOut(BaseModel):
    reply: str
    model: str


# ---- prompts / knowledge / tasks ----
class PromptIn(BaseModel):
    name: str
    purpose: str = ""
    body: str = ""


class PromptOut(ORMModel):
    id: int
    name: str
    purpose: str
    body: str
    version: int


class ArticleIn(BaseModel):
    title: str
    category: str = ""
    body: str = ""


class ArticleOut(ORMModel):
    id: int
    title: str
    category: str
    body: str


class TaskIn(BaseModel):
    title: str
    detail: str = ""
    video_id: int | None = None
    due_at: datetime | None = None


class TaskOut(ORMModel):
    id: int
    title: str
    detail: str
    video_id: int | None
    due_at: datetime | None
    done: bool
