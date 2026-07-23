from core.trade_plan.plan import build_trade_plan


def test_neutral_bias_has_no_plan():
    assert build_trade_plan("Neutral", 100, 90, 110, atr_val=5) is None


def test_long_target_floored_by_atr_when_resistance_is_near():
    # resistance(102) is closer than the ATR-floor target(100+2*5=110) ->
    # the floor wins, guaranteeing R:R = k_target/k_stop = 2.0
    plan = build_trade_plan("Long", price=100, support=90, resistance=102,
                             atr_val=5, k_stop=1.0, k_target=2.0)
    assert plan["entry"] == 100
    assert plan["stop"] == 95
    assert plan["target1"] == 110       # ATR floor, not the near resistance
    assert plan["target2"] == 120
    assert plan["risk_reward"] == 2.0


def test_long_target_extended_when_resistance_is_far():
    # resistance(130) is further than the ATR floor(110) -> real S/R extends it
    plan = build_trade_plan("Long", price=100, support=90, resistance=130,
                             atr_val=5, k_stop=1.0, k_target=2.0)
    assert plan["target1"] == 130
    assert plan["risk_reward"] == 6.0


def test_short_target_floored_and_extended():
    near = build_trade_plan("Short", price=100, support=85, resistance=110,
                             atr_val=4, k_stop=1.0, k_target=2.0)
    assert near["stop"] == 104
    assert near["target1"] == 85        # support(85) further than ATR floor(92) -> extends
    assert near["risk_reward"] == 3.75

    close_support = build_trade_plan("Short", price=100, support=97, resistance=110,
                                      atr_val=4, k_stop=1.0, k_target=2.0)
    assert close_support["target1"] == 92  # ATR floor wins over the too-near support(97)
    assert close_support["risk_reward"] == 2.0


def test_every_plan_meets_the_rr_floor():
    for bias in ("Long", "Short"):
        plan = build_trade_plan(bias, price=100, support=99, resistance=101,
                                 atr_val=3, k_stop=1.0, k_target=2.0)
        assert plan["risk_reward"] >= 2.0
