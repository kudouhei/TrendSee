"""
Engagement scoring — normalises raw platform metrics into a unified 0–100 score.
Also computes a virality potential index.
"""
import math
from dataclasses import dataclass


# Platform-specific median benchmarks (rough estimates for normalisation)
_PLATFORM_BENCHMARKS = {
    "xhs":           {"likes": 500,  "comments": 50,  "collects": 200, "shares": 20,  "views": 5000},
    "douyin":        {"likes": 5000, "comments": 200, "collects": 0,   "shares": 500, "views": 50000},
    "reddit":        {"likes": 100,  "comments": 20,  "collects": 0,   "shares": 0,   "views": 1000},
    "google_trends": {"likes": 50,   "comments": 0,   "collects": 0,   "shares": 0,   "views": 0},
}

# Weight of each metric in the engagement score
_WEIGHTS = {"likes": 0.35, "comments": 0.30, "collects": 0.25, "shares": 0.10}


@dataclass
class EngagementResult:
    engagement_score: float   # 0–100
    virality_score: float     # 0–100
    breakdown: dict           # per-metric normalised scores


def _log_normalise(value: int, benchmark: int) -> float:
    """Map raw metric to 0–100 using log scaling against a platform benchmark."""
    if value <= 0:
        return 0.0
    ratio = value / max(benchmark, 1)
    return min(100.0, 50.0 * math.log1p(ratio) / math.log1p(1))


def score_engagement(
    platform: str,
    likes: int = 0,
    comments: int = 0,
    collects: int = 0,
    shares: int = 0,
    views: int = 0,
) -> EngagementResult:
    bench = _PLATFORM_BENCHMARKS.get(platform, _PLATFORM_BENCHMARKS["reddit"])

    scores = {
        "likes":    _log_normalise(likes,    bench["likes"]),
        "comments": _log_normalise(comments, bench["comments"]),
        "collects": _log_normalise(collects, bench["collects"]),
        "shares":   _log_normalise(shares,   bench["shares"]),
    }

    engagement = sum(scores[k] * _WEIGHTS[k] for k in scores)

    # Virality = amplified when shares/comments are disproportionately high
    comment_ratio = scores["comments"] / max(scores["likes"], 1)
    share_ratio   = scores["shares"]   / max(scores["likes"], 1)
    virality = min(100.0, engagement * (1 + 0.3 * comment_ratio + 0.4 * share_ratio))

    return EngagementResult(
        engagement_score=round(engagement, 2),
        virality_score=round(virality, 2),
        breakdown={k: round(v, 2) for k, v in scores.items()},
    )
