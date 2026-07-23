"""Moving averages: SMA/EMA, price-vs-MA stack, golden/death cross.

Ported/generalized from v1 scripts/technical.py (sma, detect_crosses); adds EMA.
"""
from __future__ import annotations

import pandas as pd

DEFAULT_WINDOWS = (20, 50, 100, 200)


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False, min_periods=window).mean()


def ma_stack(df: pd.DataFrame, windows=DEFAULT_WINDOWS, kind: str = "sma") -> dict:
    fn = sma if kind == "sma" else ema
    series = {w: fn(df["close"], w) for w in windows}
    price = float(df["close"].iloc[-1])
    last = {w: (None if pd.isna(s.iloc[-1]) else round(float(s.iloc[-1]), 2))
            for w, s in series.items()}
    valid = {w: v for w, v in last.items() if v is not None}
    above = [w for w, v in valid.items() if price >= v]
    below = [w for w, v in valid.items() if price < v]
    if valid and len(above) == len(valid):
        trend = "Strong uptrend — price above all moving averages"
    elif valid and len(below) == len(valid):
        trend = "Strong downtrend — price below all moving averages"
    elif 200 in valid and price >= valid[200]:
        trend = "Uptrend bias — price above the 200-DMA"
    elif 200 in valid:
        trend = "Downtrend bias — price below the 200-DMA"
    else:
        trend = "Insufficient history for a trend read"
    return {"price": round(price, 2), "values": last, "above": above, "below": below,
            "trend": trend}


def golden_death_crosses(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> list[dict]:
    f, s = sma(df["close"], fast), sma(df["close"], slow)
    out = []
    for i in range(1, len(df)):
        if pd.isna(f.iloc[i]) or pd.isna(s.iloc[i]) or pd.isna(f.iloc[i - 1]) or pd.isna(s.iloc[i - 1]):
            continue
        if f.iloc[i - 1] <= s.iloc[i - 1] and f.iloc[i] > s.iloc[i]:
            out.append({"date": str(df["ts"].iloc[i]), "type": "golden"})
        elif f.iloc[i - 1] >= s.iloc[i - 1] and f.iloc[i] < s.iloc[i]:
            out.append({"date": str(df["ts"].iloc[i]), "type": "death"})
    return out
