import pytest

from core.features.momentum import adx, atr, bollinger, macd, rsi, volume_spike, vwap
from tests.conftest import flat_series, make_df


def test_rsi_all_gains_is_100():
    closes = list(range(100, 130))  # +1 every day, no losses
    rows = [{"o": c, "h": c, "l": c, "c": c} for c in closes]
    df = make_df(rows)
    out = rsi(df["close"], window=14)
    assert out.iloc[-1] == 100


def test_rsi_all_losses_is_0():
    closes = list(range(130, 100, -1))  # -1 every day, no gains
    rows = [{"o": c, "h": c, "l": c, "c": c} for c in closes]
    df = make_df(rows)
    out = rsi(df["close"], window=14)
    assert out.iloc[-1] == 0


def test_atr_zero_for_flat_series():
    df = make_df(flat_series(100, 20))
    out = atr(df, window=14)
    assert out.iloc[-1] == 0


def test_bollinger_bands_collapse_on_flat_series():
    df = make_df(flat_series(50, 25))
    b = bollinger(df["close"], window=20, num_std=2)
    assert b["mid"].iloc[-1] == 50
    assert b["upper"].iloc[-1] == 50
    assert b["lower"].iloc[-1] == 50


def test_macd_zero_on_flat_series():
    df = make_df(flat_series(75, 20))
    m = macd(df["close"], fast=3, slow=6, signal=3)
    assert m["hist"].iloc[-1] == 0
    assert m["macd"].iloc[-1] == 0


def test_adx_high_for_strong_uptrend():
    # high/low/close all step up by a constant amount every bar -> no down-moves
    rows = [{"o": 100 + i, "h": 101 + i, "l": 99 + i, "c": 100 + i} for i in range(40)]
    df = make_df(rows)
    out = adx(df, window=14)
    assert out.iloc[-1] > 90


def test_vwap_hand_computed():
    rows = [
        {"o": 9, "h": 10, "l": 8, "c": 9, "v": 100},
        {"o": 9, "h": 12, "l": 10, "c": 11, "v": 200},
        {"o": 11, "h": 11, "l": 9, "c": 10, "v": 100},
    ]
    df = make_df(rows)
    out = vwap(df)
    assert out.iloc[0] == pytest.approx(9.0)
    assert out.iloc[1] == pytest.approx(3100 / 300)
    assert out.iloc[2] == pytest.approx(4100 / 400)


def test_volume_spike_flagged():
    rows = [{"o": 100, "h": 100, "l": 100, "c": 100, "v": 100} for _ in range(20)]
    rows.append({"o": 100, "h": 100, "l": 100, "c": 100, "v": 300})
    df = make_df(rows)
    out = volume_spike(df, window=20, mult=1.5)
    assert bool(out.iloc[-1]) is True
    assert bool(out.iloc[-2]) is False
