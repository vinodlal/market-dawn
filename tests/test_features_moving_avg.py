from core.features.moving_avg import ema, golden_death_crosses, ma_stack, sma
from tests.conftest import make_df, flat_series


def test_sma_constant_series():
    df = make_df(flat_series(100, 10))
    out = sma(df["close"], 5)
    assert out.iloc[-1] == 100
    assert out.iloc[:4].isna().all()  # first window-1 are NaN


def test_ema_constant_series():
    df = make_df(flat_series(50, 10))
    out = ema(df["close"], 5)
    assert out.iloc[-1] == 50


def test_ma_stack_strong_uptrend_label():
    # price sits well above a rising close series -> above all short windows
    closes = [100 + i for i in range(30)]
    rows = [{"o": c, "h": c + 1, "l": c - 1, "c": c} for c in closes]
    df = make_df(rows)
    out = ma_stack(df, windows=(5, 10))
    assert out["trend"] == "Strong uptrend — price above all moving averages"
    assert set(out["above"]) == {5, 10}


def test_golden_cross_detected():
    # fast(2) crosses above slow(4) partway through a rising series
    closes = [10, 10, 10, 10, 20, 30, 40, 50]
    rows = [{"o": c, "h": c, "l": c, "c": c} for c in closes]
    df = make_df(rows)
    crosses = golden_death_crosses(df, fast=2, slow=4)
    assert any(c["type"] == "golden" for c in crosses)
