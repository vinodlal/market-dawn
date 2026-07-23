import pandas as pd

from core.features.oi import (
    LONG_BUILDUP, LONG_UNWINDING, NEUTRAL, SHORT_BUILDUP, SHORT_COVERING,
    buildup_series, classify_buildup,
)  # noqa: F401 (SHORT_COVERING used in classify_buildup truth-table test)

# price=[100,102,99,97,100], oi=[1000,1100,1150,1100,1150]
#   i=1: price +2.000%, oi +10.000%  -> both up   -> long_buildup
#   i=2: price -2.941%, oi  +4.545%  -> down/up   -> short_buildup
#   i=3: price -2.020%, oi  -4.348%  -> both down -> long_unwinding
#   i=4: price +3.093%, oi  +4.545%  -> both up   -> long_buildup


def test_classify_buildup_truth_table():
    assert classify_buildup(2.0, 3.0) == LONG_BUILDUP      # price up, OI up
    assert classify_buildup(-2.0, 3.0) == SHORT_BUILDUP    # price down, OI up
    assert classify_buildup(-2.0, -3.0) == LONG_UNWINDING  # price down, OI down
    assert classify_buildup(2.0, -3.0) == SHORT_COVERING   # price up, OI down
    assert classify_buildup(0.001, 0.001) == NEUTRAL       # both flat


def test_buildup_series_matches_pointwise_classification():
    price = pd.Series([100, 102, 99, 97, 100])
    oi = pd.Series([1000, 1100, 1150, 1100, 1150])
    out = buildup_series(price, oi)
    assert pd.isna(out.iloc[0])  # no prior bar to diff against
    assert out.iloc[1] == LONG_BUILDUP     # price +2.0%, OI +10.0%
    assert out.iloc[2] == SHORT_BUILDUP    # price -2.9%, OI +4.5%
    assert out.iloc[3] == LONG_UNWINDING   # price -2.0%, OI -4.3%
    assert out.iloc[4] == LONG_BUILDUP     # price +3.1%, OI +4.5%
