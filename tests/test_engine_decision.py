import pytest

from core.engine.decision import (
    classify_bias, confidence_from_agreement, ev_gate, expected_value,
    fractional_kelly, position_size,
)


def test_classify_bias_thresholds():
    assert classify_bias(65) == "Long"
    assert classify_bias(64) == "Neutral"
    assert classify_bias(35) == "Short"
    assert classify_bias(36) == "Neutral"


def test_confidence_high_when_factors_agree():
    subscores = {"sr": 70, "gap": 65, "momentum": 80, "vix": 50}
    weights = {"sr": 25, "gap": 25, "momentum": 25, "vix": 10}
    assert confidence_from_agreement(subscores, weights, "Long") == "high"


def test_confidence_low_when_factors_disagree():
    subscores = {"sr": 70, "gap": 30, "momentum": 48}
    weights = {"sr": 25, "gap": 25, "momentum": 25}
    assert confidence_from_agreement(subscores, weights, "Long") == "low"


def test_confidence_low_for_neutral_bias():
    assert confidence_from_agreement({"sr": 60}, {"sr": 25}, "Neutral") == "low"


def test_position_size_exact():
    # capital=100000, risk 1% = 1000; per-unit risk = 2 -> 500 units -> /lot_size
    assert position_size(100_000, 1.0, entry=100, stop=98, lot_size=1) == 500
    assert position_size(100_000, 1.0, entry=100, stop=98, lot_size=25) == 20


def test_position_size_zero_risk_is_zero():
    assert position_size(100_000, 1.0, entry=100, stop=100) == 0


def test_fractional_kelly_known_value():
    # b=1.5; kelly=0.6-0.4/1.5=0.3333; *0.5=0.1667
    out = fractional_kelly(win_rate=0.6, avg_win_r=1.5, avg_loss_r=1.0, fraction=0.5, cap=0.25)
    assert out == pytest.approx(0.1667, abs=1e-3)


def test_fractional_kelly_capped():
    out = fractional_kelly(win_rate=0.9, avg_win_r=3.0, avg_loss_r=1.0, fraction=1.0, cap=0.25)
    assert out == 0.25


def test_expected_value_exact():
    assert expected_value(0.6, 1.5, 1.0) == pytest.approx(0.5)


def test_ev_gate_insufficient_history_allows():
    allow, reason = ev_gate(None, None, None)
    assert allow is True
    assert "insufficient" in reason


def test_ev_gate_blocks_negative_ev():
    allow, _ = ev_gate(win_rate=0.3, avg_win_r=1.0, avg_loss_r=1.0)
    assert allow is False


def test_ev_gate_allows_strong_setup():
    allow, _ = ev_gate(win_rate=0.6, avg_win_r=2.0, avg_loss_r=1.0, min_r_r=1.5)
    assert allow is True
