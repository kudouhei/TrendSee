"""
Google Trends Agent — uses pytrends to get search interest over time,
related queries and real-time trending topics.
"""
import asyncio
from datetime import datetime
from typing import List

from loguru import logger

from app.agents.base import BaseAgent, RawItem


class GoogleTrendsAgent(BaseAgent):
    name = "google_trends"

    async def fetch(self, keyword: str = "", limit: int = 20, **kwargs) -> List[RawItem]:
        geo: str = kwargs.get("geo", "")         # "" = worldwide, "CN", "US", etc.
        timeframe: str = kwargs.get("timeframe", "now 7-d")

        return await asyncio.get_event_loop().run_in_executor(
            None, self._fetch_sync, keyword, limit, geo, timeframe
        )

    def _fetch_sync(self, keyword: str, limit: int, geo: str, timeframe: str) -> List[RawItem]:
        # pytrends uses urllib3 Retry with the deprecated `method_whitelist` kwarg
        # (removed in urllib3 >= 2.0, renamed to `allowed_methods`). Patch it before import.
        import urllib3.util.retry as _retry_mod
        _orig_retry_init = _retry_mod.Retry.__init__
        def _compat_retry_init(self, *args, **kwargs):
            if "method_whitelist" in kwargs:
                kwargs["allowed_methods"] = kwargs.pop("method_whitelist")
            _orig_retry_init(self, *args, **kwargs)
        _retry_mod.Retry.__init__ = _compat_retry_init

        from pytrends.request import TrendReq
        items: List[RawItem] = []

        try:
            pt = TrendReq(hl="zh-CN", tz=480, timeout=(10, 30), retries=2, backoff_factor=0.5)

            # ── 无关键词：直接抓实时热搜榜 ──────────────────────────────────
            if not keyword:
                pn = "china" if geo == "CN" else "united_states"
                trending = pt.trending_searches(pn=pn)
                for i, row in trending.iterrows():
                    topic = str(row.iloc[0]) if hasattr(row, "iloc") else str(row)
                    items.append(RawItem(
                        platform="google_trends",
                        external_id=f"trending_{geo}_{i}",
                        title=topic,
                        content="",
                        likes=limit - i,
                        tags=["trending", geo or "global"],
                        extra={"type": "trending", "rank": i, "geo": geo},
                        published_at=datetime.utcnow(),
                    ))
                return items[:limit]

            # ── 有关键词：抓 related queries（真正的趋势信号）────────────────
            pt.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)

            # 1. 计算整体热度（interest over time 的均值），作为一条摘要条目
            iot = pt.interest_over_time()
            avg_score = 0
            if not iot.empty and keyword in iot.columns:
                avg_score = int(iot[keyword].mean())
                # 取近期最高点作为趋势信号
                peak_score = int(iot[keyword].max())
                items.append(RawItem(
                    platform="google_trends",
                    external_id=f"iot_summary_{keyword}",
                    title=f"{keyword}（搜索热度趋势）",
                    content=f"近期搜索热度均值 {avg_score}，峰值 {peak_score}（满分100）",
                    likes=peak_score,
                    tags=[keyword, "interest_over_time"],
                    extra={"type": "interest_summary", "avg_score": avg_score,
                           "peak_score": peak_score, "timeframe": timeframe},
                    published_at=datetime.utcnow(),
                ))

            # 2. Rising queries — 最具价值：近期搜索量暴涨的相关词
            # 3. Top queries — 搜索量最大的相关词
            related = pt.related_queries()
            if keyword in related:
                rising_df = related[keyword].get("rising")
                top_df    = related[keyword].get("top")

                # rising 优先，最多取 (limit-1) // 2 条
                half = max(1, (limit - 1) // 2)
                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.head(half).iterrows():
                        q   = str(row.get("query", ""))
                        val = row.get("value", 0)
                        # val 可能是 "Breakout"（爆发式增长）或具体百分比数字
                        is_breakout = isinstance(val, str) and "breakout" in val.lower()
                        score = 200 if is_breakout else int(val) if isinstance(val, (int, float)) else 100
                        items.append(RawItem(
                            platform="google_trends",
                            external_id=f"rising_{keyword}_{q}",
                            title=q,
                            content=f"与「{keyword}」相关的上升搜索词，增幅 {'爆发式增长' if is_breakout else f'+{val}%'}",
                            likes=score,
                            tags=[keyword, "rising_query"],
                            extra={"type": "rising_query", "parent_keyword": keyword,
                                   "value": val, "is_breakout": is_breakout},
                            published_at=datetime.utcnow(),
                        ))

                if top_df is not None and not top_df.empty:
                    for _, row in top_df.head(half).iterrows():
                        q   = str(row.get("query", ""))
                        val = row.get("value", 0)
                        items.append(RawItem(
                            platform="google_trends",
                            external_id=f"top_{keyword}_{q}",
                            title=q,
                            content=f"与「{keyword}」相关的热门搜索词，热度 {val}",
                            likes=int(val) if isinstance(val, (int, float)) else 50,
                            tags=[keyword, "top_query"],
                            extra={"type": "top_query", "parent_keyword": keyword, "value": val},
                            published_at=datetime.utcnow(),
                        ))

        except Exception as e:
            logger.error(f"[google_trends] error: {e}")

        return items[:limit]
