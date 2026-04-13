"""
Generated content for different target platforms.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GeneratedContent(Base):
    """AI-generated post/article for a specific output platform."""
    __tablename__ = "generated_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("trend_reports.id"))

    # Target output platform
    output_platform: Mapped[str] = mapped_column(String(32))  # xhs | wechat | general
    content_type: Mapped[str] = mapped_column(String(32))     # post | article | script

    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    cover_prompt: Mapped[Optional[str]] = mapped_column(Text)  # DALL-E / MJ prompt hint
    meta: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report: Mapped["TrendReport"] = relationship(back_populates="generated_contents")  # noqa

    __table_args__ = (Index("ix_generated_contents_platform", "output_platform"),)


class CollectionJob(Base):
    """Track background data collection jobs."""
    __tablename__ = "collection_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(64))        # agent name
    status: Mapped[str] = mapped_column(String(16), default="pending")
    params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    result_summary: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
