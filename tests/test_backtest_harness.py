from core.backtest.harness import _active_zone, _zone_hit, walk_forward
from core.backtest.metrics import summarize
from tests.conftest import make_df


def test_active_zone_matches_v1_semantics():
    sig = {"bias": "Long", "levels": {"support": 95, "pivot": 100, "resistance": 105}}
    assert _active_zone(sig) == (95, 100)
    sig["bias"] = "Short"
    assert _active_zone(sig) == (100, 105)
    sig["bias"] = "Neutral"
    assert _active_zone(sig) == (95, 105)


def test_zone_hit_overlap_logic():
    zone = (95, 100)
    assert _zone_hit(low=90, high=97, zone=zone) is True   # overlaps
    assert _zone_hit(low=98, high=99, zone=zone) is True   # fully inside
    assert _zone_hit(low=101, high=110, zone=zone) is False  # entirely above
    assert _zone_hit(low=80, high=90, zone=zone) is False    # entirely below


def _synthetic_uptrend(n=260):
    closes = [100 + i * 0.5 for i in range(n)]
    rows = [{"o": c - 0.2, "h": c + 0.4, "l": c - 0.5, "c": c} for c in closes]
    return make_df(rows)


def test_walk_forward_row_count_and_shape():
    df = _synthetic_uptrend(260)
    rows = walk_forward("TEST", df, min_window=210, horizon_days=1)
    assert len(rows) == len(df) - 210 - 1
    assert set(rows[0]) >= {"date", "score", "bias", "confidence", "directional_correct",
                             "r_multiple", "zone_hit", "zone", "outlier"}


def test_walk_forward_summary_is_sane_on_clean_uptrend():
    df = _synthetic_uptrend(260)
    rows = walk_forward("TEST", df, min_window=210, horizon_days=1)
    summary = summarize(rows)
    assert summary["days"] == len(rows)
    # a clean, noiseless uptrend should score decent directional accuracy
    if summary["directional_accuracy"] is not None:
        assert summary["directional_accuracy"] >= 0.5


def test_tighter_trigger_reduces_trade_count():
    df = _synthetic_uptrend(260)
    loose = walk_forward("TEST", df, min_window=210, horizon_days=1, buy_trigger=55, sell_trigger=45)
    tight = walk_forward("TEST", df, min_window=210, horizon_days=1, buy_trigger=80, sell_trigger=20)
    loose_trades = sum(1 for r in loose if r["bias"] != "Neutral")
    tight_trades = sum(1 for r in tight if r["bias"] != "Neutral")
    assert tight_trades <= loose_trades


def test_high_confidence_filter_reduces_or_matches_trade_count():
    df = _synthetic_uptrend(260)
    unfiltered = walk_forward("TEST", df, min_window=210, horizon_days=1)
    filtered = walk_forward("TEST", df, min_window=210, horizon_days=1, min_confidence="high")
    unf_trades = sum(1 for r in unfiltered if r["bias"] != "Neutral")
    filt_trades = sum(1 for r in filtered if r["bias"] != "Neutral")
    assert filt_trades <= unf_trades
