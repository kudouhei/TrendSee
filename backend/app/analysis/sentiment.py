"""
Sentiment analysis — bilingual (Chinese + English).
Uses VADER for English, jieba + lexicon heuristics for Chinese,
with an optional GPT fallback for nuanced cases.
"""
import re
from dataclasses import dataclass
from typing import Tuple

import jieba
from loguru import logger


# Simple Chinese sentiment lexicon (extend as needed)
_POS_WORDS = {
    "好", "棒", "厉害", "赞", "优秀", "喜欢", "爱", "完美", "惊喜", "期待",
    "值得", "推荐", "牛", "绝", "超赞", "心动", "正品", "满意", "好用", "有趣",
}
_NEG_WORDS = {
    "差", "烂", "坑", "骗", "假", "贵", "失望", "后悔", "难用", "垃圾",
    "不好", "不行", "问题", "失误", "差评", "退货", "浪费", "骗局", "虚假",
}
_INTENSIFIERS = {"非常", "超", "极其", "太", "很", "特别", "巨"}
_NEGATORS = {"不", "没", "别", "莫", "未", "非"}


@dataclass
class SentimentResult:
    score: float        # -1.0 to 1.0
    label: str          # positive | negative | neutral
    confidence: float   # 0 to 1
    method: str         # vader | zh_lexicon | gpt


def _zh_sentiment(text: str) -> Tuple[float, float]:
    """Rule-based Chinese sentiment. Returns (score, confidence)."""
    words = list(jieba.cut(text))
    pos = neg = total = 0
    i = 0
    while i < len(words):
        w = words[i]
        if w in _POS_WORDS:
            multiplier = 2.0 if (i > 0 and words[i-1] in _INTENSIFIERS) else 1.0
            if i > 0 and words[i-1] in _NEGATORS:
                neg += multiplier
            else:
                pos += multiplier
            total += multiplier
        elif w in _NEG_WORDS:
            multiplier = 2.0 if (i > 0 and words[i-1] in _INTENSIFIERS) else 1.0
            if i > 0 and words[i-1] in _NEGATORS:
                pos += multiplier
            else:
                neg += multiplier
            total += multiplier
        i += 1

    if total == 0:
        return 0.0, 0.3
    score = (pos - neg) / total
    confidence = min(0.9, 0.4 + total * 0.05)
    return score, confidence


def _en_sentiment(text: str) -> Tuple[float, float]:
    """VADER sentiment for English text."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        confidence = 0.5 + abs(compound) * 0.4
        return compound, confidence
    except Exception as e:
        logger.warning(f"VADER error: {e}")
        return 0.0, 0.3


def _is_chinese(text: str) -> bool:
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return chinese_chars / max(len(text), 1) > 0.2


def analyze_sentiment(text: str) -> SentimentResult:
    if not text or not text.strip():
        return SentimentResult(0.0, "neutral", 0.0, "none")

    if _is_chinese(text):
        score, conf = _zh_sentiment(text)
        method = "zh_lexicon"
    else:
        score, conf = _en_sentiment(text)
        method = "vader"

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(score=round(score, 4), label=label, confidence=round(conf, 4), method=method)
