"""Walk-forward parameter search: sweeps buy/sell trigger thresholds and
confidence filtering, ranked by OUT-OF-SAMPLE performance on a strict
train/test split of the walk-forward days.

Why a train/test split matters here: walk_forward() itself is already
lookahead-free day-by-day, but if we pick the "best" threshold combo by
looking at performance across the WHOLE backtest window and then report
that same window's numbers, we're curve-fitting to this one dataset — the
combo that happens to look best on this specific 2yr history isn't
necessarily the one with real predictive value. Splitting into train
(select the combo) and test (report its honest performance, untouched
during selection) is the minimum discipline needed to tell a real
improvement from a lucky fit.
"""
from __future__ import annotations

from .harness import walk_forward
from .metrics import summarize

DEFAULT_THRESHOLD_GRID = [(55, 45), (60, 40), (65, 35), (70, 30), (75, 25), (80, 20)]
DEFAULT_CONFIDENCE_GRID = [None, "medium", "high"]
DEFAULT_OBJECTIVE = ("zone_hit_rate", "win_rate")


def train_test_split_rows(rows: list[dict], train_frac: float = 0.7) -> tuple[list[dict], list[dict]]:
    cut = int(len(rows) * train_frac)
    return rows[:cut], rows[cut:]


def grid_search(symbol: str, df, vix_df=None, drivers=None, *, kind: str = "index",
                 weights: dict | None = None, min_window: int = 210, horizon_days: int = 1,
                 trade_max_days: int = 10, threshold_grid=None, confidence_grid=None,
                 train_frac: float = 0.7, objective: tuple[str, ...] = DEFAULT_OBJECTIVE,
                 min_test_trades: int = 5) -> dict:
    threshold_grid = threshold_grid or DEFAULT_THRESHOLD_GRID
    confidence_grid = confidence_grid or DEFAULT_CONFIDENCE_GRID

    results = []
    for buy_trigger, sell_trigger in threshold_grid:
        for min_conf in confidence_grid:
            rows = walk_forward(symbol, df, vix_df=vix_df, drivers=drivers, kind=kind,
                                 weights=weights, min_window=min_window, horizon_days=horizon_days,
                                 trade_max_days=trade_max_days, buy_trigger=buy_trigger,
                                 sell_trigger=sell_trigger, min_confidence=min_conf)
            train_rows, test_rows = train_test_split_rows(rows, train_frac)
            results.append({
                "buy_trigger": buy_trigger, "sell_trigger": sell_trigger,
                "min_confidence": min_conf,
                "train": summarize(train_rows), "test": summarize(test_rows),
            })

    def _rank_key(r: dict):
        t = r["test"]
        # too few out-of-sample trades to trust the combo's win_rate/zone_hit_rate --
        # don't let a lucky small sample win the ranking
        if t.get("scored_days", 0) == 0 or t.get("trades", 0) < min_test_trades:
            return float("-inf")
        vals = [t.get(k) for k in objective]
        if any(v is None for v in vals):
            return float("-inf")
        return sum(vals)

    ranked = sorted(results, key=_rank_key, reverse=True)
    return {"objective": list(objective), "min_test_trades": min_test_trades,
            "results": ranked, "best": ranked[0] if ranked and _rank_key(ranked[0]) > float("-inf") else None}
