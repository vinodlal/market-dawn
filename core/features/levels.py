"""Support/resistance: floor pivots, swing highs/lows, and level clustering.

Ported from v1 scripts/analysis_engine.py (pivot_levels, swing_points,
nearest_levels) and scripts/technical.py (cluster), generalized to work on the
standardized OHLCV DataFrame (core.providers.base.OHLCV_COLS).
"""
from __future__ import annotations

import pandas as pd


def pivot_levels(high: float, low: float, close: float) -> dict:
    p = (high + low + close) / 3.0
    r1, s1 = 2 * p - low, 2 * p - high
    r2, s2 = p + (high - low), p - (high - low)
    return {"pivot": p, "r1": r1, "r2": r2, "s1": s1, "s2": s2}


def swing_points(df: pd.DataFrame, window: int = 3) -> tuple[list[float], list[float]]:
    """Local swing highs/lows over a +-window session lookback."""
    highs, lows = df["high"].tolist(), df["low"].tolist()
    n = len(df)
    sh, sl = [], []
    for i in range(n):
        lo, hi = max(0, i - window), min(n, i + window + 1)
        if hi - lo <= window:
            continue
        if highs[i] == max(highs[lo:hi]):
            sh.append(highs[i])
        if lows[i] == min(lows[lo:hi]):
            sl.append(lows[i])
    return sorted(set(sh)), sorted(set(sl))


def nearest_levels(price: float, levels: list[float]) -> tuple[float | None, float | None]:
    below = [l for l in levels if l < price]
    above = [l for l in levels if l > price]
    return (max(below) if below else None, min(above) if above else None)


def cluster_levels(levels: list[tuple[float, str]], price: float,
                    cluster_pct: float = 0.6, keep_top: int = 4) -> list[dict]:
    """Merge nearby levels within cluster_pct of each other; keep the strongest
    (most-touched, closest-to-price) few on each side. `levels` = [(price, "S"|"R"), ...]."""
    if not levels:
        return []
    ordered = sorted(levels, key=lambda x: x[0])
    clusters: list[dict] = []
    for lv, _kind in ordered:
        if clusters and abs(lv - clusters[-1]["sum"] / clusters[-1]["n"]) / lv * 100 <= cluster_pct:
            clusters[-1]["sum"] += lv
            clusters[-1]["n"] += 1
        else:
            clusters.append({"sum": lv, "n": 1})
    out = []
    for cl in clusters:
        lvl = cl["sum"] / cl["n"]
        out.append({"price": round(lvl, 2), "type": "support" if lvl < price else "resistance",
                     "touches": cl["n"]})
    sup = sorted([l for l in out if l["type"] == "support"],
                 key=lambda l: (-l["touches"], abs(l["price"] - price)))[:keep_top]
    res = sorted([l for l in out if l["type"] == "resistance"],
                 key=lambda l: (-l["touches"], abs(l["price"] - price)))[:keep_top]
    return sorted(sup + res, key=lambda l: l["price"])
