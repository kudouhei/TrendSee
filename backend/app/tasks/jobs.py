"""
Celery task definitions.
All heavy I/O runs inside asyncio via celery-executor bridge.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from app.tasks.celery_app import celery_app


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.tasks.jobs.collect_platform", max_retries=3)
def collect_platform(self, platform: str, keyword: str = "", limit: int = 50, **kwargs):
    """Collect raw data from a single platform and persist to DB."""
    from app.agents import AGENT_REGISTRY
    from app.core.database import AsyncSessionLocal
    from app.models import RawTrendItem, CollectionJob

    async def _inner():
        async with AsyncSessionLocal() as db:
            job = CollectionJob(
                job_type=f"collect_{platform}",
                status="running",
                params={"keyword": keyword, "limit": limit},
                started_at=datetime.utcnow(),
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            try:
                agent_cls = AGENT_REGISTRY.get(platform)
                if not agent_cls:
                    raise ValueError(f"Unknown platform: {platform}")

                items = await agent_cls().safe_fetch(keyword=keyword, limit=limit, **kwargs)

                saved = 0
                for item in items:
                    try:
                        existing = await db.execute(
                            __import__("sqlalchemy", fromlist=["select"]).select(RawTrendItem).where(
                                RawTrendItem.platform == item.platform,
                                RawTrendItem.external_id == item.external_id,
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        row = RawTrendItem(
                            platform=item.platform,
                            external_id=item.external_id,
                            title=item.title,
                            content=item.content,
                            author=item.author,
                            url=item.url,
                            likes=item.likes,
                            comments=item.comments,
                            shares=item.shares,
                            collects=item.collects,
                            views=item.views,
                            tags=item.tags,
                            extra=item.extra,
                            published_at=item.published_at,
                        )
                        db.add(row)
                        saved += 1
                    except Exception:
                        pass

                await db.commit()

                job.status = "success"
                job.result_summary = {"saved": saved, "total": len(items)}
                job.finished_at = datetime.utcnow()
                await db.commit()

                logger.info(f"[collect_platform] {platform} saved={saved}")
                return {"saved": saved, "total": len(items)}

            except Exception as exc:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.utcnow()
                await db.commit()
                raise

    try:
        return _run_async(_inner())
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, name="app.tasks.jobs.run_trend_radar", max_retries=2)
def run_trend_radar(self, keywords: List[str], platforms: List[str], period: str = "weekly", **kwargs):
    """Run full Trend Radar pipeline."""
    from app.modules.trend_radar import TrendRadarModule

    async def _inner():
        module = TrendRadarModule()
        return await module.run(keywords=keywords, platforms=platforms, period=period, **kwargs)

    try:
        return _run_async(_inner())
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@celery_app.task(bind=True, name="app.tasks.jobs.run_comment_mining", max_retries=2)
def run_comment_mining(self, topic: str, platforms: List[str], **kwargs):
    from app.modules.comment_mining import CommentMiningModule

    async def _inner():
        return await CommentMiningModule().run(topic=topic, platforms=platforms, **kwargs)

    try:
        return _run_async(_inner())
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@celery_app.task(bind=True, name="app.tasks.jobs.run_viral_anatomy", max_retries=2)
def run_viral_anatomy(self, topic: str, platforms: List[str], **kwargs):
    from app.modules.viral_anatomy import ViralAnatomyModule

    async def _inner():
        return await ViralAnatomyModule().run(topic=topic, platforms=platforms, **kwargs)

    try:
        return _run_async(_inner())
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@celery_app.task(bind=True, name="app.tasks.jobs.run_vertical_deep", max_retries=2)
def run_vertical_deep(self, vertical: str, sub_topics: List[str], platforms: List[str], **kwargs):
    from app.modules.vertical_deep import VerticalDeepModule

    async def _inner():
        return await VerticalDeepModule().run(vertical=vertical, sub_topics=sub_topics, platforms=platforms, **kwargs)

    try:
        return _run_async(_inner())
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@celery_app.task(name="app.tasks.jobs.generate_content_for_report")
def generate_content_for_report(report_id: int, output_platforms: List[str] = None):
    """Generate XHS + WeChat content for an existing report."""
    from app.core.database import AsyncSessionLocal
    from app.models import TrendReport
    from app.generators.content_pipeline import generate_all_formats
    from sqlalchemy import select

    async def _inner():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(TrendReport).where(TrendReport.id == report_id))
            report = result.scalar_one_or_none()
            if not report:
                return {"error": "report_not_found"}
            return await generate_all_formats(report, db, output_platforms)

    return _run_async(_inner())
