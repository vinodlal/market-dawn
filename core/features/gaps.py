"""Unfilled price gaps (act as dynamic support/resistance until filled).

Ported from v1 scripts/analysis_engine.py:unfilled_gaps, generalized to the
standardized OHLCV DataFrame.
"""
from __future__ import annotations

import pandas as pd

GAP_THRESHOLD_PCT = 0.3


def unfilled_gaps(df: pd.DataFrame, threshold_pct: float = GAP_THRESHOLD_PCT) -> list[dict]:
    rows = df.to_dict("records")
    gaps = []
    for t in range(1, len(rows)):
        prev_close = rows[t - 1]["close"]
        gap = rows[t]["open"] - prev_close
        if prev_close <= 0 or abs(gap) / prev_close * 100 <= threshold_pct:
            continue
        level = prev_close
        direction = "up" if gap > 0 else "down"
        filled = any(r["low"] <= level <= r["high"] for r in rows[t + 1:])
        if not filled:
            gaps.append({
                "date": str(rows[t]["ts"]), "level": level, "direction": direction,
                "gap_pct": round(gap / prev_close * 100, 3),
            })
    return gaps
