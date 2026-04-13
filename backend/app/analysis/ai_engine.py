"""
AI Engine — wraps OpenAI / DeepSeek calls for deep analysis & content generation.
Both providers share the same OpenAI-compatible SDK interface.
Switch between them via AI_PROVIDER env variable.
All prompts are designed for the Chinese social media storytelling context.
"""
import json
from typing import Any, Dict, List, Optional

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


# ── Provider routing ───────────────────────────────────────────────────────────

def _active_provider() -> str:
    """Return the active provider, falling back if primary key is missing."""
    if settings.AI_PROVIDER == "deepseek":
        if settings.DEEPSEEK_API_KEY:
            return "deepseek"
        if settings.OPENAI_API_KEY:
            logger.warning("[ai_engine] DEEPSEEK_API_KEY missing — falling back to OpenAI")
            return "openai"
    else:
        if settings.OPENAI_API_KEY:
            return "openai"
        if settings.DEEPSEEK_API_KEY:
            logger.warning("[ai_engine] OPENAI_API_KEY missing — falling back to DeepSeek")
            return "deepseek"
    return "none"


def _get_client():
    """Build an AsyncOpenAI client pointed at the active provider's endpoint."""
    from openai import AsyncOpenAI

    provider = _active_provider()
    if provider == "deepseek":
        return AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )


def _active_model() -> str:
    provider = _active_provider()
    if provider == "deepseek":
        return settings.DEEPSEEK_MODEL
    return settings.OPENAI_MODEL


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _chat(messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
    provider = _active_provider()
    if provider == "none":
        logger.warning("[ai_engine] No AI API key configured — returning placeholder")
        return json.dumps({"error": "no_api_key", "placeholder": True})

    model = _active_model()
    logger.debug(f"[ai_engine] provider={provider} model={model}")

    client = _get_client()

    # DeepSeek-Reasoner (R1) does not support custom temperature
    kwargs: Dict[str, Any] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if not (provider == "deepseek" and "reasoner" in model):
        kwargs["temperature"] = temperature

    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


# ── Item-level analysis ────────────────────────────────────────────────────────

async def analyse_item(title: str, content: str, platform: str) -> Dict[str, Any]:
    """Produce structured insights for a single trend item."""
    prompt = f"""你是一位专业的社交媒体数据分析师，专注于中国互联网趋势洞察。

请分析以下来自 {platform} 的内容，并以 JSON 格式返回结构化分析结果：

标题: {title}
内容: {content[:500]}

返回格式（严格JSON）：
{{
  "summary": "一句话概括核心主题",
  "key_insights": ["洞察1", "洞察2", "洞察3"],
  "target_audience": "目标受众描述",
  "emotion_tags": ["情绪标签1", "情绪标签2"],
  "topic_clusters": ["话题聚类1", "话题聚类2"],
  "why_trending": "为什么这个内容正在流行",
  "content_angle": "创作者采用的内容角度"
}}"""

    raw = await _chat([
        {"role": "system", "content": "你是内容趋势分析专家，只返回有效JSON，不加任何额外文字。"},
        {"role": "user", "content": prompt},
    ], temperature=0.3, max_tokens=800)

    try:
        # Strip markdown code fences if present
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": title, "key_insights": [], "target_audience": "", "error": "parse_failed"}


# ── Report-level analysis ──────────────────────────────────────────────────────

async def generate_report_narrative(
    module: str,
    period_label: str,
    top_topics: List[str],
    engagement_stats: Dict,
    platform_breakdown: Dict,
) -> Dict[str, Any]:
    """Generate executive summary and deep insights for a full report."""
    prompt = f"""你是「数据故事」专栏的首席分析师。

模块：{module}
周期：{period_label}
热门话题 TOP：{', '.join(top_topics[:10])}
互动数据摘要：{json.dumps(engagement_stats, ensure_ascii=False)}
平台分布：{json.dumps(platform_breakdown, ensure_ascii=False)}

请生成：
1. 执行摘要（200字内，适合作为文章导语）
2. 3-5个深度洞察（每个洞察50-80字）
3. 对内容创作者的3条建议

返回严格JSON格式：
{{
  "executive_summary": "...",
  "deep_insights": [
    {{"title": "洞察标题", "body": "洞察内容", "implication": "对创作者的启示"}}
  ],
  "creator_tips": ["建议1", "建议2", "建议3"]
}}"""

    raw = await _chat([
        {"role": "system", "content": "你是专业的趋势报告撰写人，只返回有效JSON。"},
        {"role": "user", "content": prompt},
    ], temperature=0.5, max_tokens=1500)

    try:
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"executive_summary": "", "deep_insights": [], "creator_tips": []}


# ── Content generation ─────────────────────────────────────────────────────────

async def generate_xhs_post(
    topic: str,
    key_insights: List[str],
    module: str,
    extra_context: str = "",
) -> Dict[str, str]:
    """Generate a Xiaohongshu-style post (图文+emoji风格)."""
    insights_text = "\n".join(f"- {i}" for i in key_insights[:5])
    prompt = f"""你是爆款小红书博主「数据侦探」，擅长用数据讲有趣的社会/商业故事。

主题：{topic}
模块：{module}
核心洞察：
{insights_text}
{f'补充背景：{extra_context}' if extra_context else ''}

请创作一篇小红书笔记，要求：
- 标题：吸引眼球，含数字或悬念，加emoji（15-25字）
- 正文：800-1200字，分段清晰，每段加emoji，口语化但有深度
- 结尾：互动提问，引导评论
- hashtags：5-8个精准标签（不含#号）
- 封面图提示：描述一张适合做封面的图片（用于AI生图）

返回JSON：
{{
  "title": "...",
  "body": "...",
  "hashtags": ["...", "..."],
  "cover_prompt": "..."
}}"""

    raw = await _chat([
        {"role": "system", "content": "你是小红书爆款内容创作专家，只返回有效JSON。"},
        {"role": "user", "content": prompt},
    ], temperature=0.8, max_tokens=2000)

    try:
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": topic, "body": raw, "hashtags": [], "cover_prompt": ""}


async def generate_wechat_article(
    topic: str,
    key_insights: List[str],
    module: str,
    trend_data: Optional[Dict] = None,
    extra_context: str = "",
) -> Dict[str, str]:
    """Generate a WeChat public account deep-dive article."""
    insights_text = "\n".join(f"• {i}" for i in key_insights[:7])
    data_context = json.dumps(trend_data, ensure_ascii=False) if trend_data else ""
    prompt = f"""你是公众号「趋势见闻」的主笔，专注深度商业/社会数据分析。

主题：{topic}
模块：{module}
核心洞察：
{insights_text}
{f'数据摘要：{data_context[:500]}' if data_context else ''}
{f'补充背景：{extra_context}' if extra_context else ''}

请撰写一篇微信公众号深度文章：
- 标题：权威感，含核心数字，15-30字
- 副标题：补充说明，20字内
- 正文：2500-3500字，结构为：引言→数据画像→深度分析→商业洞察→结语
- 每个章节有小标题
- 适当加入数据表格描述（Markdown格式）

返回JSON：
{{
  "title": "...",
  "subtitle": "...",
  "body": "...",
  "hashtags": ["..."]
}}"""

    raw = await _chat([
        {"role": "system", "content": "你是专业的公众号深度内容作者，只返回有效JSON。"},
        {"role": "user", "content": prompt},
    ], temperature=0.6, max_tokens=4000)

    try:
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": topic, "subtitle": "", "body": raw, "hashtags": []}
