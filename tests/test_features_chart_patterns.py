from core.features.chart_patterns import (
    detect_channel, detect_double_top_bottom, detect_flag, detect_head_shoulders,
    detect_triangle,
)
from tests.conftest import make_df


def test_double_top_detected():
    seq = [
        {"idx": 0, "price": 100, "kind": "L"},
        {"idx": 1, "price": 150, "kind": "H"},
        {"idx": 2, "price": 110, "kind": "L"},
        {"idx": 3, "price": 151, "kind": "H"},  # within 1% of the first high
    ]
    hit = detect_double_top_bottom(seq, tolerance_pct=1.0)
    assert hit == {"type": "double_top", "dir": "bear", "level": 150.5}


def test_double_bottom_detected():
    seq = [
        {"idx": 0, "price": 200, "kind": "H"},
        {"idx": 1, "price": 100, "kind": "L"},
        {"idx": 2, "price": 190, "kind": "H"},
        {"idx": 3, "price": 100.5, "kind": "L"},
    ]
    hit = detect_double_top_bottom(seq, tolerance_pct=1.0)
    assert hit["type"] == "double_bottom"
    assert hit["dir"] == "bull"


def test_ascending_triangle_flat_highs_rising_lows():
    seq = [
        {"idx": 0, "price": 150.0, "kind": "H"},
        {"idx": 1, "price": 100, "kind": "L"},
        {"idx": 2, "price": 150.2, "kind": "H"},
        {"idx": 3, "price": 110, "kind": "L"},
        {"idx": 4, "price": 149.9, "kind": "H"},
        {"idx": 5, "price": 120, "kind": "L"},
    ]
    hit = detect_triangle(seq)
    assert hit == {"type": "ascending_triangle", "dir": "bull"}


def test_up_channel_parallel_rising_highs_and_lows():
    seq = [
        {"idx": 0, "price": 150, "kind": "H"},
        {"idx": 1, "price": 100, "kind": "L"},
        {"idx": 2, "price": 155, "kind": "H"},
        {"idx": 3, "price": 105, "kind": "L"},
        {"idx": 4, "price": 160, "kind": "H"},
        {"idx": 5, "price": 110, "kind": "L"},
    ]
    hit = detect_channel(seq)
    assert hit == {"type": "up_channel", "dir": "bull"}


def test_bull_flag_after_strong_pole():
    pole = [100 + i for i in range(10)]                       # 100 -> 109, +10% pole
    flag = [110, 109.8, 110.2, 109.9, 110.1]                   # tight consolidation ~110
    closes = pole + flag
    rows = [{"o": c, "h": c + 0.1, "l": c - 0.1, "c": c} for c in closes]
    df = make_df(rows)
    hit = detect_flag(df, pole_lookback=10, flag_lookback=5, pole_min_pct=3.0)
    assert hit == {"type": "bull_flag", "dir": "bull"}


def test_head_and_shoulders_detected():
    seq = [
        {"idx": 0, "price": 140, "kind": "H"},
        {"idx": 2, "price": 160, "kind": "H"},
        {"idx": 4, "price": 141, "kind": "H"},
    ]
    hit = detect_head_shoulders(seq, tolerance_pct=2.0)
    assert hit == {"type": "head_and_shoulders", "dir": "bear"}


def test_no_pattern_on_flat_noise():
    seq = [{"idx": i, "price": 100 + (i % 2), "kind": "H" if i % 2 == 0 else "L"}
           for i in range(4)]
    assert detect_triangle(seq) is None
