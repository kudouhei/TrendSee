"""
Core data models for raw trend signals and analyzed insights.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class Platform(str, enum.Enum):
    XHS = "xhs"
    DOUYIN = "douyin"
    REDDIT = "reddit"
    GOOGLE_TRENDS = "google_trends"


class TrendPhase(str, enum.Enum):
    RISING = "rising"
    PEAK = "peak"
    DECLINING = "declining"
    STABLE = "stable"
    UNKNOWN = "unknown"


class RawTrendItem(Base):
    """Raw scraped item from any platform."""
    __tablename__ = "raw_trend_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(256))
    url: Mapped[Optional[str]] = mapped_column(Text)

    # Engagement
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    collects: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped[Optional["TrendAnalysis"]] = relationship(
        back_populates="raw_item", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_raw_trend_platform_extid", "platform", "external_id", unique=True),
        Index("ix_raw_trend_collected_at", "collected_at"),
    )


class TrendAnalysis(Base):
    """AI-generated analysis for a raw trend item."""
    __tablename__ = "trend_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_trend_items.id"), unique=True)

    # Scores
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)  # -1 to 1
    sentiment_label: Mapped[str] = mapped_column(String(16), default="neutral")
    virality_score: Mapped[float] = mapped_column(Float, default=0.0)   # 0 to 100
    trend_phase: Mapped[str] = mapped_column(String(16), default=TrendPhase.UNKNOWN)

    # AI insights
    summary: Mapped[Optional[str]] = mapped_column(Text)
    key_insights: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    emotion_tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    topic_clusters: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    raw_item: Mapped["RawTrendItem"] = relationship(back_populates="analysis")

    __table_args__ = (Index("ix_trend_analyses_virality", "virality_score"),)


class TrendReport(Base):
    """Aggregated module report (radar / mining / anatomy / vertical)."""
    __tablename__ = "trend_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    period_label: Mapped[str] = mapped_column(String(64))    # e.g. "2025-W03"
    platforms: Mapped[list] = mapped_column(JSON, default=list)

    # Aggregated stats
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    top_topics: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    trend_chart_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # AI narrative
    executive_summary: Mapped[Optional[str]] = mapped_column(Text)
    deep_insights: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    generated_contents: Mapped[list["GeneratedContent"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
