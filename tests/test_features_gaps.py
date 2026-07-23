from core.features.gaps import unfilled_gaps
from tests.conftest import make_df


def test_unfilled_gap_up_detected():
    rows = [
        {"o": 100, "h": 101, "l": 99, "c": 100},   # prev close = 100
        {"o": 105, "h": 106, "l": 104, "c": 105},  # gap up 5% from 100, never revisited
        {"o": 105, "h": 107, "l": 104, "c": 106},
    ]
    df = make_df(rows)
    gaps = unfilled_gaps(df, threshold_pct=0.3)
    assert len(gaps) == 1
    assert gaps[0]["direction"] == "up"
    assert gaps[0]["level"] == 100


def test_gap_filled_is_excluded():
    rows = [
        {"o": 100, "h": 101, "l": 99, "c": 100},
        {"o": 105, "h": 106, "l": 104, "c": 105},  # gap up from 100
        {"o": 105, "h": 106, "l": 99, "c": 104},   # no new gap (opens at prev close);
                                                    # low 99 <= 100 <= high 106 -> fills the first gap
    ]
    df = make_df(rows)
    gaps = unfilled_gaps(df, threshold_pct=0.3)
    assert gaps == []


def test_small_gap_below_threshold_ignored():
    rows = [
        {"o": 100, "h": 101, "l": 99, "c": 100},
        {"o": 100.1, "h": 101, "l": 99, "c": 100},  # 0.1% gap < 0.3% threshold
    ]
    df = make_df(rows)
    assert unfilled_gaps(df, threshold_pct=0.3) == []
