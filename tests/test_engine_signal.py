from core.engine.signal import analyze
from tests.conftest import make_df


def _uptrend_df(n=60, start=100.0, step=1.0):
    closes = [start + i * step for i in range(n)]
    rows = [{"o": c - 0.3, "h": c + 0.5, "l": c - 0.6, "c": c} for c in closes]
    return make_df(rows)


def test_analyze_produces_coherent_bullish_signal():
    df = _uptrend_df()
    sig = analyze("TESTIDX", kind="index", df=df)
    assert 0 <= sig["score"] <= 100
    assert sig["bias"] in ("Long", "Short", "Neutral")
    assert sig["confidence"] in ("high", "medium", "low")
    assert len(sig["reasons"]) > 0
    assert sig["disclaimer"]
    # a clean, strong uptrend should read at least mildly bullish
    assert sig["score"] > 50


def test_analyze_future_includes_oi_subscore():
    df = _uptrend_df()
    sig = analyze("TESTFUT", kind="future", df=df, oi_buildup="long_buildup")
    assert "oi" in sig["component_scores"]
    assert "oi" in sig["weights"]


def test_analyze_reasons_are_explainable_strings():
    df = _uptrend_df()
    sig = analyze("TESTIDX", kind="index", df=df)
    assert all(isinstance(r, str) and len(r) > 5 for r in sig["reasons"])
