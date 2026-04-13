"""
Trend lifecycle detector — classifies a topic into rising / peak / declining / stable
using time-series engagement data and statistical heuristics.
"""
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class LifecycleResult:
    phase: str          # rising | peak | declining | stable | unknown
    confidence: float   # 0–1
    velocity: float     # rate of change (positive = growing)
    momentum: float     # acceleration (positive = accelerating)


def detect_lifecycle(scores: List[Tuple[float, float]]) -> LifecycleResult:
    """
    scores: list of (timestamp_numeric, engagement_score) sorted by time.
    Needs at least 3 data points for meaningful classification.
    """
    if len(scores) < 2:
        return LifecycleResult("unknown", 0.0, 0.0, 0.0)

    times  = np.array([s[0] for s in scores], dtype=float)
    values = np.array([s[1] for s in scores], dtype=float)

    # Normalise time to [0, 1]
    t_range = times[-1] - times[0]
    if t_range > 0:
        t_norm = (times - times[0]) / t_range
    else:
        t_norm = np.linspace(0, 1, len(times))

    # Linear trend
    coeffs = np.polyfit(t_norm, values, 1) if len(scores) >= 3 else np.array([0.0, values.mean()])
    velocity = float(coeffs[0])  # slope

    # Acceleration (second-order fit)
    if len(scores) >= 4:
        c2 = np.polyfit(t_norm, values, 2)
        momentum = float(c2[0])
    else:
        momentum = 0.0

    # Peak detection: is the max near the middle/end?
    peak_idx = int(np.argmax(values))
    peak_position = peak_idx / max(len(values) - 1, 1)   # 0 = start, 1 = end

    recent_mean = float(values[-max(2, len(values)//4):].mean())
    overall_mean = float(values.mean())
    peak_value   = float(values.max())
    trough_value = float(values.min())
    spread = peak_value - trough_value

    # Classification rules
    if spread < 2.0:
        phase = "stable"
        confidence = 0.7
    elif velocity > 5 and momentum >= 0:
        phase = "rising"
        confidence = min(0.95, 0.6 + abs(velocity) / 50)
    elif velocity > 5 and momentum < 0:
        # Slowing growth — near peak
        phase = "peak"
        confidence = 0.65
    elif peak_position > 0.6 and recent_mean < overall_mean * 0.8:
        phase = "declining"
        confidence = min(0.90, 0.5 + abs(velocity) / 50)
    elif velocity < -5:
        phase = "declining"
        confidence = min(0.90, 0.5 + abs(velocity) / 50)
    else:
        phase = "stable"
        confidence = 0.5

    return LifecycleResult(
        phase=phase,
        confidence=round(confidence, 3),
        velocity=round(velocity, 3),
        momentum=round(momentum, 3),
    )


def classify_single_item(virality_score: float, days_old: int = 0) -> LifecycleResult:
    """
    Quick heuristic for a single data point (no time series).
    Uses virality score + age as proxy.
    """
    if virality_score >= 70:
        phase = "peak" if days_old <= 2 else "declining"
    elif virality_score >= 40:
        phase = "rising" if days_old <= 5 else "stable"
    elif virality_score >= 15:
        phase = "stable"
    else:
        phase = "declining"

    return LifecycleResult(phase=phase, confidence=0.5, velocity=0.0, momentum=0.0)
