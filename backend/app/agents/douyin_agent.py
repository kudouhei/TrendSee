"""
Douyin Agent — fetches the public hot-list (热榜) via the Douyin Hot Search API.
Uses httpx for direct HTTP calls. Falls back to mock data on failure.
"""
import hashlib
from datetime import datetime
from typing import List

import httpx
from loguru import logger

from app.agents.base import BaseAgent, RawItem

DOUYIN_HOT_API_URL = (
    "https://www.douyin.com/aweme/v1/hot/search/list/"
    "?count=50&source=6&detail_list=1&aid=6383&app_name=aweme_web&device_platform=webapp"
)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Referer": "https://www.douyin.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class DouyinAgent(BaseAgent):
    name = "douyin"

    async def fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        cookie: str = kwargs.get("douyin_cookie", "")
        return await self._fetch_hot(limit, cookie)

    async def _fetch_hot(self, limit: int, cookie: str) -> List[RawItem]:
        headers = {**_DEFAULT_HEADERS}
        if cookie:
            headers["Cookie"] = cookie

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(DOUYIN_HOT_API_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            items = self._parse_api(data)
            if items:
                logger.info(f"[douyin] Hot API returned {len(items)} items")
                return items[:limit]

            logger.warning("[douyin] Hot API returned empty list, falling back to mock")
        except Exception as e:
            logger.error(f"[douyin] Hot API error: {e}")

        return self._mock_items(limit)

    def _parse_api(self, body: dict) -> List[RawItem]:
        items: List[RawItem] = []
        word_list = (
            body.get("data", {}).get("word_list")
            or body.get("hot_list")
            or []
        )
        for rank, entry in enumerate(word_list):
            label = entry.get("word") or entry.get("sentence") or entry.get("desc") or ""
            hot_value = entry.get("hot_value") or entry.get("score") or (100 - rank)
            items.append(RawItem(
                platform="douyin",
                external_id=f"hot_{rank}_{hashlib.md5(label.encode()).hexdigest()[:8]}",
                title=label,
                content="",
                likes=int(hot_value) if isinstance(hot_value, (int, float)) else 0,
                tags=["热榜", f"rank_{rank + 1}"],
                extra={"rank": rank + 1, "hot_value": hot_value},
                published_at=datetime.utcnow(),
            ))
        return items

    def _mock_items(self, limit: int) -> List[RawItem]:
        topics = [
            "AI换脸技术引发热议", "春节出行高峰来临", "新能源汽车价格战升级",
            "年轻人躺平还是内卷", "国产手机出海战略", "直播带货监管趋严",
            "独生子女养老困局", "大厂裁员潮还在继续", "咖啡市场争夺白热化",
            "健康饮食新风潮",
        ]
        return [
            RawItem(
                platform="douyin",
                external_id=f"mock_dy_{i}",
                title=t,
                content="",
                likes=10000000 - i * 500000,
                tags=["热榜", f"rank_{i + 1}"],
                extra={"rank": i + 1, "is_mock": True},
                published_at=datetime.utcnow(),
            )
            for i, t in enumerate(topics[:limit])
        ]
