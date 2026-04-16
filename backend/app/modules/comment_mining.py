"""
Module 2: 评论区挖矿 (Comment Mining)
Digs into comment sections to surface hidden opinions,
user emotions, and emerging sub-narratives.
"""
import asyncio
import json
from collections import Counter
from typing import Dict, List

import jieba
from loguru import logger

from app.agents import AGENT_REGISTRY, default_agent_kwargs
from app.analysis.sentiment import analyze_sentiment
from app.analysis.ai_engine import _chat
from app.core.database import AsyncSessionLocal
from app.models import TrendReport


_STOPWORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "这", "那", "啊", "哈", "哦", "嗯", "吗", "呢", "吧", "啦",
}


class CommentMiningModule:
    MODULE_NAME = "comment_mining"

    async def run(
        self,
        topic: str,
        platforms: List[str],
        limit_per_source: int = 50,
        **agent_kwargs,
    ) -> Dict:
        logger.info(f"[CommentMining] topic={topic} platforms={platforms}")

        agent_kwargs = {**default_agent_kwargs(), **agent_kwargs}

        # ── Collect posts about the topic ─────────────────────────────────────
        all_items = []
        tasks = []
        for platform in platforms:
            agent_cls = AGENT_REGISTRY.get(platform)
            if not agent_cls:
                continue
            tasks.append(agent_cls().safe_fetch(keyword=topic, limit=limit_per_source, **agent_kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)

        # ── Sentiment breakdown ───────────────────────────────────────────────
        sentiments = []
        for item in all_items:
            text = item.title + " " + item.content
            s = analyze_sentiment(text)
            sentiments.append({
                "title": item.title[:80],
                "platform": item.platform,
                "sentiment": s.label,
                "score": s.score,
                "likes": item.likes,
                "comments": item.comments,
            })

        # ── Word frequency (extract "voice of the audience") ─────────────────
        all_text = " ".join(i.title + " " + i.content for i in all_items)
        words = [w for w in jieba.cut(all_text) if len(w) >= 2 and w not in _STOPWORDS]
        word_freq = Counter(words).most_common(30)

        # ── AI deep mining ────────────────────────────────────────────────────
        sample_titles = [i.title for i in all_items[:20]]
        insights = await self._ai_mine(topic, sample_titles, sentiments)

        # ── Aggregate stats ───────────────────────────────────────────────────
        sentiment_dist = Counter(s["sentiment"] for s in sentiments)
        avg_sentiment = sum(s["score"] for s in sentiments) / max(len(sentiments), 1)

        result = {
            "module": self.MODULE_NAME,
            "topic": topic,
            "total_posts_analysed": len(all_items),
            "sentiment_distribution": dict(sentiment_dist),
            "avg_sentiment_score": round(avg_sentiment, 3),
            "top_words": [{"word": w, "count": c} for w, c in word_freq],
            "sample_sentiments": sentiments[:30],
            "ai_insights": insights,
        }

        report_id = await self._persist(topic, result)
        result["report_id"] = report_id
        return result

    async def _ai_mine(self, topic: str, titles: List[str], sentiments: List[Dict]) -> Dict:
        pos_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        neg_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        total = max(len(sentiments), 1)

        prompt = f"""你是评论区深度挖掘专家。话题：「{topic}」

采集到 {total} 条相关内容：
正面情绪：{pos_count}条 ({round(pos_count/total*100)}%)
负面情绪：{neg_count}条 ({round(neg_count/total*100)}%)

典型标题样本：
{chr(10).join(f'• {t}' for t in titles[:15])}

请深度分析：
1. 受众对这个话题的真实态度和隐藏情绪
2. 正负面情绪背后的深层原因
3. 评论区最值得关注的争议点
4. 对内容创作者的挖矿价值（哪个角度最能引发共鸣）

返回JSON：
{{
  "audience_attitude": "受众整体态度描述",
  "hidden_emotions": ["隐藏情绪1", "隐藏情绪2"],
  "controversy_points": ["争议点1", "争议点2"],
  "content_opportunities": ["创作机会1", "创作机会2", "创作机会3"],
  "recommended_angle": "最推荐的创作角度"
}}"""

        raw = await _chat([
            {"role": "system", "content": "你是社交媒体评论分析专家，只返回有效JSON。"},
            {"role": "user", "content": prompt},
        ], temperature=0.4, max_tokens=1000)

        try:
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)
        except Exception:
            return {"audience_attitude": "", "content_opportunities": []}

    async def _persist(self, topic: str, result: Dict) -> int:  # noqa: return type
        async with AsyncSessionLocal() as db:
            report = TrendReport(
                module=self.MODULE_NAME,
                title=f"评论区挖矿 — {topic}",
                period_label="",
                platforms=list({r.get("platform", "") for r in result.get("sample_sentiments", [])}),
                total_items=result["total_posts_analysed"],
                top_topics=[w["word"] for w in result["top_words"][:10]],
                trend_chart_data={
                    "sentiment_distribution": result["sentiment_distribution"],
                    "top_words": result["top_words"],
                    "sample_sentiments": result["sample_sentiments"],
                },
                executive_summary=result.get("ai_insights", {}).get("audience_attitude", ""),
                deep_insights=result.get("ai_insights", {}).get("content_opportunities", []),
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            return report.id
