"""
Base agent interface that every platform agent must implement.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from loguru import logger


@dataclass
class RawItem:
    platform: str
    external_id: str
    title: str
    content: str = ""
    author: str = ""
    url: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collects: int = 0
    views: int = 0
    tags: List[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    published_at: Optional[datetime] = None


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        """Fetch raw items. Keyword can be empty for hot-list agents."""

    async def safe_fetch(self, keyword: str = "", limit: int = 50, **kwargs) -> List[RawItem]:
        try:
            items = await self.fetch(keyword=keyword, limit=limit, **kwargs)
            logger.info(f"[{self.name}] fetched {len(items)} items for '{keyword}'")
            return items
        except Exception as exc:
            logger.error(f"[{self.name}] fetch failed: {exc}")
            return []
