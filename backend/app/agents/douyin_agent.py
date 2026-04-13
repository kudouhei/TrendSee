"""
Douyin Agent — scrapes the public hot-list (热榜) and keyword search.
Uses Playwright to handle JS rendering and intercepts XHR calls.
Falls back to mock data in dev mode.
"""
import asyncio
import hashlib
from datetime import datetime
from typing import List

from loguru import logger

from app.agents.base import BaseAgent, RawItem

DOUYIN_HOTLIST_URL = "https://www.douyin.com/hot"
DOUYIN_SEARCH_URL  = "https://www.douyin.com/search/{keyword}?type=video"


class DouyinAgent(BaseAgent):
    name = "douyin"

    async def fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        cookie: str = kwargs.get("douyin_cookie", "")
        return await self._scrape(keyword, limit, cookie)

    async def _scrape(self, keyword: str, limit: int, cookie: str) -> List[RawItem]:
        items: List[RawItem] = []
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                        "Version/17.0 Mobile/15E148 Safari/604.1"
                    ),
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                    viewport={"width": 390, "height": 844},
                )
                if cookie:
                    for part in cookie.split(";"):
                        part = part.strip()
                        if "=" in part:
                            name, value = part.split("=", 1)
                            await ctx.add_cookies([{
                                "name": name.strip(), "value": value.strip(),
                                "domain": ".douyin.com", "path": "/"
                            }])

                captured: List[dict] = []

                async def on_resp(resp):
                    if "aweme/v1/hot/search/list" in resp.url or \
                       "aweme/v2/hot/search/list" in resp.url or \
                       "search/item/list" in resp.url:
                        try:
                            data = await resp.json()
                            captured.append(data)
                        except Exception:
                            pass

                page = await ctx.new_page()
                page.on("response", on_resp)

                url = DOUYIN_SEARCH_URL.format(keyword=keyword) if keyword else DOUYIN_HOTLIST_URL
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(4)

                # Parse intercepted API responses
                for body in captured:
                    items.extend(self._parse_api(body))

                # Fallback: DOM parse
                if not items:
                    items = await self._parse_dom(page, keyword)

                await browser.close()
        except Exception as e:
            logger.error(f"[douyin] scrape error: {e}")
            items = self._mock_items(keyword, limit)

        return items[:limit]

    def _parse_api(self, body: dict) -> List[RawItem]:
        items = []
        word_list = (
            body.get("data", {}).get("word_list") or
            body.get("hot_list") or
            []
        )
        for rank, entry in enumerate(word_list):
            label = entry.get("word") or entry.get("sentence") or entry.get("desc") or ""
            hot_value = entry.get("hot_value") or entry.get("score") or (100 - rank)
            items.append(RawItem(
                platform="douyin",
                external_id=f"hotlist_{rank}_{hashlib.md5(label.encode()).hexdigest()[:8]}",
                title=label,
                content="",
                likes=int(hot_value) if isinstance(hot_value, (int, float)) else 0,
                tags=["热榜", f"rank_{rank+1}"],
                extra={"rank": rank + 1, "hot_value": hot_value},
                published_at=datetime.utcnow(),
            ))
        return items

    async def _parse_dom(self, page, keyword: str) -> List[RawItem]:
        items = []
        try:
            rows = await page.query_selector_all(".hot-list-item, .search-card-item")
            for i, row in enumerate(rows):
                title_el = await row.query_selector(".title, .content-title")
                title = (await title_el.inner_text()).strip() if title_el else f"热榜 #{i+1}"
                items.append(RawItem(
                    platform="douyin",
                    external_id=f"dom_{hashlib.md5(title.encode()).hexdigest()[:12]}",
                    title=title,
                    likes=100 - i,
                    tags=["热榜"],
                    extra={"rank": i + 1},
                    published_at=datetime.utcnow(),
                ))
        except Exception as e:
            logger.warning(f"[douyin] DOM parse error: {e}")
        return items

    def _mock_items(self, keyword: str, limit: int) -> List[RawItem]:
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
                title=t if not keyword else f"{keyword} · {t}",
                content="",
                likes=10000000 - i * 500000,
                tags=["热榜", f"rank_{i+1}"],
                extra={"rank": i + 1, "is_mock": True},
                published_at=datetime.utcnow(),
            )
            for i, t in enumerate(topics[:limit])
        ]
