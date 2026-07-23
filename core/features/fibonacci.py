"""Fibonacci retracement / extension levels off an active swing."""
from __future__ import annotations

RETRACEMENT_RATIOS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
EXTENSION_RATIOS = (1.272, 1.618, 2.0, 2.618)


def retracement_levels(swing_low: float, swing_high: float) -> dict[float, float]:
    """Levels between low and high (an uptrend swing). For a downtrend swing,
    call with swing_low/swing_high still meaning the range's low/high — ratio 0
    always maps to the high (retracement start), ratio 1 to the low."""
    span = swing_high - swing_low
    return {r: round(swing_high - r * span, 2) for r in RETRACEMENT_RATIOS}


def extension_levels(swing_low: float, swing_high: float, direction: str = "up") -> dict[float, float]:
    span = swing_high - swing_low
    if direction == "up":
        return {r: round(swing_high + (r - 1.0) * span, 2) for r in EXTENSION_RATIOS}
    return {r: round(swing_low - (r - 1.0) * span, 2) for r in EXTENSION_RATIOS}
