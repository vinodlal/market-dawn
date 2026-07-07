"""
optimize_weights.py — Section 8. Tune composite-score weights.

After >= 20 scored (non-outlier) trading days exist, grid-search the four
composite weights (sr, gap, pcr, vix) to maximize
    objective = directional_accuracy + zone_hit_rate
evaluated only on non-outlier days.

Guardrails:
  - each weight may drift at most +-5 points from its current value per cycle,
  - weights are integers that sum to 100,
  - if fewer than 20 scored days exist, do nothing (avoid overfitting a short window).

Writes the winning weights to data/model_weights.json.
"""

import json
import os
from datetime import date

import analysis_engine as ae
import backtest as bt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_FILE = os.path.join(ROOT, "data", "model_weights.json")

MIN_SCORED_DAYS = 20
DRIFT_CAP = 5           # +-5 points per weight per cycle
STEP = 1                # search granularity


def candidate_weights(current):
    """All integer (sr,gap,pcr,vix) within +-DRIFT_CAP of current, summing to 100."""
    keys = ["sr", "gap", "pcr", "vix"]
    ranges = {k: range(max(0, current[k] - DRIFT_CAP),
                        current[k] + DRIFT_CAP + 1, STEP) for k in keys}
    out = []
    for sr in ranges["sr"]:
        for gap in ranges["gap"]:
            for pcr in ranges["pcr"]:
                vix = 100 - sr - gap - pcr
                if vix < 0:
                    continue
                if abs(vix - current["vix"]) > DRIFT_CAP:
                    continue
                out.append({"sr": sr, "gap": gap, "pcr": pcr, "vix": vix})
    return out


def objective(pairs, weights, macro_flags):
    rows = [bt.evaluate_day(prev, cur, weights, macro_flags) for prev, cur in pairs]
    scored = [r for r in rows if not r["outlier_flag"]]
    if not scored:
        return -1.0, 0
    dir_rows = [r for r in scored if r["directional_correct"] is not None]
    dir_acc = (sum(1 for r in dir_rows if r["directional_correct"]) / len(dir_rows)
               if dir_rows else 0.0)
    hit = sum(1 for r in scored if r["zone_hit"]) / len(scored)
    return dir_acc + hit, len(scored)


def main():
    current = ae.load_weights()
    macro_flags = ae.load_macro_flags()
    pairs = bt.build_pairs()

    # count scored days at current weights
    base_score, scored_days = objective(pairs, current, macro_flags)
    if scored_days < MIN_SCORED_DAYS:
        print(f"Only {scored_days} scored days (< {MIN_SCORED_DAYS}). "
              f"Keeping current weights {current}.")
        return

    best_w, best_obj = current, base_score
    for w in candidate_weights(current):
        obj, _ = objective(pairs, w, macro_flags)
        if obj > best_obj + 1e-9:
            best_obj, best_w = obj, w

    payload = {
        "weights": best_w,
        "updated": date.today().isoformat(),
        "version": 1,
        "note": "Optimized via grid search over non-outlier backtest days "
                f"(objective dir_acc+hit_rate: {base_score:.3f} -> {best_obj:.3f}). "
                f"Drift capped at +-{DRIFT_CAP} pts/cycle.",
    }
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Weights {current} -> {best_w} "
          f"(objective {base_score:.3f} -> {best_obj:.3f}, {scored_days} scored days)")


if __name__ == "__main__":
    main()
