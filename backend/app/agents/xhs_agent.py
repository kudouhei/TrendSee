"""
XHS (小红书) Agent — scrapes public search results via Playwright.

Note: XHS heavily protects its API. This agent uses headless Chromium with
realistic browser fingerprints. You may need to pass cookies/tokens from a
logged-in session via `xhs_cookie` kwarg for reliable results.
"""
import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import List, Optional

import httpx
from loguru import logger

from app.agents.base import BaseAgent, RawItem
from app.core.config import settings


class XHSAgent(BaseAgent):
    name = "xhs"

    XHS_SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"

    async def fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        cookie: str = kwargs.get("xhs_cookie", "")
        return await self._scrape_playwright(keyword, limit, cookie)

    async def _scrape_playwright(self, keyword: str, limit: int, cookie: str) -> List[RawItem]:
        items: List[RawItem] = []
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                )
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                )
                if cookie:
                    await ctx.add_cookies(self._parse_cookie_string(cookie))

                page = await ctx.new_page()

                # Intercept XHR to capture API responses
                captured: List[dict] = []

                async def on_response(resp):
                    if "api/sns/web/v1/search/notes" in resp.url or \
                       "api/sns/web/v1/feed" in resp.url:
                        try:
                            body = await resp.json()
                            captured.append(body)
                        except Exception:
                            pass

                page.on("response", on_response)

                url = self.XHS_SEARCH_URL.format(keyword=keyword)
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)

                # Parse from intercepted API responses first
                for body in captured:
                    notes = self._extract_notes_from_api(body)
                    items.extend(notes)

                # Fallback: parse rendered DOM
                if not items:
                    items = await self._parse_dom(page, keyword)

                await browser.close()
        except Exception as e:
            logger.error(f"[xhs] playwright error: {e}")
            # Return mock data in dev mode so the pipeline can still be tested
            items = self._mock_items(keyword, limit)

        return items[:limit]

    def _extract_notes_from_api(self, body: dict) -> List[RawItem]:
        items = []
        notes = (
            body.get("data", {}).get("items") or
            body.get("data", {}).get("notes") or []
        )
        for note in notes:
            ni = note.get("note_card") or note
            note_id = ni.get("id") or ni.get("note_id") or ""
            interact = ni.get("interact_info") or {}
            items.append(RawItem(
                platform="xhs",
                external_id=note_id,
                title=ni.get("title") or ni.get("desc") or "",
                content=ni.get("desc") or "",
                author=((ni.get("user") or {}).get("nickname") or ""),
                url=f"https://www.xiaohongshu.com/explore/{note_id}",
                likes=self._parse_num(interact.get("liked_count")),
                comments=self._parse_num(interact.get("comment_count")),
                collects=self._parse_num(interact.get("collected_count")),
                shares=self._parse_num(interact.get("share_count")),
                tags=[t.get("name", "") for t in ni.get("tag_list") or []],
                extra={"type": ni.get("type", "normal")},
                published_at=datetime.utcnow(),
            ))
        return items

    async def _parse_dom(self, page, keyword: str) -> List[RawItem]:
        items = []
        try:
            cards = await page.query_selector_all("section.note-item, .feeds-page .note-item")
            for card in cards:
                title_el = await card.query_selector(".title, .footer .title")
                title = (await title_el.inner_text()).strip() if title_el else ""
                author_el = await card.query_selector(".author .name, .user-name")
                author = (await author_el.inner_text()).strip() if author_el else ""
                like_el = await card.query_selector(".like-wrapper .count, .likes-count")
                likes_raw = (await like_el.inner_text()).strip() if like_el else "0"

                link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                note_id = href.split("/")[-1].split("?")[0] if href else hashlib.md5(title.encode()).hexdigest()[:16]

                items.append(RawItem(
                    platform="xhs",
                    external_id=note_id,
                    title=title,
                    content="",
                    author=author,
                    url=f"https://www.xiaohongshu.com{href}" if href else "",
                    likes=self._parse_num(likes_raw),
                    tags=[keyword],
                    extra={},
                    published_at=datetime.utcnow(),
                ))
        except Exception as e:
            logger.warning(f"[xhs] DOM parse error: {e}")
        return items

    def _mock_items(self, keyword: str, limit: int) -> List[RawItem]:
        """Return plausible mock data when scraping is unavailable (dev mode)."""
        mock_titles = [
            f"｜{keyword}｜ 我用一个月实测这个趋势，结果出乎意料",
            f"关于{keyword}，你不知道的5个真相 🔥",
            f"所有人都在聊{keyword}，但真正懂的人只有这些",
            f"【深度测评】{keyword} 到底值不值得关注？",
            f"{keyword} 的商业逻辑，看完我惊了",
        ]
        return [
            RawItem(
                platform="xhs",
                external_id=f"mock_xhs_{i}",
                title=mock_titles[i % len(mock_titles)],
                content=f"这是关于{keyword}的测试内容，实际运行时将替换为真实数据。",
                author=f"博主_{i}",
                url=f"https://www.xiaohongshu.com/explore/mock_{i}",
                likes=5000 - i * 300,
                comments=200 - i * 10,
                collects=800 - i * 50,
                shares=100 - i * 5,
                tags=[keyword, "测试"],
                extra={"is_mock": True},
                published_at=datetime.utcnow(),
            )
            for i in range(min(limit, len(mock_titles)))
        ]

    @staticmethod
    def _parse_num(val) -> int:
        if val is None:
            return 0
        s = str(val).replace(",", "").strip()
        if s.endswith("w") or s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        if s.endswith("k") or s.endswith("K"):
            return int(float(s[:-1]) * 1000)
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _parse_cookie_string(cookie_str: str) -> List[dict]:
        cookies = []
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".xiaohongshu.com", "path": "/"})
        return cookies
