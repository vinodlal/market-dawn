from core.features.fibonacci import extension_levels, retracement_levels


def test_retracement_levels_known_values():
    levels = retracement_levels(swing_low=100, swing_high=200)
    assert levels[0.0] == 200      # ratio 0 -> the high
    assert levels[1.0] == 100      # ratio 1 -> the low
    assert levels[0.5] == 150      # midpoint
    assert levels[0.618] == 200 - 0.618 * 100


def test_extension_levels_up_direction():
    levels = extension_levels(swing_low=100, swing_high=200, direction="up")
    assert levels[1.618] == 200 + 0.618 * 100  # 261.8


def test_extension_levels_down_direction():
    levels = extension_levels(swing_low=100, swing_high=200, direction="down")
    assert levels[1.618] == 100 - 0.618 * 100  # 38.2
