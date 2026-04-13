"""
Celery application configuration with periodic schedule.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "trendsee",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Periodic schedule ──────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Trend Radar — every Monday 08:00
    "weekly-trend-radar": {
        "task": "app.tasks.jobs.run_trend_radar",
        "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
        "kwargs": {
            "keywords": ["AI", "新消费", "出海", "国潮", "社交电商"],
            "platforms": ["xhs", "douyin", "reddit", "google_trends"],
            "period": "weekly",
        },
    },
    # Douyin hot list — every day 09:00
    "daily-douyin-hotlist": {
        "task": "app.tasks.jobs.collect_platform",
        "schedule": crontab(hour=9, minute=0),
        "kwargs": {"platform": "douyin", "keyword": "", "limit": 50},
    },
    # Reddit trending — every 6 hours
    "reddit-trending": {
        "task": "app.tasks.jobs.collect_platform",
        "schedule": crontab(minute=0, hour="*/6"),
        "kwargs": {"platform": "reddit", "keyword": "", "limit": 30},
    },
    # Google Trends — every day 07:00
    "daily-google-trends": {
        "task": "app.tasks.jobs.collect_platform",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"platform": "google_trends", "keyword": "", "limit": 20},
    },
}
