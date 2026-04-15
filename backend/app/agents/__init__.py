from app.agents.reddit_agent import RedditAgent
from app.agents.google_trends_agent import GoogleTrendsAgent
from app.agents.xhs_agent import XHSAgent
from app.agents.douyin_agent import DouyinAgent

AGENT_REGISTRY = {
    "reddit": RedditAgent,
    "google_trends": GoogleTrendsAgent,
    "xhs": XHSAgent,
    "douyin": DouyinAgent,
}


def default_agent_kwargs() -> dict:
    """Return platform-level kwargs populated from environment / .env config.

    Each module should merge these into the kwargs it passes to safe_fetch so
    that cookies are automatically available without having to thread them
    through every API call.
    """
    from app.core.config import settings
    kwargs: dict = {}
    if settings.XHS_COOKIE:
        kwargs["xhs_cookie"] = settings.XHS_COOKIE
    if settings.DOUYIN_COOKIE:
        kwargs["douyin_cookie"] = settings.DOUYIN_COOKIE
    return kwargs


__all__ = [
    "RedditAgent", "GoogleTrendsAgent", "XHSAgent", "DouyinAgent",
    "AGENT_REGISTRY", "default_agent_kwargs",
]
