"""
Content Generation Pipeline — wraps AI generation and persists outputs.
Called after any module produces a report.
"""
import json
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.ai_engine import generate_xhs_post, generate_wechat_article
from app.models import TrendReport, GeneratedContent


async def generate_all_formats(
    report: TrendReport,
    db: AsyncSession,
    output_platforms: List[str] = None,
) -> Dict[str, int]:
    """
    Generate XHS + WeChat posts from a completed report.
    Returns {platform: generated_content_id}.
    """
    if output_platforms is None:
        output_platforms = ["xhs", "wechat"]

    key_insights: List[str] = []
    if report.deep_insights:
        if isinstance(report.deep_insights[0], dict):
            key_insights = [i.get("body") or i.get("title", "") for i in report.deep_insights]
        else:
            key_insights = report.deep_insights

    topic = report.top_topics[0] if report.top_topics else report.title
    results = {}

    if "xhs" in output_platforms:
        try:
            xhs_data = await generate_xhs_post(
                topic=topic,
                key_insights=key_insights,
                module=report.module,
                extra_context=report.executive_summary or "",
            )
            gc = GeneratedContent(
                report_id=report.id,
                output_platform="xhs",
                content_type="post",
                title=xhs_data.get("title", topic),
                body=xhs_data.get("body", ""),
                hashtags=xhs_data.get("hashtags", []),
                cover_prompt=xhs_data.get("cover_prompt", ""),
            )
            db.add(gc)
            await db.flush()
            results["xhs"] = gc.id
            logger.info(f"[ContentPipeline] XHS post generated, id={gc.id}")
        except Exception as e:
            logger.error(f"[ContentPipeline] XHS generation failed: {e}")

    if "wechat" in output_platforms:
        try:
            wc_data = await generate_wechat_article(
                topic=topic,
                key_insights=key_insights,
                module=report.module,
                trend_data=report.trend_chart_data,
                extra_context=report.executive_summary or "",
            )
            gc = GeneratedContent(
                report_id=report.id,
                output_platform="wechat",
                content_type="article",
                title=wc_data.get("title", topic),
                body=wc_data.get("body", ""),
                hashtags=wc_data.get("hashtags", []),
                meta={"subtitle": wc_data.get("subtitle", "")},
            )
            db.add(gc)
            await db.flush()
            results["wechat"] = gc.id
            logger.info(f"[ContentPipeline] WeChat article generated, id={gc.id}")
        except Exception as e:
            logger.error(f"[ContentPipeline] WeChat generation failed: {e}")

    await db.commit()
    return results
