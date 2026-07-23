"""Price action: candlestick patterns, chronological swing sequence, market
structure (HH/HL vs LH/LL), and simple breakouts.

Candlestick detection ported/generalized from v1 scripts/technical.py.
"""
from __future__ import annotations

import pandas as pd


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _rng(h: float, l: float) -> float:
    return max(h - l, 1e-9)


def detect_candlestick_patterns(df: pd.DataFrame, lookback: int = 70) -> list[dict]:
    rows = df.to_dict("records")
    n = len(rows)
    out = []
    for i in range(1, n):
        d, p = rows[i], rows[i - 1]
        o, cl, h, l = d["open"], d["close"], d["high"], d["low"]
        body, rng = _body(o, cl), _rng(h, l)
        upper, lower = h - max(o, cl), min(o, cl) - l
        trend_up = i >= 5 and cl > rows[i - 5]["close"]
        trend_dn = i >= 5 and cl < rows[i - 5]["close"]

        pat = None
        if cl > o and p["close"] < p["open"] and o <= p["close"] and cl >= p["open"] \
                and body > _body(p["open"], p["close"]):
            pat = ("Bullish engulfing", "bull")
        elif cl < o and p["close"] > p["open"] and o >= p["close"] and cl <= p["open"] \
                and body > _body(p["open"], p["close"]):
            pat = ("Bearish engulfing", "bear")
        elif body <= 0.4 * rng and lower >= 2 * body and upper <= body and trend_dn:
            pat = ("Hammer", "bull")
        elif body <= 0.4 * rng and upper >= 2 * body and lower <= body and trend_up:
            pat = ("Shooting star", "bear")
        elif body <= 0.001 * o and rng > 0.004 * o:
            pat = ("Doji", "neutral")

        if pat and i >= n - lookback:
            out.append({"date": str(d["ts"]), "type": pat[0], "dir": pat[1]})
    return out


def swing_sequence(df: pd.DataFrame, window: int = 3) -> list[dict]:
    """Chronologically ordered swing highs/lows (unlike features.levels.swing_points,
    which dedups/sorts by price for S/R clustering — this preserves order for
    structure reads)."""
    highs, lows = df["high"].tolist(), df["low"].tolist()
    n = len(df)
    seq = []
    for i in range(n):
        lo, hi = max(0, i - window), min(n, i + window + 1)
        if hi - lo <= window:
            continue
        if highs[i] == max(highs[lo:hi]):
            seq.append({"idx": i, "date": str(df["ts"].iloc[i]), "price": highs[i], "kind": "H"})
        if lows[i] == min(lows[lo:hi]):
            seq.append({"idx": i, "date": str(df["ts"].iloc[i]), "price": lows[i], "kind": "L"})
    return sorted(seq, key=lambda x: x["idx"])


def structure_trend(seq: list[dict]) -> str:
    highs = [p["price"] for p in seq if p["kind"] == "H"]
    lows = [p["price"] for p in seq if p["kind"] == "L"]
    if len(highs) >= 2 and len(lows) >= 2:
        if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
            return "uptrend (higher highs, higher lows)"
        if highs[-1] < highs[-2] and lows[-1] < lows[-2]:
            return "downtrend (lower highs, lower lows)"
    return "range/unclear structure"


def breakout(df: pd.DataFrame, swing_highs: list[float], swing_lows: list[float]) -> str | None:
    price = float(df["close"].iloc[-1])
    if swing_highs and price > max(swing_highs):
        return "bullish_breakout"
    if swing_lows and price < min(swing_lows):
        return "bearish_breakdown"
    return None
