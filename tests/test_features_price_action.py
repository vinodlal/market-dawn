from core.features.price_action import (
    breakout, detect_candlestick_patterns, structure_trend, swing_sequence,
)
from tests.conftest import make_df

# Zigzag 100,110,105,115,108,120,112 with window=1 produces swing points in
# chronological order: L(100) H(110) L(105) H(115) L(108) H(120) L(112) —
# strictly increasing highs (110<115<120) and lows (100<105<108<112).
UPTREND_VALUES = [100, 110, 105, 115, 108, 120, 112]


def _zigzag_df(values):
    return make_df([{"o": v, "h": v, "l": v, "c": v} for v in values])


def test_bullish_engulfing_detected():
    rows = [
        {"o": 10, "h": 10.2, "l": 8.8, "c": 9},     # bearish prior candle
        {"o": 8.5, "h": 10.7, "l": 8.3, "c": 10.5},  # engulfs it, bullish
    ]
    df = make_df(rows)
    pats = detect_candlestick_patterns(df)
    assert any(p["type"] == "Bullish engulfing" and p["dir"] == "bull" for p in pats)


def test_swing_sequence_and_uptrend_structure():
    df = _zigzag_df(UPTREND_VALUES)
    seq = swing_sequence(df, window=1)
    assert structure_trend(seq) == "uptrend (higher highs, higher lows)"


def test_swing_sequence_and_downtrend_structure():
    # mirror the uptrend zigzag (v' = 220 - v): swap-flips every local max/min,
    # producing lower highs + lower lows by construction.
    mirrored = [220 - v for v in UPTREND_VALUES]
    df = _zigzag_df(mirrored)
    seq = swing_sequence(df, window=1)
    assert structure_trend(seq) == "downtrend (lower highs, lower lows)"


def test_breakout_above_swing_highs():
    df = _zigzag_df([100, 105, 103, 130])  # last close 130 breaks above prior highs
    assert breakout(df, swing_highs=[105, 110], swing_lows=[95, 90]) == "bullish_breakout"


def test_breakout_below_swing_lows():
    df = _zigzag_df([100, 95, 97, 80])
    assert breakout(df, swing_highs=[105, 110], swing_lows=[95, 90]) == "bearish_breakdown"


def test_no_breakout_inside_range():
    df = _zigzag_df([100, 95, 97, 100])
    assert breakout(df, swing_highs=[105, 110], swing_lows=[90, 92]) is None
