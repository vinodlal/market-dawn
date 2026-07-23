from core.features.options import compute_pcr, max_pain, oi_shift, oi_walls


def _chain():
    calls = [
        {"strike": 90, "oi": 100}, {"strike": 95, "oi": 150},
        {"strike": 100, "oi": 500}, {"strike": 105, "oi": 200}, {"strike": 110, "oi": 80},
    ]
    puts = [
        {"strike": 90, "oi": 300}, {"strike": 95, "oi": 400},
        {"strike": 100, "oi": 600}, {"strike": 105, "oi": 120}, {"strike": 110, "oi": 60},
    ]
    return calls, puts


def test_compute_pcr_known_value():
    calls, puts = _chain()
    pcr, atm = compute_pcr(calls, puts, spot=100, atm_window=5)
    call_oi_total = 100 + 150 + 500 + 200 + 80  # all 5 strikes fall in the window
    put_oi_total = 300 + 400 + 600 + 120 + 60
    assert atm == 100
    assert pcr == round(put_oi_total / call_oi_total, 3)


def test_max_pain_known_value():
    # writer payout at each candidate strike:
    #  90:  puts(100@10*600 no wait compute properly below in comments
    calls = [{"strike": 100, "oi": 100}, {"strike": 110, "oi": 500}]
    puts = [{"strike": 100, "oi": 500}, {"strike": 90, "oi": 100}]
    # pain(90)  = calls: max(0,90-100)*100+max(0,90-110)*500=0    | puts: max(0,100-90)*500+max(0,90-90)*100=5000 -> total 5000
    # pain(100) = calls: 0+0=0                                    | puts: max(0,100-100)*500+max(0,90-100)*100=0 -> total 0
    # pain(110) = calls: max(0,110-100)*100+0=1000                | puts: max(0,100-110)*500+0=0 -> total 1000
    assert max_pain(calls, puts) == 100


def test_oi_walls_picks_max_oi_strike():
    calls, puts = _chain()
    walls = oi_walls(calls, puts)
    assert walls["resistance"] == 100  # highest call OI
    assert walls["support"] == 100     # highest put OI


def test_oi_shift_percentage():
    prev = {100: 1000, 105: 500}
    curr = {100: 1100, 105: 400, 110: 200}
    shift = oi_shift(prev, curr)
    assert shift[100] == 10.0
    assert shift[105] == -20.0
    assert shift[110] is None  # no prior OI to compare against
