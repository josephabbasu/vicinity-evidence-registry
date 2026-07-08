from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Content pipeline states, in order. A video may only advance one step at a
# time, and may not pass fact_checked while any claim is unverified.
PIPELINE_STATES = [
    "idea",
    "researched",
    "scripted",
    "fact_checked",
    "voiced",
    "edited",
    "thumbnail",
    "scheduled",
    "published",
    "analyzed",
]

CLAIM_STATES = ["unverified", "verified", "corrected", "cut"]


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Idea(Base):
    __tablename__ = "ideas"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    pillar: Mapped[str] = mapped_column(String(120), default="")
    format: Mapped[str] = mapped_column(String(40), default="long")  # long | short
    notes: Mapped[str] = mapped_column(Text, default="")
    # 1-10 opportunity scores, mirroring the Phase 1 ranking criteria
    demand: Mapped[int] = mapped_column(Integer, default=5)
    evergreen: Mapped[int] = mapped_column(Integer, default=5)
    competition_gap: Mapped[int] = mapped_column(Integer, default=5)
    monetization: Mapped[int] = mapped_column(Integer, default=5)
    production_ease: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(30), default="backlog")  # backlog|selected|archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def score(self) -> float:
        # Weighted to favor demand/evergreen/monetization, per the market analysis
        return round(
            0.25 * self.demand
            + 0.25 * self.evergreen
            + 0.15 * self.competition_gap
            + 0.20 * self.monetization
            + 0.15 * self.production_ease,
            2,
        )


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[int | None] = mapped_column(ForeignKey("ideas.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    pillar: Mapped[str] = mapped_column(String(120), default="")
    format: Mapped[str] = mapped_column(String(40), default="long")
    status: Mapped[str] = mapped_column(String(40), default="idea", index=True)
    research_brief: Mapped[str] = mapped_column(Text, default="")
    script: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    thumbnail_brief: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    youtube_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    claims: Mapped[list["Claim"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    metrics: Mapped[list["VideoMetric"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class Claim(Base):
    """A factual claim in a script. The pipeline blocks past fact_checked
    while any claim is unverified — this is the trust gate."""

    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    source_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="unverified")
    verified_by: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    video: Mapped[Video] = relationship(back_populates="claims")


class VideoMetric(Base):
    __tablename__ = "video_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    views: Mapped[int] = mapped_column(Integer, default=0)
    watch_hours: Mapped[float] = mapped_column(Float, default=0.0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)  # percent
    avg_percentage_viewed: Mapped[float] = mapped_column(Float, default=0.0)  # percent
    subscribers_gained: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    video: Mapped[Video] = relationship(back_populates="metrics")


class TrendKeyword(Base):
    __tablename__ = "trend_keywords"
    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    points: Mapped[list["TrendPoint"]] = relationship(back_populates="keyword_ref", cascade="all, delete-orphan")


class TrendPoint(Base):
    __tablename__ = "trend_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("trend_keywords.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    interest: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 relative interest

    keyword_ref: Mapped[TrendKeyword] = relationship(back_populates="points")


class Competitor(Base):
    __tablename__ = "competitors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    channel_url: Mapped[str] = mapped_column(String(500), default="")
    niche_overlap: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )


class CompetitorSnapshot(Base):
    __tablename__ = "competitor_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    subscribers: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    videos: Mapped[int] = mapped_column(Integer, default=0)

    competitor: Mapped[Competitor] = relationship(back_populates="snapshots")


class Prompt(Base):
    __tablename__ = "prompts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    purpose: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(120), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text, default="")
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
