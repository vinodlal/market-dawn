"""
verify_sources.py — Section 0 gate. RUN THIS FIRST.

Confirms the 5 data sources actually work for THIS Kite Connect account before
any pipeline code is trusted. Resolves each source by name from a fresh
kite.instruments() dump and attempts a small historical_data()/quote() call.
Prints PASS/FAIL per source and exits non-zero if any fail.

Usage:
    # 1) create a fresh access token (needs the 5 KITE_* secrets in env)
    python scripts/generate_token.py
    # 2) verify
    python scripts/verify_sources.py

If a source FAILs, the usual causes are:
  - the Historical Data API add-on is not active on this subscription,
  - the account lacks F&O / currency / commodity segment permission in Console,
  - the instrument name changed.
Check Kite Connect Console segment settings before debugging code.
"""

import sys
from datetime import date, timedelta

import kite_utils as ku


def _hist(kite, token, days=5):
    to_d = date.today()
    from_d = to_d - timedelta(days=days + 10)  # pad for weekends/holidays
    return kite.historical_data(token, from_d, to_d, "day")


def _check(label, fn):
    try:
        detail = fn()
        print(f"PASS  {label}: {detail}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  {label}: {type(exc).__name__}: {exc}")
        return False


def check_banknifty(kite):
    inst = ku.resolve_index(kite, "NIFTY BANK")
    if not inst:
        raise RuntimeError("NIFTY BANK not found in NSE instruments")
    rows = _hist(kite, inst["instrument_token"])
    return f"token={inst['instrument_token']}, {len(rows)} daily candles, last close={rows[-1]['close']}"


def check_vix(kite):
    inst = ku.resolve_index(kite, "INDIA VIX")
    if not inst:
        raise RuntimeError("INDIA VIX not found in NSE instruments")
    rows = _hist(kite, inst["instrument_token"])
    return f"token={inst['instrument_token']}, {len(rows)} daily candles, last={rows[-1]['close']}"


def check_crude(kite):
    inst = ku.resolve_crude(kite)
    if not inst:
        raise RuntimeError("No MCX CRUDEOIL future resolved")
    rows = _hist(kite, inst["instrument_token"])
    return (f"{inst['tradingsymbol']} exp={inst['expiry']}, "
            f"{len(rows)} candles, last={rows[-1]['close']}")


def check_usdinr(kite):
    inst = ku.resolve_usdinr(kite)
    if not inst:
        raise RuntimeError("No CDS USDINR future resolved")
    rows = _hist(kite, inst["instrument_token"])
    return (f"{inst['tradingsymbol']} exp={inst['expiry']}, "
            f"{len(rows)} candles, last={rows[-1]['close']}")


def check_options(kite):
    expiry, chain = ku.resolve_option_chain(kite)
    if not chain:
        raise RuntimeError("No BANKNIFTY option chain resolved")
    # quote() a small sample to confirm OI access works.
    sample = [f"NFO:{i['tradingsymbol']}" for i in chain[:5]]
    q = kite.quote(sample)
    return f"expiry={expiry}, {len(chain)} strikes(CE+PE), sample quotes ok: {len(q)}"


def main():
    kite = ku.make_kite()
    checks = [
        ("NSE:NIFTY BANK", lambda: check_banknifty(kite)),
        ("NSE:INDIA VIX", lambda: check_vix(kite)),
        ("MCX:CRUDEOIL (near future)", lambda: check_crude(kite)),
        ("CDS:USDINR (near future)", lambda: check_usdinr(kite)),
        ("NFO BANKNIFTY option chain", lambda: check_options(kite)),
    ]
    results = [_check(label, fn) for label, fn in checks]
    print("-" * 60)
    passed = sum(results)
    print(f"{passed}/{len(results)} sources PASS")
    if passed != len(results):
        print("Do NOT proceed to the pipeline until all 5 sources PASS.")
        sys.exit(1)
    print("All sources verified. Safe to run the daily pipeline.")


if __name__ == "__main__":
    main()
