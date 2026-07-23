"""Decision models: bias classification, ensemble confidence, position sizing
(fixed-fractional + capped fractional Kelly), and expected-value gating.

EV gating and Kelly sizing need historical win-rate/payoff stats, which only
exist once the paper-trading ledger (M6) has scored real trades. Until then,
ev_gate() defaults to "allow, insufficient history" — the hook is wired now so
M6 only needs to supply real stats, not new logic.
"""
from __future__ import annotations


def classify_bias(score: int, buy_trigger: int = 65, sell_trigger: int = 35) -> str:
    if score >= buy_trigger:
        return "Long"
    if score <= sell_trigger:
        return "Short"
    return "Neutral"


def confidence_from_agreement(subscores: dict[str, float], weights: dict[str, float],
                               bias: str, damp_keys: tuple[str, ...] = ("vix",)) -> str:
    """High confidence needs most active factors agreeing with the overall bias."""
    if bias == "Neutral":
        return "low"
    active = {k: v for k, v in subscores.items() if k in weights and k not in damp_keys}
    if not active:
        return "low"
    agree = (sum(1 for v in active.values() if v > 55) if bias == "Long"
             else sum(1 for v in active.values() if v < 45))
    ratio = agree / len(active)
    if ratio >= 0.75:
        return "high"
    if ratio >= 0.5:
        return "medium"
    return "low"


def position_size(capital: float, risk_pct: float, entry: float, stop: float,
                   lot_size: int = 1) -> int:
    """Fixed-fractional sizing: risk risk_pct% of capital per trade."""
    per_unit_risk = abs(entry - stop)
    if per_unit_risk <= 0 or capital <= 0:
        return 0
    risk_amount = capital * risk_pct / 100
    units = risk_amount / per_unit_risk
    return max(0, int(units // lot_size))


def fractional_kelly(win_rate: float, avg_win_r: float, avg_loss_r: float,
                      fraction: float = 0.5, cap: float = 0.25) -> float:
    """Capped fractional-Kelly risk fraction from realized win-rate/payoff."""
    if avg_loss_r <= 0 or avg_win_r <= 0:
        return 0.0
    b = avg_win_r / avg_loss_r
    kelly = win_rate - (1 - win_rate) / b
    return min(max(0.0, kelly * fraction), cap)


def expected_value(win_rate: float, avg_win_r: float, avg_loss_r: float) -> float:
    return win_rate * avg_win_r - (1 - win_rate) * avg_loss_r


def ev_gate(win_rate: float | None, avg_win_r: float | None, avg_loss_r: float | None,
            min_r_r: float = 1.5) -> tuple[bool, str]:
    if win_rate is None or avg_win_r is None or avg_loss_r is None:
        return True, "insufficient trade history for EV gating — proceeding on rule-based score"
    ev = expected_value(win_rate, avg_win_r, avg_loss_r)
    rr = avg_win_r / avg_loss_r if avg_loss_r else 0.0
    if ev <= 0 or rr < min_r_r:
        return False, f"empirical EV {ev:.2f}R or R:R {rr:.2f} below threshold — signal suppressed"
    return True, f"empirical EV {ev:.2f}R, R:R {rr:.2f} — passes gate"
