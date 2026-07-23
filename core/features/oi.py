"""Futures OI build-up classification (price x OI quadrant matrix)."""
from __future__ import annotations

import pandas as pd

LONG_BUILDUP = "long_buildup"
SHORT_BUILDUP = "short_buildup"
LONG_UNWINDING = "long_unwinding"
SHORT_COVERING = "short_covering"
NEUTRAL = "neutral"


def classify_buildup(price_chg_pct: float, oi_chg_pct: float, flat_tol: float = 0.02) -> str:
    """price up & OI up -> long buildup (bullish); price down & OI up -> short
    buildup (bearish); price down & OI down -> long unwinding; price up & OI
    down -> short covering (bullish)."""
    if abs(price_chg_pct) < flat_tol or abs(oi_chg_pct) < flat_tol:
        return NEUTRAL
    if price_chg_pct > 0 and oi_chg_pct > 0:
        return LONG_BUILDUP
    if price_chg_pct < 0 and oi_chg_pct > 0:
        return SHORT_BUILDUP
    if price_chg_pct < 0 and oi_chg_pct < 0:
        return LONG_UNWINDING
    if price_chg_pct > 0 and oi_chg_pct < 0:
        return SHORT_COVERING
    return NEUTRAL


IMPLICATION = {
    LONG_BUILDUP: "bullish", SHORT_COVERING: "bullish",
    SHORT_BUILDUP: "bearish", LONG_UNWINDING: "bearish",
    NEUTRAL: "neutral",
}


def buildup_series(price: pd.Series, oi: pd.Series) -> pd.Series:
    price_chg = price.pct_change() * 100
    oi_chg = oi.pct_change() * 100
    return pd.Series(
        [classify_buildup(p, o) if pd.notna(p) and pd.notna(o) else None
         for p, o in zip(price_chg, oi_chg)],
        index=price.index,
    )
