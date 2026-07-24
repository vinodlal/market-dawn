"""Daily paper-trading cycle: settle open trades against today's actual close,
then open new trades from today's live signals across the tracked universe.

Run ONCE per trading day, after NSE close (~16:00 IST) so today's OHLC is
final. Intended for Windows Task Scheduler (desktop-based automation, per
the decision to hold cloud hosting until accuracy work is further along).

Tracks every stock's directional call for accuracy validation regardless of
F&O availability — core.engine.stock.analyze_stock() only fills
strategies.futures when has_futures=True (correct for the UI, which
shouldn't imply futures tradeability that doesn't exist), so this script
builds its own tracking trade plan directly from the signal's price/levels/
ATR, independent of F&O status. Short calls on cash-only stocks aren't
realistically tradeable by a retail investor, but for measuring whether the
DIRECTIONAL CALL was right, tracking them anyway has value.

Run:  python -m core.paper.run_daily
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from ..engine.futures import analyze_futures
from ..engine.signal import DEFAULT_FUTURES_WEIGHTS, DEFAULT_WEIGHTS
from ..engine.signal import analyze as analyze_signal
from ..features import momentum as momentum_mod
from ..providers.kite_provider import KiteProvider
from ..providers.public_provider import PublicProvider
from ..trade_plan.plan import build_trade_plan
from ..universe import drivers_for
from .ledger import get_open_trades, open_trade, settle_trades
from .scoreboard import compute_scoreboard

IST = ZoneInfo("Asia/Kolkata")
HISTORY_DAYS = 400

FUTURES_UNIVERSE = ["BANKNIFTY", "NIFTY"]
STOCK_BASKET = ["HDFCBANK", "ICICIBANK", "SBIN", "TCS", "INFY", "RELIANCE", "MARUTI", "SUNPHARMA"]


def _bar_lookup(kp: KiteProvider, symbols: list[str]) -> dict:
    lookup = {}
    for sym in symbols:
        df = kp.daily_candles(sym, date.today() - timedelta(days=10), date.today())
        if df.empty:
            continue
        last = df.iloc[-1]
        lookup[sym] = {"high": float(last["high"]), "low": float(last["low"]), "close": float(last["close"])}
    return lookup


def _open_futures_trades(kp: KiteProvider, pp: PublicProvider, vix_df: pd.DataFrame,
                          start: date, end: date) -> list[dict]:
    opened = []
    for name in FUTURES_UNIVERSE:
        if get_open_trades(symbol=name):
            continue  # already have an open position -- don't stack duplicates
        df = kp.daily_candles(name, start, end)
        if df.empty:
            continue
        future_quote, spot_quote = kp.future_quote(name), kp.quote(name)
        drivers = {n: pp.daily_candles(n, start, end) for n in drivers_for(name)}
        sig = analyze_futures(name, df, future_quote=future_quote, spot_quote=spot_quote,
                               vix_df=vix_df, drivers=drivers, weights=DEFAULT_FUTURES_WEIGHTS)
        if sig["bias"] == "Neutral" or not sig.get("trade_plan"):
            continue
        tid = open_trade(name, "future", sig["bias"], sig["trade_plan"],
                          strategy="daily_auto_futures", predicted_score=sig["score"],
                          predicted_confidence=sig["confidence"])
        opened.append({"id": tid, "symbol": name, "bias": sig["bias"], "score": sig["score"]})
    return opened


def _open_stock_trades(kp: KiteProvider, pp: PublicProvider, vix_df: pd.DataFrame,
                        start: date, end: date) -> list[dict]:
    opened = []
    for sym in STOCK_BASKET:
        if get_open_trades(symbol=sym):
            continue  # already have an open position -- don't stack duplicates
        df = kp.daily_candles(sym, start, end)
        if df.empty:
            continue
        drivers = {n: pp.daily_candles(n, start, end) for n in drivers_for(sym)}
        sig = analyze_signal(sym, "equity", df, vix_df=vix_df, drivers=drivers, weights=DEFAULT_WEIGHTS)
        if sig["bias"] == "Neutral":
            continue
        atr_series = momentum_mod.atr(df)
        atr_val = float(atr_series.iloc[-1]) if pd.notna(atr_series.iloc[-1]) else sig["price"] * 0.01
        plan = build_trade_plan(sig["bias"], price=sig["price"], support=sig["levels"]["support"],
                                 resistance=sig["levels"]["resistance"], atr_val=atr_val)
        if not plan:
            continue
        tid = open_trade(sym, "equity", sig["bias"], plan, strategy="daily_auto_stock",
                          predicted_score=sig["score"], predicted_confidence=sig["confidence"])
        opened.append({"id": tid, "symbol": sym, "bias": sig["bias"], "score": sig["score"]})
    return opened


def run() -> dict:
    kp, pp = KiteProvider(), PublicProvider()
    all_symbols = FUTURES_UNIVERSE + STOCK_BASKET

    closed_ids = settle_trades(_bar_lookup(kp, all_symbols), max_days=10)

    start, end = date.today() - timedelta(days=HISTORY_DAYS), date.today()
    vix_df = kp.daily_candles("INDIAVIX", start, end)
    opened = _open_futures_trades(kp, pp, vix_df, start, end) + _open_stock_trades(kp, pp, vix_df, start, end)

    return {
        "date": datetime.now(IST).isoformat(),
        "closed_trade_ids": closed_ids,
        "opened_trades": opened,
        "open_trades_now": len(get_open_trades()),
        "scoreboard": compute_scoreboard(),
    }


if __name__ == "__main__":
    result = run()
    print(f"Daily paper-trading cycle: {result['date']}")
    print(f"  Closed {len(result['closed_trade_ids'])} trades")
    print(f"  Opened {len(result['opened_trades'])} new trades:")
    for o in result["opened_trades"]:
        print(f"    {o['symbol']}: {o['bias']} (score {o['score']})")
    print(f"  Total open trades: {result['open_trades_now']}")
    print(f"  Scoreboard: {result['scoreboard']}")
