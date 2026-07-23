"""Index constituent breadth (advancers/decliners) — pure function on %changes."""
from __future__ import annotations


def breadth_summary(changes_pct: dict[str, float], flat_tol: float = 0.02) -> dict:
    advancers = {s: c for s, c in changes_pct.items() if c > flat_tol}
    decliners = {s: c for s, c in changes_pct.items() if c < -flat_tol}
    unchanged = {s: c for s, c in changes_pct.items() if s not in advancers and s not in decliners}
    total = len(changes_pct) or 1
    return {
        "advancers": sorted(advancers, key=lambda s: -advancers[s]),
        "decliners": sorted(decliners, key=lambda s: decliners[s]),
        "unchanged": sorted(unchanged),
        "n_advancers": len(advancers), "n_decliners": len(decliners),
        "n_unchanged": len(unchanged),
        "pct_bullish": round(len(advancers) / total * 100, 1),
    }
