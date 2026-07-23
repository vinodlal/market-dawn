"""Chart-pattern heuristics: double top/bottom, triangles, channels, flags,
head & shoulders — built on price_action.swing_sequence().

These are heuristic detectors (not exact-match), tuned on clean synthetic
shapes in tests; real-world detections should be read as suggestive, not exact.
"""
from __future__ import annotations

import pandas as pd


def _slope(points: list[dict]) -> float:
    xs = [p["idx"] for p in points]
    ys = [p["price"] for p in points]
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs) or 1e-9
    return num / den


def detect_double_top_bottom(seq: list[dict], tolerance_pct: float = 1.0) -> dict | None:
    highs = [p for p in seq if p["kind"] == "H"]
    lows = [p for p in seq if p["kind"] == "L"]
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        if abs(h1["price"] - h2["price"]) / h1["price"] * 100 <= tolerance_pct:
            return {"type": "double_top", "dir": "bear", "level": round((h1["price"] + h2["price"]) / 2, 2)}
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        if abs(l1["price"] - l2["price"]) / l1["price"] * 100 <= tolerance_pct:
            return {"type": "double_bottom", "dir": "bull", "level": round((l1["price"] + l2["price"]) / 2, 2)}
    return None


def detect_triangle(seq: list[dict], lookback: int = 6, flat_slope_tol: float = 0.05) -> dict | None:
    highs = [p for p in seq if p["kind"] == "H"][-lookback:]
    lows = [p for p in seq if p["kind"] == "L"][-lookback:]
    if len(highs) < 2 or len(lows) < 2:
        return None
    href = highs[-1]["price"]
    hs, ls = _slope(highs) / href * 100, _slope(lows) / href * 100
    h_flat, l_flat = abs(hs) < flat_slope_tol, abs(ls) < flat_slope_tol
    if h_flat and ls > flat_slope_tol:
        return {"type": "ascending_triangle", "dir": "bull"}
    if l_flat and hs < -flat_slope_tol:
        return {"type": "descending_triangle", "dir": "bear"}
    if hs < -flat_slope_tol and ls > flat_slope_tol:
        return {"type": "symmetrical_triangle", "dir": "neutral"}
    return None


def detect_channel(seq: list[dict], lookback: int = 6, min_slope: float = 0.05,
                    parallel_tol: float = 0.5) -> dict | None:
    highs = [p for p in seq if p["kind"] == "H"][-lookback:]
    lows = [p for p in seq if p["kind"] == "L"][-lookback:]
    if len(highs) < 2 or len(lows) < 2:
        return None
    href = highs[-1]["price"]
    hs, ls = _slope(highs) / href * 100, _slope(lows) / href * 100
    if abs(hs) > min_slope and abs(ls) > min_slope and abs(hs - ls) <= parallel_tol:
        direction = "up" if hs > 0 else "down"
        return {"type": f"{direction}_channel", "dir": "bull" if direction == "up" else "bear"}
    return None


def detect_flag(df: pd.DataFrame, pole_lookback: int = 10, flag_lookback: int = 5,
                 pole_min_pct: float = 3.0) -> dict | None:
    if len(df) < pole_lookback + flag_lookback:
        return None
    pole_start = df["close"].iloc[-(pole_lookback + flag_lookback)]
    pole_end = df["close"].iloc[-flag_lookback]
    pole_pct = (pole_end - pole_start) / pole_start * 100
    if abs(pole_pct) < pole_min_pct:
        return None
    flag_slice = df.iloc[-flag_lookback:]
    flag_range_pct = (flag_slice["high"].max() - flag_slice["low"].min()) / pole_end * 100
    if flag_range_pct < abs(pole_pct) * 0.6:
        direction = "bull" if pole_pct > 0 else "bear"
        return {"type": f"{direction}_flag", "dir": direction}
    return None


def detect_head_shoulders(seq: list[dict], tolerance_pct: float = 2.0) -> dict | None:
    highs = [p for p in seq if p["kind"] == "H"][-3:]
    if len(highs) == 3:
        l, h, r = highs
        if h["price"] > l["price"] and h["price"] > r["price"] \
                and abs(l["price"] - r["price"]) / l["price"] * 100 <= tolerance_pct:
            return {"type": "head_and_shoulders", "dir": "bear"}
    lows = [p for p in seq if p["kind"] == "L"][-3:]
    if len(lows) == 3:
        l, h, r = lows
        if h["price"] < l["price"] and h["price"] < r["price"] \
                and abs(l["price"] - r["price"]) / l["price"] * 100 <= tolerance_pct:
            return {"type": "inverse_head_and_shoulders", "dir": "bull"}
    return None


def detect_all(df: pd.DataFrame, seq: list[dict]) -> list[dict]:
    out = []
    for hit in (detect_double_top_bottom(seq), detect_triangle(seq),
                detect_channel(seq), detect_flag(df), detect_head_shoulders(seq)):
        if hit:
            out.append(hit)
    return out
