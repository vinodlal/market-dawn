"""
backtest.py — Section 8. Reconstruct past recommendations and score them.

For each pair of consecutive history days (T-1, T):
  - run analysis_engine.analyze() on the T-1 payload  (only data available at T-1 close),
  - compare its recommendation against what actually happened on day T.

Metrics per day (written to data/backtest_log.json):
  - directional_accuracy : did next-day move match the implied direction?
  - zone_hit_rate        : did T's session range enter the predicted zone?
  - outlier_flag         : unscheduled shock -> excluded from optimization scoring.

Exposes build_pairs() / evaluate_day() / is_outlier() for optimize_weights.py.
Rebuilds the whole log from history each run (idempotent, no duplicate rows).
"""

import json
import os
from datetime import datetime

import numpy as np

import analysis_engine as ae

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(ROOT, "data", "backtest_log.json")

OUTLIER_MIN_MOVE_PCT = 3.0   # absolute floor for "shock"
OUTLIER_VOL_MULT = 2.0       # or 2x the 20-day realized vol


def load_payload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_pairs():
    """Return [(prev_payload, cur_payload), ...] over consecutive history files."""
    files = ae.load_history_files()
    payloads = [load_payload(p) for p in files]
    payloads = [p for p in payloads if p.get("banknifty", {}).get("candles")]
    return list(zip(payloads[:-1], payloads[1:]))


def realized_vol_pct(candles, window=20):
    closes = np.array([c["close"] for c in candles[-(window + 1):]], dtype=float)
    if len(closes) < 3:
        return None
    rets = np.diff(closes) / closes[:-1]
    return float(np.std(rets) * 100)


def is_outlier(daily_move_pct, prev_candles, cur_date, macro_flags):
    scheduled = {m["date"] for m in macro_flags if m.get("type") == "scheduled"}
    if cur_date in scheduled:
        return False, "scheduled event — kept in scoring"
    vol = realized_vol_pct(prev_candles) or 0.0
    threshold = max(OUTLIER_MIN_MOVE_PCT, OUTLIER_VOL_MULT * vol)
    if abs(daily_move_pct) > threshold:
        return True, (f"|move| {abs(daily_move_pct):.1f}% > {threshold:.1f}% "
                      f"(max of 3% and 2x{vol:.1f}% vol) — unscheduled shock")
    return False, ""


def _range_overlaps_zone(low, high, zone):
    z_lo, z_hi = min(zone), max(zone)
    return not (high < z_lo or low > z_hi)


def _zone_accuracy_pct(actual_close, zone):
    z_lo, z_hi = min(zone), max(zone)
    if z_lo <= actual_close <= z_hi:
        return 100.0
    width = max(z_hi - z_lo, 1e-9)
    dist = z_lo - actual_close if actual_close < z_lo else actual_close - z_hi
    return round(max(0.0, 100.0 - dist / width * 100.0), 1)


def evaluate_day(prev_payload, cur_payload, weights, macro_flags):
    """Score a single (T-1 -> T) transition. Returns a log row dict."""
    pred = ae.analyze(prev_payload, weights, macro_flags)

    prev_candle = prev_payload["banknifty"]["candles"][-1]
    cur_candle = cur_payload["banknifty"]["candles"][-1]
    prev_close = prev_candle["close"]
    actual_open = cur_candle["open"]
    actual_close = cur_candle["close"]
    actual_low = cur_candle["low"]
    actual_high = cur_candle["high"]
    cur_date = cur_payload["date"]
    daily_move_pct = (actual_close - prev_close) / prev_close * 100 if prev_close else 0.0

    rec = pred["recommendation"]
    if rec == "Buy Zone":
        active_zone = pred["buy_zone"]
        directional_correct = daily_move_pct > 0
    elif rec == "Sell Zone":
        active_zone = pred["sell_zone"]
        directional_correct = daily_move_pct < 0
    else:  # Neutral — direction not scored; zone = full support..resistance span
        active_zone = [min(pred["buy_zone"] + pred["sell_zone"]),
                       max(pred["buy_zone"] + pred["sell_zone"])]
        directional_correct = None

    zone_hit = _range_overlaps_zone(actual_low, actual_high, active_zone)
    zone_accuracy = _zone_accuracy_pct(actual_close, active_zone)
    outlier, reason = is_outlier(daily_move_pct, prev_payload["banknifty"]["candles"],
                                 cur_date, macro_flags)

    return {
        "date": cur_date,
        "recommendation": rec,
        "score": pred["score"],
        "buy_zone": pred["buy_zone"],
        "sell_zone": pred["sell_zone"],
        "active_zone": active_zone,
        "prev_close": round(prev_close, 2),
        "actual_open": round(actual_open, 2),
        "actual_close": round(actual_close, 2),
        "daily_move_pct": round(daily_move_pct, 3),
        "directional_correct": directional_correct,
        "zone_hit": zone_hit,
        "zone_accuracy_pct": zone_accuracy,
        "outlier_flag": outlier,
        "outlier_reason": reason,
        "reasons": pred["reasons"],
    }


def summarize(rows):
    scored = [r for r in rows if not r["outlier_flag"]]
    dir_rows = [r for r in scored if r["directional_correct"] is not None]
    dir_acc = (sum(1 for r in dir_rows if r["directional_correct"]) / len(dir_rows)
               if dir_rows else None)
    hit_rate = (sum(1 for r in scored if r["zone_hit"]) / len(scored)
                if scored else None)
    return {
        "days": len(rows),
        "scored_days": len(scored),
        "outliers": sum(1 for r in rows if r["outlier_flag"]),
        "directional_accuracy": round(dir_acc, 3) if dir_acc is not None else None,
        "overall_hit_rate": round(hit_rate, 3) if hit_rate is not None else None,
    }


def run():
    weights = ae.load_weights()
    macro_flags = ae.load_macro_flags()
    rows = [evaluate_day(prev, cur, weights, macro_flags)
            for prev, cur in build_pairs()]
    log = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": summarize(rows),
        "days": rows,
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    return log


def main():
    log = run()
    s = log["summary"]
    print(f"Backtest over {s['days']} transitions ({s['scored_days']} scored, "
          f"{s['outliers']} outliers)")
    print(f"  directional_accuracy = {s['directional_accuracy']}")
    print(f"  overall_hit_rate     = {s['overall_hit_rate']}")


if __name__ == "__main__":
    main()
