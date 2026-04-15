"""
Module 1: 趋势雷达 (Trend Radar)
Weekly/monthly cross-platform trend aggregation.
Identifies rising signals before they peak.
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import jieba
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENT_REGISTRY
from app.analysis.engagement import score_engagement
from app.analysis.sentiment import analyze_sentiment
from app.analysis.lifecycle import classify_single_item
from app.analysis.ai_engine import generate_report_narrative
from app.models import RawTrendItem, TrendAnalysis, TrendReport
from app.core.database import AsyncSessionLocal


class TrendRadarModule:
    MODULE_NAME = "trend_radar"

    async def run(
        self,
        keywords: List[str],
        platforms: List[str],
        period: str = "weekly",   # weekly | monthly | custom
        limit_per_source: int = 30,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        **agent_kwargs,
    ) -> Dict:
        """
        Full pipeline: collect → analyse → aggregate → narrate → persist.
        When date_from/date_to are provided, period is treated as "custom" and
        keywords default to [] so each platform fetches its current hot-list.
        Returns the report dict.
        """
        is_date_range = bool(date_from and date_to)
        if is_date_range:
            period = "custom"
            keywords = keywords or []

        logger.info(
            f"[TrendRadar] Starting run | period={period} | keywords={keywords} "
            f"| date_range={date_from}~{date_to}"
        )

        # When a date range is given, pass it as a timeframe hint to Google Trends.
        if is_date_range:
            agent_kwargs.setdefault("timeframe", f"{date_from} {date_to}")

        # ── 1. Collect ────────────────────────────────────────────────────────
        all_items = []
        tasks = []
        for platform in platforms:
            agent_cls = AGENT_REGISTRY.get(platform)
            if not agent_cls:
                continue
            agent = agent_cls()
            for kw in (keywords or [""]):
                tasks.append(agent.safe_fetch(keyword=kw, limit=limit_per_source, **agent_kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)

        logger.info(f"[TrendRadar] Collected {len(all_items)} raw items")

        # ── 2. Analyse ────────────────────────────────────────────────────────
        analysed = []
        for item in all_items:
            eng = score_engagement(
                item.platform, item.likes, item.comments, item.collects, item.shares, item.views
            )
            sent = analyze_sentiment(item.title + " " + item.content)
            lifecycle = classify_single_item(eng.virality_score)

            analysed.append({
                "item": item,
                "engagement_score": eng.engagement_score,
                "virality_score": eng.virality_score,
                "sentiment": sent,
                "lifecycle": lifecycle,
            })

        # ── 3. Aggregate topics ───────────────────────────────────────────────
        topic_counter: Dict[str, float] = defaultdict(float)
        for a in analysed:
            words = list(jieba.cut(a["item"].title))
            for w in words:
                if len(w) >= 2:
                    topic_counter[w] += a["virality_score"]

        top_topics = sorted(topic_counter.items(), key=lambda x: x[1], reverse=True)[:20]
        top_topic_names = [t[0] for t in top_topics]

        # ── 4. Build chart data ───────────────────────────────────────────────
        platform_breakdown = defaultdict(int)
        phase_distribution = defaultdict(int)
        sentiment_dist = defaultdict(int)
        for a in analysed:
            platform_breakdown[a["item"].platform] += 1
            phase_distribution[a["lifecycle"].phase] += 1
            sentiment_dist[a["sentiment"].label] += 1

        engagement_stats = {
            "avg_engagement": round(sum(a["engagement_score"] for a in analysed) / max(len(analysed), 1), 2),
            "avg_virality":   round(sum(a["virality_score"]   for a in analysed) / max(len(analysed), 1), 2),
            "total_items":    len(analysed),
        }

        # Sort top items by virality
        top_items = sorted(analysed, key=lambda x: x["virality_score"], reverse=True)[:10]
        top_items_data = [
            {
                "title": a["item"].title,
                "platform": a["item"].platform,
                "virality_score": a["virality_score"],
                "engagement_score": a["engagement_score"],
                "sentiment": a["sentiment"].label,
                "lifecycle": a["lifecycle"].phase,
                "url": a["item"].url,
            }
            for a in top_items
        ]

        # ── 5. AI narrative ───────────────────────────────────────────────────
        period_label = self._period_label(period, date_from, date_to)
        narrative = await generate_report_narrative(
            module="趋势雷达",
            period_label=period_label,
            top_topics=top_topic_names,
            engagement_stats=engagement_stats,
            platform_breakdown=dict(platform_breakdown),
        )

        # ── 6. Persist ────────────────────────────────────────────────────────
        report_id = await self._persist(
            period_label=period_label,
            platforms=platforms,
            total_items=len(analysed),
            top_topics=top_topic_names,
            trend_chart_data={
                "platform_breakdown": dict(platform_breakdown),
                "phase_distribution": dict(phase_distribution),
                "sentiment_dist":     dict(sentiment_dist),
                "top_items":          top_items_data,
                "top_topics_weighted": [{"topic": t, "score": s} for t, s in top_topics],
            },
            narrative=narrative,
        )

        return {
            "report_id":         report_id,
            "module":            self.MODULE_NAME,
            "period_label":      period_label,
            "total_items":       len(analysed),
            "top_topics":        top_topic_names,
            "top_items":         top_items_data,
            "platform_breakdown": dict(platform_breakdown),
            "phase_distribution": dict(phase_distribution),
            "sentiment_dist":    dict(sentiment_dist),
            "engagement_stats":  engagement_stats,
            "narrative":         narrative,
        }

    async def _persist(self, **kwargs) -> int:
        narrative = kwargs.pop("narrative", {})
        async with AsyncSessionLocal() as db:
            report = TrendReport(
                module=self.MODULE_NAME,
                title=f"趋势雷达 — {kwargs['period_label']}",
                period_label=kwargs["period_label"],
                platforms=kwargs["platforms"],
                total_items=kwargs["total_items"],
                top_topics=kwargs["top_topics"],
                trend_chart_data=kwargs["trend_chart_data"],
                executive_summary=narrative.get("executive_summary", ""),
                deep_insights=narrative.get("deep_insights", []),
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            return report.id

    @staticmethod
    def _period_label(
        period: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        if period == "custom" and date_from and date_to:
            return f"{date_from} ~ {date_to}"
        now = datetime.utcnow()
        if period == "weekly":
            week = now.isocalendar()[1]
            return f"{now.year}-W{week:02d}"
        return f"{now.year}-{now.month:02d}"
