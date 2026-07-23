"""Reconcile the new engine against v1's recorded output for 2026-07-07
(data/history/2026-07-07.json -> data/latest.json), per the M3 confirm gate.

Same inputs, same v1 weights {sr:40, gap:25, pcr:20, vix:15} -> same score.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core.engine.regime import vix_caution
from core.engine.score import composite_score, gap_subscore, pcr_subscore, sr_subscore
from core.features.gaps import unfilled_gaps
from core.features.levels import nearest_levels, pivot_levels, swing_points
from core.features.options import compute_pcr

ROOT = Path(__file__).resolve().parents[1]
V1_WEIGHTS = {"sr": 40, "gap": 25, "pcr": 20, "vix": 15}


def _v1_candles_to_df(candles: list[dict]) -> pd.DataFrame:
    ts = pd.to_datetime([c["date"] for c in candles]).tz_localize("Asia/Kolkata")
    return pd.DataFrame({
        "ts": ts,
        "open": [c["open"] for c in candles], "high": [c["high"] for c in candles],
        "low": [c["low"] for c in candles], "close": [c["close"] for c in candles],
        "volume": [c["volume"] for c in candles],
    })


def test_banknifty_swing_score_reconciles_with_v1():
    payload = json.loads((ROOT / "data" / "history" / "2026-07-07.json").read_text(encoding="utf-8"))
    v1_latest = json.loads((ROOT / "data" / "latest.json").read_text(encoding="utf-8"))
    assert v1_latest["date"] == "2026-07-07"

    bn = _v1_candles_to_df(payload["banknifty"]["candles"])
    vix = _v1_candles_to_df(payload["vix"]["candles"])
    last = bn.iloc[-1]
    price = float(last["close"])

    piv = pivot_levels(last["high"], last["low"], last["close"])
    sh, sl = swing_points(bn, window=3)
    level_set = [piv["r1"], piv["r2"], piv["s1"], piv["s2"], *sh, *sl]
    support, resistance = nearest_levels(price, level_set)
    if support is None:
        support = min(piv["s1"], price * 0.99)
    if resistance is None:
        resistance = max(piv["r1"], price * 1.01)

    gaps = unfilled_gaps(bn, threshold_pct=0.3)

    oc = payload["option_chain"]
    pcr, atm = compute_pcr(oc["calls"], oc["puts"], oc["spot"], atm_window=5)

    caution, _vix_chg = vix_caution(bn, vix, lookback=3)

    sr = sr_subscore(price, support, resistance)
    gap_s = gap_subscore(price, gaps)
    pcr_s = pcr_subscore(pcr)
    score = composite_score({"sr": sr, "gap": gap_s, "pcr": pcr_s}, V1_WEIGHTS,
                             damp_flags={"vix": caution})

    # -- reconcile against v1's recorded values --------------------------------
    assert score == v1_latest["score"] == 60
    assert round(piv["pivot"], 2) == v1_latest["levels"]["pivot"]
    assert round(support, 2) == v1_latest["levels"]["nearest_support"]
    assert round(resistance, 2) == v1_latest["levels"]["nearest_resistance"]
    assert atm == v1_latest["levels"]["atm_strike"]
    assert pcr == v1_latest["pcr"] == 0.821
    assert round(sr, 1) == v1_latest["components"]["sr"] == 61.3
    assert round(gap_s, 1) == v1_latest["components"]["gap"] == 75.0
    assert round(pcr_s, 1) == v1_latest["components"]["pcr"] == 37.1
    assert caution == v1_latest["components"]["vix_caution"] == False
    assert 35 < score < 65  # Neutral band, matches v1_latest["recommendation"] == "Neutral"
