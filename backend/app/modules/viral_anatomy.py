"""
Module 3: 爆款解剖室 (Viral Content Anatomy)
Reverse-engineers why specific content went viral.
Identifies replicable formulas and content patterns.
"""
import asyncio
import json
from typing import Dict, List, Optional

from loguru import logger

from app.agents import AGENT_REGISTRY
from app.analysis.engagement import score_engagement
from app.analysis.sentiment import analyze_sentiment
from app.analysis.ai_engine import _chat
from app.core.database import AsyncSessionLocal
from app.models import TrendReport


class ViralAnatomyModule:
    MODULE_NAME = "viral_anatomy"

    async def run(
        self,
        topic: str,
        platforms: List[str],
        limit_per_source: int = 20,
        **agent_kwargs,
    ) -> Dict:
        logger.info(f"[ViralAnatomy] Dissecting virals for: {topic}")

        # ── Collect ───────────────────────────────────────────────────────────
        all_items = []
        tasks = [
            AGENT_REGISTRY[p]().safe_fetch(keyword=topic, limit=limit_per_source, **agent_kwargs)
            for p in platforms if p in AGENT_REGISTRY
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)

        if not all_items:
            return {"error": "no_data", "topic": topic}

        # ── Score and rank ────────────────────────────────────────────────────
        scored = []
        for item in all_items:
            eng = score_engagement(item.platform, item.likes, item.comments, item.collects, item.shares)
            sent = analyze_sentiment(item.title + " " + item.content)
            scored.append({
                "item": item,
                "engagement": eng,
                "sentiment": sent,
            })

        scored.sort(key=lambda x: x["engagement"].virality_score, reverse=True)
        top_viral = scored[:5]
        avg_viral = scored[len(scored)//2:len(scored)//2+5]  # median items as control

        # ── Anatomy ───────────────────────────────────────────────────────────
        anatomy = await self._ai_anatomy(topic, top_viral, avg_viral)

        # ── Title formula analysis ────────────────────────────────────────────
        title_patterns = self._extract_title_patterns([s["item"].title for s in top_viral])

        viral_items_data = [
            {
                "title": s["item"].title,
                "platform": s["item"].platform,
                "url": s["item"].url,
                "virality_score": s["engagement"].virality_score,
                "engagement_score": s["engagement"].engagement_score,
                "likes": s["item"].likes,
                "comments": s["item"].comments,
                "collects": s["item"].collects,
                "sentiment": s["sentiment"].label,
            }
            for s in top_viral
        ]

        result = {
            "module": self.MODULE_NAME,
            "topic": topic,
            "total_analysed": len(scored),
            "viral_items": viral_items_data,
            "title_patterns": title_patterns,
            "anatomy": anatomy,
        }

        await self._persist(topic, result)
        return result

    def _extract_title_patterns(self, titles: List[str]) -> List[Dict]:
        patterns = []
        indicators = {
            "数字型":     lambda t: any(c.isdigit() for c in t),
            "疑问型":     lambda t: "？" in t or "?" in t or "为什么" in t or "如何" in t,
            "对比型":     lambda t: "vs" in t.lower() or "对比" in t or "还是" in t,
            "悬念型":     lambda t: "竟然" in t or "居然" in t or "没想到" in t or "震惊" in t,
            "情绪型":     lambda t: any(w in t for w in ["绝了", "太厉害", "崩溃", "感动", "哭了"]),
            "实测/亲测型": lambda t: "实测" in t or "亲测" in t or "测评" in t,
            "列表型":     lambda t: "个" in t and any(c.isdigit() for c in t),
        }
        for name, test in indicators.items():
            matching = [t for t in titles if test(t)]
            if matching:
                patterns.append({
                    "pattern": name,
                    "count": len(matching),
                    "examples": matching[:2],
                })
        return sorted(patterns, key=lambda x: x["count"], reverse=True)

    async def _ai_anatomy(self, topic: str, top_viral: List, avg_viral: List) -> Dict:
        top_titles = [s["item"].title for s in top_viral]
        avg_titles = [s["item"].title for s in avg_viral]
        top_metrics = [
            f"点赞{s['item'].likes} 评论{s['item'].comments} 收藏{s['item'].collects}"
            for s in top_viral
        ]

        prompt = f"""你是爆款内容解剖专家。话题：「{topic}」

【爆款内容】（高病毒传播度）：
{chr(10).join(f'{i+1}. {t} [{m}]' for i,(t,m) in enumerate(zip(top_titles,top_metrics)))}

【普通内容】（对照组）：
{chr(10).join(f'{i+1}. {t}' for i,t in enumerate(avg_titles))}

请深度解剖爆款内容的成功密码：
1. 内容结构模板（可复用的框架）
2. 情绪触发点（引发转发/收藏的关键情绪）
3. 受众心理（满足了哪些深层需求）
4. 普通内容缺少什么
5. 可复制的爆款公式

返回JSON：
{{
  "content_formula": "一句话总结爆款公式",
  "structure_template": "内容结构模板描述",
  "emotion_triggers": ["情绪触发点1", "情绪触发点2"],
  "audience_psychology": "受众深层心理分析",
  "missing_in_average": "普通内容缺失的关键要素",
  "replication_tips": ["复制技巧1", "复制技巧2", "复制技巧3"],
  "title_formula": "爆款标题公式"
}}"""

        raw = await _chat([
            {"role": "system", "content": "你是爆款内容分析专家，只返回有效JSON。"},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=1200)

        try:
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)
        except Exception:
            return {"content_formula": "", "replication_tips": []}

    async def _persist(self, topic: str, result: Dict) -> int:
        async with AsyncSessionLocal() as db:
            report = TrendReport(
                module=self.MODULE_NAME,
                title=f"爆款解剖室 — {topic}",
                period_label="",
                platforms=list({i["platform"] for i in result.get("viral_items", [])}),
                total_items=result["total_analysed"],
                top_topics=[topic],
                trend_chart_data={
                    "viral_items": result["viral_items"],
                    "title_patterns": result["title_patterns"],
                },
                executive_summary=result.get("anatomy", {}).get("content_formula", ""),
                deep_insights=result.get("anatomy", {}).get("replication_tips", []),
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            return report.id
