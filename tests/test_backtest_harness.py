from core.backtest.harness import walk_forward
from core.backtest.metrics import summarize
from tests.conftest import make_df


def _synthetic_uptrend(n=260):
    closes = [100 + i * 0.5 for i in range(n)]
    rows = [{"o": c - 0.2, "h": c + 0.4, "l": c - 0.5, "c": c} for c in closes]
    return make_df(rows)


def test_walk_forward_row_count_and_shape():
    df = _synthetic_uptrend(260)
    rows = walk_forward("TEST", df, min_window=210, horizon_days=1)
    assert len(rows) == len(df) - 210 - 1
    assert set(rows[0]) >= {"date", "score", "bias", "confidence", "directional_correct",
                             "r_multiple", "outlier"}


def test_walk_forward_summary_is_sane_on_clean_uptrend():
    df = _synthetic_uptrend(260)
    rows = walk_forward("TEST", df, min_window=210, horizon_days=1)
    summary = summarize(rows)
    assert summary["days"] == len(rows)
    # a clean, noiseless uptrend should score decent directional accuracy
    if summary["directional_accuracy"] is not None:
        assert summary["directional_accuracy"] >= 0.5
