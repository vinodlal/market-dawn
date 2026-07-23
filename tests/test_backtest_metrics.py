from core.backtest.metrics import summarize


def test_summarize_known_values():
    rows = [
        {"outlier": False, "directional_correct": True, "r_multiple": 2.0},
        {"outlier": False, "directional_correct": False, "r_multiple": -1.0},
        {"outlier": False, "directional_correct": True, "r_multiple": 1.5},
        {"outlier": True, "directional_correct": True, "r_multiple": 5.0},   # excluded
        {"outlier": False, "directional_correct": None, "r_multiple": None},  # Neutral day
    ]
    out = summarize(rows)
    assert out["days"] == 5
    assert out["scored_days"] == 4
    assert out["outliers"] == 1
    assert out["directional_accuracy"] == round(2 / 3, 3)
    assert out["trades"] == 3
    assert out["win_rate"] == round(2 / 3, 3)
    assert out["avg_r"] == round(2.5 / 3, 3)
    assert out["avg_win_r"] == 1.75
    assert out["avg_loss_r"] == 1.0
    assert out["profit_factor"] == 3.5
    assert out["max_drawdown_r"] == -1.0
    assert out["equity_curve_r"] == [2.0, 1.0, 2.5]


def test_summarize_empty_rows():
    out = summarize([])
    assert out["days"] == 0
    assert out["directional_accuracy"] is None
    assert out["win_rate"] is None
    assert out["equity_curve_r"] == []
