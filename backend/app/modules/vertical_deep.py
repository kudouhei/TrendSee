"""
Module 4: 垂直精分 (Vertical Deep Dive)
Produces a comprehensive deep-dive report on a niche vertical.
Output: long-form report + video script outline (monthly 1-2x).
"""
import asyncio
import json
from typing import Dict, List, Optional

from loguru import logger

from app.agents import AGENT_REGISTRY
from app.analysis.engagement import score_engagement
from app.analysis.sentiment import analyze_sentiment
from app.analysis.lifecycle import classify_single_item
from app.analysis.ai_engine import _chat, generate_wechat_article
from app.core.database import AsyncSessionLocal
from app.models import TrendReport, GeneratedContent


class VerticalDeepModule:
    MODULE_NAME = "vertical_deep"

    async def run(
        self,
        vertical: str,         # e.g. "新能源汽车", "国货美妆", "AI工具"
        sub_topics: List[str],
        platforms: List[str],
        output_types: List[str] = None,   # ["report", "video_script", "wechat"]
        limit_per_source: int = 30,
        **agent_kwargs,
    ) -> Dict:
        if output_types is None:
            output_types = ["report", "wechat"]

        logger.info(f"[VerticalDeep] vertical={vertical} sub_topics={sub_topics}")

        # ── Collect for each sub-topic ────────────────────────────────────────
        all_data: Dict[str, List] = {}
        for sub in sub_topics:
            items = []
            tasks = [
                AGENT_REGISTRY[p]().safe_fetch(keyword=sub, limit=limit_per_source, **agent_kwargs)
                for p in platforms if p in AGENT_REGISTRY
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    items.extend(r)
            all_data[sub] = items

        # ── Per-sub-topic analysis ────────────────────────────────────────────
        sub_analysis = {}
        for sub, items in all_data.items():
            scored = []
            for item in items:
                eng  = score_engagement(item.platform, item.likes, item.comments, item.collects, item.shares)
                sent = analyze_sentiment(item.title + " " + item.content)
                lc   = classify_single_item(eng.virality_score)
                scored.append({"item": item, "eng": eng, "sent": sent, "lc": lc})

            if scored:
                sub_analysis[sub] = {
                    "total": len(scored),
                    "avg_virality": round(sum(s["eng"].virality_score for s in scored) / len(scored), 2),
                    "phase": max(set(s["lc"].phase for s in scored), key=lambda p: sum(1 for s in scored if s["lc"].phase == p)),
                    "top_items": [
                        {"title": s["item"].title, "platform": s["item"].platform,
                         "virality": s["eng"].virality_score, "sentiment": s["sent"].label}
                        for s in sorted(scored, key=lambda x: x["eng"].virality_score, reverse=True)[:3]
                    ],
                    "sentiment_mix": {
                        "positive": sum(1 for s in scored if s["sent"].label == "positive"),
                        "neutral":  sum(1 for s in scored if s["sent"].label == "neutral"),
                        "negative": sum(1 for s in scored if s["sent"].label == "negative"),
                    }
                }

        # ── AI deep report ────────────────────────────────────────────────────
        deep_report = await self._ai_deep_report(vertical, sub_topics, sub_analysis)

        # ── Generate outputs ──────────────────────────────────────────────────
        generated = {}
        key_insights = deep_report.get("key_findings", [])

        if "wechat" in output_types:
            wechat = await generate_wechat_article(
                topic=vertical,
                key_insights=key_insights,
                module="垂直精分",
                trend_data=sub_analysis,
            )
            generated["wechat"] = wechat

        if "video_script" in output_types:
            script = await self._generate_video_script(vertical, deep_report)
            generated["video_script"] = script

        result = {
            "module": self.MODULE_NAME,
            "vertical": vertical,
            "sub_topics": sub_topics,
            "sub_analysis": sub_analysis,
            "deep_report": deep_report,
            "generated_content": generated,
        }

        await self._persist(vertical, result, generated)
        return result

    async def _ai_deep_report(self, vertical: str, sub_topics: List[str], sub_analysis: Dict) -> Dict:
        analysis_text = json.dumps(sub_analysis, ensure_ascii=False, indent=2)[:2000]
        prompt = f"""你是垂直行业研究专家。目标垂类：「{vertical}」

子话题：{', '.join(sub_topics)}
各子话题数据分析：
{analysis_text}

请生成深度行业报告框架：

返回JSON：
{{
  "industry_overview": "行业现状概述（150字）",
  "key_findings": ["核心发现1", "核心发现2", "核心发现3", "核心发现4", "核心发现5"],
  "trend_signals": [
    {{"signal": "趋势信号", "evidence": "数据依据", "phase": "rising/peak/declining"}}
  ],
  "user_profile": {{
    "core_audience": "核心受众画像",
    "pain_points": ["痛点1", "痛点2"],
    "desires": ["欲望/需求1", "需求2"]
  }},
  "content_opportunities": [
    {{"angle": "内容角度", "format": "适合的内容形式", "why": "为什么有潜力"}}
  ],
  "market_insight": "商业洞察（100字）",
  "report_title": "深度报告标题"
}}"""

        raw = await _chat([
            {"role": "system", "content": "你是专业行业研究分析师，只返回有效JSON。"},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=2000)

        try:
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)
        except Exception:
            return {"industry_overview": "", "key_findings": [], "content_opportunities": []}

    async def _generate_video_script(self, vertical: str, deep_report: Dict) -> Dict:
        findings = deep_report.get("key_findings", [])
        prompt = f"""你是财经/社会议题视频博主的选题策划。主题：「{vertical}」

核心发现：
{chr(10).join(f'{i+1}. {f}' for i, f in enumerate(findings[:5]))}

请生成一个5-8分钟的视频脚本大纲：

返回JSON：
{{
  "video_title": "视频标题（含钩子）",
  "hook": "开场钩子（前15秒说什么）",
  "outline": [
    {{"section": "段落名", "duration": "时长", "key_points": ["要点1", "要点2"], "visual_note": "画面/数据展示建议"}}
  ],
  "call_to_action": "结尾号召行动",
  "thumbnail_idea": "封面缩略图创意"
}}"""

        raw = await _chat([
            {"role": "system", "content": "你是专业视频内容策划，只返回有效JSON。"},
            {"role": "user", "content": prompt},
        ], temperature=0.7, max_tokens=1500)

        try:
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)
        except Exception:
            return {"video_title": vertical, "outline": []}

    async def _persist(self, vertical: str, result: Dict, generated: Dict) -> int:
        deep_report = result.get("deep_report", {})
        async with AsyncSessionLocal() as db:
            report = TrendReport(
                module=self.MODULE_NAME,
                title=deep_report.get("report_title", f"垂直精分 — {vertical}"),
                period_label="",
                platforms=[],
                total_items=sum(v.get("total", 0) for v in result["sub_analysis"].values()),
                top_topics=result["sub_topics"],
                trend_chart_data={"sub_analysis": result["sub_analysis"]},
                executive_summary=deep_report.get("industry_overview", ""),
                deep_insights=deep_report.get("key_findings", []),
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            for platform_key, content in generated.items():
                if isinstance(content, dict) and content.get("body"):
                    gc = GeneratedContent(
                        report_id=report.id,
                        output_platform=platform_key,
                        content_type="article" if platform_key == "wechat" else "script",
                        title=content.get("title", vertical),
                        body=content.get("body", ""),
                        hashtags=content.get("hashtags", []),
                        cover_prompt=content.get("cover_prompt", ""),
                    )
                    db.add(gc)

            await db.commit()
            return report.id
