from core.features.breadth import breadth_summary


def test_breadth_summary_counts_and_ranking():
    changes = {"A": 1.5, "B": -0.8, "C": 0.0, "D": 3.0, "E": -2.0}
    out = breadth_summary(changes)
    assert out["n_advancers"] == 2
    assert out["n_decliners"] == 2
    assert out["n_unchanged"] == 1
    assert out["advancers"] == ["D", "A"]      # descending by change
    assert out["decliners"] == ["E", "B"]      # ascending (most negative first)
    assert out["pct_bullish"] == 40.0          # 2/5
