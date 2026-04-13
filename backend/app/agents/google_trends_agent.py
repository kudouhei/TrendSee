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
        from pytrends.request import TrendReq
        items: List[RawItem] = []

        try:
            pt = TrendReq(hl="zh-CN", tz=480, timeout=(10, 30), retries=2, backoff_factor=0.5)

            # ── Trending searches (real-time hot topics) ─────────────────────
            if not keyword:
                trending = pt.trending_searches(pn="china" if geo == "CN" else "united_states")
                for i, row in trending.iterrows():
                    topic = str(row.iloc[0]) if hasattr(row, "iloc") else str(row)
                    items.append(RawItem(
                        platform="google_trends",
                        external_id=f"trending_{geo}_{i}",
                        title=topic,
                        content="",
                        likes=limit - i,   # proxy rank as score
                        tags=["trending", geo or "global"],
                        extra={"type": "trending", "rank": i, "geo": geo},
                        published_at=datetime.utcnow(),
                    ))
                return items[:limit]

            # ── Interest over time ────────────────────────────────────────────
            pt.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            iot = pt.interest_over_time()

            if not iot.empty and keyword in iot.columns:
                for ts, row in iot.iterrows():
                    score = int(row[keyword])
                    items.append(RawItem(
                        platform="google_trends",
                        external_id=f"iot_{keyword}_{ts}",
                        title=f"{keyword} — Search Interest",
                        content="",
                        likes=score,
                        tags=[keyword, "interest_over_time"],
                        extra={"type": "interest_over_time", "score": score, "timestamp": str(ts)},
                        published_at=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.utcnow(),
                    ))

            # ── Related queries ───────────────────────────────────────────────
            related = pt.related_queries()
            if keyword in related:
                for query_type in ("top", "rising"):
                    df = related[keyword].get(query_type)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            q = row.get("query", "")
                            val = row.get("value", 0)
                            items.append(RawItem(
                                platform="google_trends",
                                external_id=f"related_{keyword}_{query_type}_{q}",
                                title=f"Related: {q}",
                                content=f"Related {query_type} query for '{keyword}'",
                                likes=int(val) if isinstance(val, (int, float)) else 0,
                                tags=[keyword, f"related_{query_type}"],
                                extra={"type": f"related_{query_type}", "parent_keyword": keyword},
                                published_at=datetime.utcnow(),
                            ))
        except Exception as e:
            logger.error(f"[google_trends] error: {e}")

        return items[:limit]
