"""Summarize walk_forward() rows into accuracy/expectancy metrics."""
from __future__ import annotations


def summarize(rows: list[dict], exclude_outliers: bool = True) -> dict:
    scored = [r for r in rows if not (exclude_outliers and r["outlier"])]

    dir_rows = [r for r in scored if r["directional_correct"] is not None]
    dir_acc = (sum(1 for r in dir_rows if r["directional_correct"]) / len(dir_rows)
               if dir_rows else None)

    zone_rows = [r for r in scored if "zone_hit" in r]
    zone_hit_rate = (sum(1 for r in zone_rows if r["zone_hit"]) / len(zone_rows)
                      if zone_rows else None)

    r_values = [r["r_multiple"] for r in scored if r["r_multiple"] is not None]
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r <= 0]
    win_rate = len(wins) / len(r_values) if r_values else None
    avg_r = sum(r_values) / len(r_values) if r_values else None
    avg_win_r = sum(wins) / len(wins) if wins else None
    avg_loss_r = abs(sum(losses) / len(losses)) if losses else None
    profit_factor = (sum(wins) / abs(sum(losses))
                      if losses and sum(losses) != 0 else None)

    equity, cum, peak, max_dd = [], 0.0, float("-inf"), 0.0
    for r in r_values:
        cum += r
        equity.append(cum)
        peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)

    return {
        "days": len(rows), "scored_days": len(scored),
        "outliers": sum(1 for r in rows if r["outlier"]),
        "directional_accuracy": round(dir_acc, 3) if dir_acc is not None else None,
        "zone_hit_rate": round(zone_hit_rate, 3) if zone_hit_rate is not None else None,
        "trades": len(r_values),
        "win_rate": round(win_rate, 3) if win_rate is not None else None,
        "avg_r": round(avg_r, 3) if avg_r is not None else None,
        "avg_win_r": round(avg_win_r, 3) if avg_win_r is not None else None,
        "avg_loss_r": round(avg_loss_r, 3) if avg_loss_r is not None else None,
        "profit_factor": round(profit_factor, 3) if profit_factor is not None else None,
        "max_drawdown_r": round(max_dd, 2),
        "equity_curve_r": [round(e, 2) for e in equity],
    }
