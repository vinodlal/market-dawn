from core.features.levels import cluster_levels, nearest_levels, pivot_levels, swing_points
from tests.conftest import make_df


def test_pivot_levels_known_values():
    piv = pivot_levels(high=110, low=90, close=100)
    assert piv["pivot"] == 100
    assert piv["r1"] == 110   # 2*100 - 90
    assert piv["s1"] == 90    # 2*100 - 110
    assert piv["r2"] == 120   # 100 + (110-90)
    assert piv["s2"] == 80    # 100 - (110-90)


def test_swing_points_local_extrema():
    # index 2 is a clear local high (105), index 4 a clear local low (95)
    rows = [
        {"o": 100, "h": 101, "l": 99, "c": 100},
        {"o": 100, "h": 103, "l": 99, "c": 102},
        {"o": 102, "h": 105, "l": 101, "c": 104},
        {"o": 104, "h": 104, "l": 96, "c": 97},
        {"o": 97, "h": 98, "l": 95, "c": 96},
        {"o": 96, "h": 99, "l": 96, "c": 98},
        {"o": 98, "h": 100, "l": 97, "c": 99},
    ]
    df = make_df(rows)
    highs, lows = swing_points(df, window=2)
    assert 105 in highs
    assert 95 in lows


def test_nearest_levels():
    support, resistance = nearest_levels(100, [80, 90, 95, 110, 120])
    assert support == 95
    assert resistance == 110


def test_nearest_levels_missing_side():
    support, resistance = nearest_levels(100, [110, 120])
    assert support is None
    assert resistance == 110


def test_cluster_levels_merges_nearby():
    # 100.1 and 100.4 are within 0.6% of each other -> one support cluster, touches=2
    levels = [(100.1, "S"), (100.4, "S"), (150.0, "R")]
    out = cluster_levels(levels, price=120)
    supports = [l for l in out if l["type"] == "support"]
    assert len(supports) == 1
    assert supports[0]["touches"] == 2
    resistances = [l for l in out if l["type"] == "resistance"]
    assert resistances[0]["price"] == 150.0
