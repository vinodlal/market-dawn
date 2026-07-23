"""Trade plan: entry/stop/target/R:R/size from bias + levels + ATR."""
from __future__ import annotations

from ..engine.decision import position_size


def build_trade_plan(bias: str, price: float, support: float, resistance: float,
                      atr_val: float, k_stop: float = 1.0, capital: float = 100_000,
                      risk_pct: float = 1.0, lot_size: int = 1) -> dict | None:
    if bias == "Neutral":
        return None
    if bias == "Long":
        entry, stop = price, price - k_stop * atr_val
        target1, target2 = resistance, resistance + (resistance - price)
    else:  # Short
        entry, stop = price, price + k_stop * atr_val
        target1, target2 = support, support - (price - support)

    risk, reward = abs(entry - stop), abs(target1 - entry)
    rr = round(reward / risk, 2) if risk else None
    size = position_size(capital, risk_pct, entry, stop, lot_size)
    return {
        "bias": bias, "entry": round(entry, 2), "stop": round(stop, 2),
        "target1": round(target1, 2), "target2": round(target2, 2),
        "risk_reward": rr, "size": size,
        "capital": capital, "risk_pct": risk_pct,
    }
