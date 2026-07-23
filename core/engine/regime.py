"""Market regime: VIX-caution damping (ported from v1) + trend/range classification."""
from __future__ import annotations

import pandas as pd


def vix_caution(bn_df: pd.DataFrame, vix_df: pd.DataFrame, lookback: int = 3) -> tuple[bool, float | None]:
    """True if VIX rose while the index fell over the last `lookback` sessions.
    Ported from v1 scripts/analysis_engine.py:vix_caution."""
    if len(bn_df) < lookback + 1 or len(vix_df) < lookback + 1:
        return False, None
    bn_chg = (bn_df["close"].iloc[-1] - bn_df["close"].iloc[-1 - lookback]) / bn_df["close"].iloc[-1 - lookback]
    vix_chg = (vix_df["close"].iloc[-1] - vix_df["close"].iloc[-1 - lookback]) / vix_df["close"].iloc[-1 - lookback]
    caution = bool(vix_chg > 0 and bn_chg < 0)
    return caution, round(float(vix_chg) * 100, 2)


def classify_regime(adx: float | None, vix_chg_pct: float | None,
                     trend_threshold: float = 25.0, shock_vix_pct: float = 5.0) -> str:
    """ADX + VIX-change based regime read: 'shock' | 'trend' | 'range'."""
    if vix_chg_pct is not None and vix_chg_pct >= shock_vix_pct:
        return "shock"
    if adx is not None and adx >= trend_threshold:
        return "trend"
    return "range"
