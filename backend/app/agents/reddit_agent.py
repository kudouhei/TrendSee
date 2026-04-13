"""
Reddit Agent — uses PRAW to pull hot/rising posts from relevant subreddits.
Falls back to public JSON API when credentials are absent.
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from loguru import logger

from app.agents.base import BaseAgent, RawItem
from app.core.config import settings

# Default subreddits to monitor for trend signals
DEFAULT_SUBREDDITS = [
    "technology", "business", "marketing", "socialmedia",
    "dataisbeautiful", "china", "investing", "artificial",
]


class RedditAgent(BaseAgent):
    name = "reddit"

    def __init__(self):
        self._praw = None
        self._init_praw()

    def _init_praw(self):
        if not settings.REDDIT_CLIENT_ID:
            logger.warning("[reddit] No credentials — will use public JSON API")
            return
        try:
            import praw
            self._praw = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
        except Exception as e:
            logger.warning(f"[reddit] PRAW init failed: {e}")

    async def fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        subreddits: List[str] = kwargs.get("subreddits", DEFAULT_SUBREDDITS)
        sort: str = kwargs.get("sort", "hot")   # hot | rising | top

        if self._praw:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_praw, subreddits, keyword, limit, sort
            )
        return await self._fetch_public(subreddits, keyword, limit, sort)

    # ── PRAW (authenticated) ──────────────────────────────────────────────────
    def _fetch_praw(self, subreddits, keyword, limit, sort) -> List[RawItem]:
        items = []
        for sub_name in subreddits:
            try:
                sub = self._praw.subreddit(sub_name)
                if keyword:
                    posts = sub.search(keyword, sort=sort, limit=limit)
                else:
                    posts = getattr(sub, sort)(limit=limit)

                for post in posts:
                    items.append(RawItem(
                        platform="reddit",
                        external_id=post.id,
                        title=post.title,
                        content=post.selftext[:2000] if post.selftext else "",
                        author=str(post.author) if post.author else "",
                        url=f"https://reddit.com{post.permalink}",
                        likes=post.score,
                        comments=post.num_comments,
                        shares=0,
                        collects=0,
                        views=getattr(post, "view_count", 0) or 0,
                        tags=[sub_name, post.link_flair_text or ""],
                        extra={"subreddit": sub_name, "upvote_ratio": post.upvote_ratio},
                        published_at=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                    ))
            except Exception as e:
                logger.error(f"[reddit] subreddit={sub_name} error: {e}")
        return items

    # ── Public JSON API (no credentials) ────────────────────────────────────
    async def _fetch_public(self, subreddits, keyword, limit, sort) -> List[RawItem]:
        items = []
        headers = {"User-Agent": settings.REDDIT_USER_AGENT}
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            for sub_name in subreddits[:3]:  # rate-limit friendly
                try:
                    url = f"https://www.reddit.com/r/{sub_name}/{sort}.json?limit={min(limit,25)}"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    for child in resp.json()["data"]["children"]:
                        d = child["data"]
                        if keyword and keyword.lower() not in (d.get("title","") + d.get("selftext","")).lower():
                            continue
                        items.append(RawItem(
                            platform="reddit",
                            external_id=d["id"],
                            title=d["title"],
                            content=(d.get("selftext") or "")[:2000],
                            author=d.get("author", ""),
                            url=f"https://reddit.com{d['permalink']}",
                            likes=d.get("score", 0),
                            comments=d.get("num_comments", 0),
                            shares=0,
                            collects=0,
                            views=d.get("view_count") or 0,
                            tags=[sub_name],
                            extra={"subreddit": sub_name},
                            published_at=datetime.fromtimestamp(d["created_utc"], tz=timezone.utc),
                        ))
                except Exception as e:
                    logger.error(f"[reddit] public API sub={sub_name}: {e}")
        return items
