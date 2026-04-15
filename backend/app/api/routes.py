"""
FastAPI REST API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import TrendReport, GeneratedContent, CollectionJob, RawTrendItem

router = APIRouter()


# ── Request schemas ────────────────────────────────────────────────────────────

class TrendRadarRequest(BaseModel):
    keywords: List[str] = []
    platforms: List[str] = ["xhs", "douyin", "reddit", "google_trends"]
    period: str = "weekly"
    limit_per_source: int = 30
    # Optional date range mode — when provided, overrides `period` and fetches
    # hot topics for the given date window (YYYY-MM-DD).
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class CommentMiningRequest(BaseModel):
    topic: str
    platforms: List[str] = ["xhs", "douyin", "reddit"]
    limit_per_source: int = 50

class ViralAnatomyRequest(BaseModel):
    topic: str
    platforms: List[str] = ["xhs", "douyin"]
    limit_per_source: int = 20

class VerticalDeepRequest(BaseModel):
    vertical: str
    sub_topics: List[str]
    platforms: List[str] = ["xhs", "douyin", "reddit", "google_trends"]
    output_types: List[str] = ["wechat", "video_script"]
    limit_per_source: int = 30

class CollectRequest(BaseModel):
    platform: str
    keyword: str = ""
    limit: int = 50

class GenerateContentRequest(BaseModel):
    report_id: int
    output_platforms: List[str] = ["xhs", "wechat"]


# ── Dashboard / Stats ─────────────────────────────────────────────────────────

@router.get("/dashboard/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_items   = (await db.execute(select(func.count(RawTrendItem.id)))).scalar() or 0
    total_reports = (await db.execute(select(func.count(TrendReport.id)))).scalar() or 0
    total_content = (await db.execute(select(func.count(GeneratedContent.id)))).scalar() or 0
    total_jobs    = (await db.execute(select(func.count(CollectionJob.id)))).scalar() or 0

    platform_dist_rows = await db.execute(
        select(RawTrendItem.platform, func.count(RawTrendItem.id))
        .group_by(RawTrendItem.platform)
    )
    platform_dist = {row[0]: row[1] for row in platform_dist_rows.all()}

    recent_reports = (await db.execute(
        select(TrendReport).order_by(desc(TrendReport.created_at)).limit(5)
    )).scalars().all()

    return {
        "total_items":   total_items,
        "total_reports": total_reports,
        "total_content": total_content,
        "total_jobs":    total_jobs,
        "platform_distribution": platform_dist,
        "recent_reports": [
            {"id": r.id, "module": r.module, "title": r.title, "created_at": r.created_at.isoformat()}
            for r in recent_reports
        ],
    }


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports")
async def list_reports(
    module: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(TrendReport).order_by(desc(TrendReport.created_at)).limit(limit).offset(offset)
    if module:
        q = q.where(TrendReport.module == module)
    reports = (await db.execute(q)).scalars().all()
    return [
        {
            "id": r.id, "module": r.module, "title": r.title,
            "period_label": r.period_label, "total_items": r.total_items,
            "top_topics": r.top_topics, "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(TrendReport).where(TrendReport.id == report_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Report not found")
    return {
        "id": r.id, "module": r.module, "title": r.title,
        "period_label": r.period_label, "platforms": r.platforms,
        "total_items": r.total_items, "top_topics": r.top_topics,
        "trend_chart_data": r.trend_chart_data,
        "executive_summary": r.executive_summary,
        "deep_insights": r.deep_insights,
        "created_at": r.created_at.isoformat(),
    }


@router.get("/reports/{report_id}/content")
async def get_report_content(report_id: int, db: AsyncSession = Depends(get_db)):
    items = (await db.execute(
        select(GeneratedContent).where(GeneratedContent.report_id == report_id)
    )).scalars().all()
    return [
        {
            "id": c.id, "output_platform": c.output_platform,
            "content_type": c.content_type, "title": c.title,
            "body": c.body, "hashtags": c.hashtags,
            "cover_prompt": c.cover_prompt, "meta": c.meta,
            "created_at": c.created_at.isoformat(),
        }
        for c in items
    ]


# ── Module triggers ───────────────────────────────────────────────────────────

@router.post("/modules/trend-radar")
async def trigger_trend_radar(req: TrendRadarRequest, background_tasks: BackgroundTasks):
    from app.tasks.jobs import run_trend_radar
    task = run_trend_radar.delay(
        keywords=req.keywords,
        platforms=req.platforms,
        period=req.period,
        date_from=req.date_from,
        date_to=req.date_to,
    )
    return {"task_id": task.id, "status": "queued", "module": "trend_radar"}


@router.post("/modules/comment-mining")
async def trigger_comment_mining(req: CommentMiningRequest, background_tasks: BackgroundTasks):
    from app.tasks.jobs import run_comment_mining
    task = run_comment_mining.delay(topic=req.topic, platforms=req.platforms)
    return {"task_id": task.id, "status": "queued", "module": "comment_mining"}


@router.post("/modules/viral-anatomy")
async def trigger_viral_anatomy(req: ViralAnatomyRequest):
    from app.tasks.jobs import run_viral_anatomy
    task = run_viral_anatomy.delay(topic=req.topic, platforms=req.platforms)
    return {"task_id": task.id, "status": "queued", "module": "viral_anatomy"}


@router.post("/modules/vertical-deep")
async def trigger_vertical_deep(req: VerticalDeepRequest):
    from app.tasks.jobs import run_vertical_deep
    task = run_vertical_deep.delay(
        vertical=req.vertical,
        sub_topics=req.sub_topics,
        platforms=req.platforms,
        output_types=req.output_types,
    )
    return {"task_id": task.id, "status": "queued", "module": "vertical_deep"}


# ── Direct (synchronous) run for testing ─────────────────────────────────────

@router.post("/modules/trend-radar/run-now")
async def run_trend_radar_now(req: TrendRadarRequest):
    from app.modules.trend_radar import TrendRadarModule
    result = await TrendRadarModule().run(
        keywords=req.keywords,
        platforms=req.platforms,
        period=req.period,
        limit_per_source=req.limit_per_source,
        date_from=req.date_from,
        date_to=req.date_to,
    )
    return result


@router.post("/modules/comment-mining/run-now")
async def run_comment_mining_now(req: CommentMiningRequest):
    from app.modules.comment_mining import CommentMiningModule
    return await CommentMiningModule().run(
        topic=req.topic, platforms=req.platforms, limit_per_source=req.limit_per_source
    )


@router.post("/modules/viral-anatomy/run-now")
async def run_viral_anatomy_now(req: ViralAnatomyRequest):
    from app.modules.viral_anatomy import ViralAnatomyModule
    return await ViralAnatomyModule().run(
        topic=req.topic, platforms=req.platforms, limit_per_source=req.limit_per_source
    )


@router.post("/modules/vertical-deep/run-now")
async def run_vertical_deep_now(req: VerticalDeepRequest):
    from app.modules.vertical_deep import VerticalDeepModule
    return await VerticalDeepModule().run(
        vertical=req.vertical,
        sub_topics=req.sub_topics,
        platforms=req.platforms,
        output_types=req.output_types,
        limit_per_source=req.limit_per_source,
    )


# ── Re-generate AI narrative for an existing report ───────────────────────────

@router.post("/reports/{report_id}/regenerate-narrative")
async def regenerate_narrative(report_id: int, db: AsyncSession = Depends(get_db)):
    """Re-run the AI narrative step for a report whose executive_summary is missing."""
    from app.analysis.ai_engine import generate_report_narrative

    r = (await db.execute(select(TrendReport).where(TrendReport.id == report_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Report not found")

    narrative = await generate_report_narrative(
        module=r.module,
        period_label=r.period_label or "",
        top_topics=(r.top_topics or [])[:10],
        engagement_stats={"total_items": r.total_items},
        platform_breakdown=(r.trend_chart_data or {}).get("platform_breakdown", {}),
    )

    r.executive_summary = narrative.get("executive_summary", "")
    r.deep_insights = narrative.get("deep_insights", [])
    await db.commit()

    return {
        "report_id": report_id,
        "executive_summary": r.executive_summary,
        "deep_insights": r.deep_insights,
    }


# ── Content generation ────────────────────────────────────────────────────────

@router.post("/content/generate")
async def generate_content(req: GenerateContentRequest, db: AsyncSession = Depends(get_db)):
    from app.models import TrendReport
    from app.generators.content_pipeline import generate_all_formats

    r = (await db.execute(select(TrendReport).where(TrendReport.id == req.report_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Report not found")
    results = await generate_all_formats(r, db, req.output_platforms)
    return {"generated": results}


# ── Collection jobs ───────────────────────────────────────────────────────────

@router.post("/collect")
async def trigger_collect(req: CollectRequest):
    from app.tasks.jobs import collect_platform
    task = collect_platform.delay(platform=req.platform, keyword=req.keyword, limit=req.limit)
    return {"task_id": task.id, "status": "queued"}


@router.get("/jobs")
async def list_jobs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    jobs = (await db.execute(
        select(CollectionJob).order_by(desc(CollectionJob.created_at)).limit(limit)
    )).scalars().all()
    return [
        {
            "id": j.id, "job_type": j.job_type, "status": j.status,
            "params": j.params, "result_summary": j.result_summary,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


# ── Raw items ─────────────────────────────────────────────────────────────────

@router.get("/items")
async def list_items(
    platform: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(RawTrendItem).order_by(desc(RawTrendItem.collected_at)).limit(limit).offset(offset)
    if platform:
        q = q.where(RawTrendItem.platform == platform)
    items = (await db.execute(q)).scalars().all()
    return [
        {
            "id": i.id, "platform": i.platform, "title": i.title,
            "author": i.author, "url": i.url,
            "likes": i.likes, "comments": i.comments,
            "collects": i.collects, "shares": i.shares,
            "tags": i.tags, "collected_at": i.collected_at.isoformat(),
        }
        for i in items
    ]


# ── Task status ───────────────────────────────────────────────────────────────

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    from app.tasks.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
