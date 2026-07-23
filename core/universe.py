"""Instrument registry: logical name -> per-provider symbols + metadata.

Kite tradingsymbols and lot sizes are refreshed from the Kite instruments dump
in M1 (kept as None here until then, to avoid asserting stale values). yfinance
symbols are used by the public provider and the accuracy cross-check.
"""
from __future__ import annotations

from dataclasses import dataclass

IST = "Asia/Kolkata"


@dataclass(frozen=True)
class Instrument:
    name: str
    kind: str                 # "index" | "global" | "equity"
    yf: str | None            # yfinance symbol (public provider / cross-check)
    kite: str | None          # kite "EXCH:TRADINGSYMBOL"
    lot_size: int | None = None


INDICES: dict[str, Instrument] = {
    "BANKNIFTY": Instrument("BANKNIFTY", "index", "^NSEBANK", "NSE:NIFTY BANK"),
    "NIFTY": Instrument("NIFTY", "index", "^NSEI", "NSE:NIFTY 50"),
    "INDIAVIX": Instrument("INDIAVIX", "index", "^INDIAVIX", "NSE:INDIA VIX"),
}

# Overnight / global drivers. GIFT Nifty has no clean free feed — handled by a
# dedicated public source later; kept here as a known gap.
GLOBAL: dict[str, Instrument] = {
    "BRENT": Instrument("BRENT", "global", "BZ=F", None),
    "USDINR": Instrument("USDINR", "global", "INR=X", "CDS:USDINR"),
    "GIFTNIFTY": Instrument("GIFTNIFTY", "global", None, None),
}


def equity(symbol: str) -> Instrument:
    s = symbol.upper().strip()
    return Instrument(s, "equity", f"{s}.NS", f"NSE:{s}")


def resolve(name: str) -> Instrument:
    n = name.upper().strip()
    return INDICES.get(n) or GLOBAL.get(n) or equity(n)


SNAPSHOT = ["NIFTY", "GIFTNIFTY", "BANKNIFTY", "BRENT", "USDINR", "INDIAVIX"]
