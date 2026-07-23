"""Option-chain analytics: PCR, max-pain, OI walls, OI shift.

compute_pcr ported from v1 scripts/analysis_engine.py. IV is read from the
provider's option-chain payload (Kite supplies it directly) — not computed here.
"""
from __future__ import annotations


def compute_pcr(calls: list[dict], puts: list[dict], spot: float,
                 atm_window: int = 5) -> tuple[float | None, float | None]:
    if not calls or not puts or not spot:
        return None, None
    strikes = sorted({c["strike"] for c in calls} & {p["strike"] for p in puts})
    if not strikes:
        return None, None
    atm = min(strikes, key=lambda s: abs(s - spot))
    idx = strikes.index(atm)
    lo, hi = max(0, idx - atm_window), min(len(strikes), idx + atm_window + 1)
    window = set(strikes[lo:hi])
    call_oi = sum(c["oi"] for c in calls if c["strike"] in window)
    put_oi = sum(p["oi"] for p in puts if p["strike"] in window)
    if call_oi <= 0:
        return None, atm
    return round(put_oi / call_oi, 3), atm


def max_pain(calls: list[dict], puts: list[dict]) -> float | None:
    """Strike at which option writers' total payout to holders is minimized."""
    call_oi = {c["strike"]: c["oi"] for c in calls}
    put_oi = {p["strike"]: p["oi"] for p in puts}
    all_strikes = sorted(set(call_oi) | set(put_oi))
    if not all_strikes:
        return None
    best_strike, best_pain = None, float("inf")
    for s in all_strikes:
        pain = (sum(max(0, s - k) * oi for k, oi in call_oi.items())
                + sum(max(0, k - s) * oi for k, oi in put_oi.items()))
        if pain < best_pain:
            best_pain, best_strike = pain, s
    return best_strike


def oi_walls(calls: list[dict], puts: list[dict]) -> dict:
    call_wall = max(calls, key=lambda c: c["oi"], default=None)
    put_wall = max(puts, key=lambda p: p["oi"], default=None)
    return {
        "resistance": call_wall["strike"] if call_wall else None,
        "support": put_wall["strike"] if put_wall else None,
    }


def oi_shift(prev: dict[float, int], curr: dict[float, int]) -> dict[float, float | None]:
    """Per-strike OI % change between two snapshots."""
    out: dict[float, float | None] = {}
    for k, cur_oi in curr.items():
        prev_oi = prev.get(k, 0)
        out[k] = round((cur_oi - prev_oi) / prev_oi * 100, 2) if prev_oi else None
    return out
