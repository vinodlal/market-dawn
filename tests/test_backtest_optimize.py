from core.backtest.optimize import grid_search, train_test_split_rows
from tests.conftest import make_df


def test_train_test_split_exact_cut():
    rows = [{"i": i} for i in range(10)]
    train, test = train_test_split_rows(rows, train_frac=0.7)
    assert len(train) == 7
    assert len(test) == 3
    assert train == rows[:7]
    assert test == rows[7:]


def _synthetic_uptrend(n=260):
    closes = [100 + i * 0.5 for i in range(n)]
    rows = [{"o": c - 0.2, "h": c + 0.4, "l": c - 0.5, "c": c} for c in closes]
    return make_df(rows)


def test_grid_search_returns_ranked_results_with_train_and_test():
    df = _synthetic_uptrend(260)
    out = grid_search("TEST", df, min_window=210,
                       threshold_grid=[(60, 40), (75, 25)],
                       confidence_grid=[None, "high"],
                       min_test_trades=1)
    assert len(out["results"]) == 4  # 2 thresholds x 2 confidence levels
    for r in out["results"]:
        assert "train" in r and "test" in r
        assert "buy_trigger" in r and "sell_trigger" in r and "min_confidence" in r
    # ranking must be by TEST (out-of-sample) objective, not train
    scores = [sum(r["test"].get(k) or 0 for k in out["objective"]) for r in out["results"]]
    assert scores == sorted(scores, reverse=True)


def test_grid_search_excludes_combos_below_min_test_trades():
    df = _synthetic_uptrend(260)
    # an extremely tight threshold should yield ~0 trades in the test split
    out = grid_search("TEST", df, min_window=210,
                       threshold_grid=[(99, 1)], confidence_grid=[None],
                       min_test_trades=1000)  # impossible to satisfy
    assert out["best"] is None
