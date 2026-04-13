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

__all__ = ["RedditAgent", "GoogleTrendsAgent", "XHSAgent", "DouyinAgent", "AGENT_REGISTRY"]
