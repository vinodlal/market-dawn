"""
kite_utils.py — shared Kite Connect helpers.

Central place for:
  - building an authenticated KiteConnect client from an access token, and
  - resolving the 5 data sources BY NAME from a fresh `kite.instruments()` dump.

Instrument tokens roll over at expiry, so everything here resolves dynamically.
Nothing is hardcoded except the human-readable names / exchanges.
"""

import json
import os
from datetime import date, datetime

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "kite_access_token.json")

# Source identifiers used across the codebase.
SRC_BANKNIFTY = "banknifty"
SRC_VIX = "vix"
SRC_CRUDE = "crude_proxy_mcx"
SRC_USDINR = "usdinr_proxy_futures"
SRC_OPTIONS = "banknifty_option_chain"


def load_access_token():
    """Read the access token from env (KITE_ACCESS_TOKEN) or kite_access_token.json."""
    tok = os.environ.get("KITE_ACCESS_TOKEN")
    if tok:
        return tok.strip()
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)["access_token"]
    raise SystemExit(
        "No access token found. Run generate_token.py first, or set KITE_ACCESS_TOKEN."
    )


def make_kite(api_key=None, access_token=None):
    """Return an authenticated KiteConnect client."""
    from kiteconnect import KiteConnect

    api_key = api_key or os.environ.get("KITE_API_KEY")
    if not api_key:
        raise SystemExit("KITE_API_KEY not set.")
    access_token = access_token or load_access_token()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite


def _as_date(value):
    """kite.instruments() returns expiry as datetime.date or '' — normalize."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return None


def _nearest_future(instruments, name, today=None):
    """Pick the nearest not-yet-expired FUT contract for `name`."""
    today = today or date.today()
    futs = [
        i for i in instruments
        if i.get("name") == name and i.get("instrument_type") == "FUT"
    ]
    dated = [(exp, i) for i in futs if (exp := _as_date(i.get("expiry"))) is not None]
    upcoming = sorted([(e, i) for e, i in dated if e >= today], key=lambda x: x[0])
    if upcoming:
        return upcoming[0][1]
    # fall back to the latest available if nothing looks "upcoming"
    if dated:
        return sorted(dated, key=lambda x: x[0])[-1][1]
    return None


def resolve_index(kite, tradingsymbol):
    """Resolve an NSE index (e.g. 'NIFTY BANK', 'INDIA VIX') to its instrument row."""
    for i in kite.instruments("NSE"):
        if i.get("tradingsymbol") == tradingsymbol and i.get("segment") == "INDICES":
            return i
    return None


def resolve_crude(kite, today=None):
    """Nearest-month MCX CRUDEOIL future (Brent proxy)."""
    return _nearest_future(kite.instruments("MCX"), "CRUDEOIL", today)


def resolve_usdinr(kite, today=None):
    """Nearest-month CDS USDINR future."""
    return _nearest_future(kite.instruments("CDS"), "USDINR", today)


def resolve_option_chain(kite, today=None):
    """
    Return (expiry_date, [option instrument rows]) for the nearest BANKNIFTY expiry.
    Includes every CE/PE at that expiry; callers filter by strike window.
    """
    today = today or date.today()
    opts = [
        i for i in kite.instruments("NFO")
        if i.get("name") == "BANKNIFTY" and i.get("instrument_type") in ("CE", "PE")
    ]
    dated = [(exp, i) for i in opts if (exp := _as_date(i.get("expiry"))) is not None]
    upcoming = [e for e, _ in dated if e >= today]
    if not upcoming:
        return None, []
    nearest = min(upcoming)
    chain = [i for e, i in dated if e == nearest]
    return nearest, chain
