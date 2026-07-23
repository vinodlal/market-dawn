"""Public/free market data (yfinance).

Used as (a) the independent reference the accuracy gate compares Kite against,
and (b) a proxy feed for instruments outside the Kite plan. Values are labelled
`source="public"`, may be slightly delayed, and are never used for execution.
"""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import yfinance as yf

from ..universe import IST, resolve
from .base import OHLCV_COLS, MarketDataProvider


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=OHLCV_COLS)
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    tscol = "date" if "date" in df.columns else (
        "datetime" if "datetime" in df.columns else df.columns[0])
    ts = pd.to_datetime(df[tscol])
    ts = ts.dt.tz_localize(IST) if ts.dt.tz is None else ts.dt.tz_convert(IST)
    out = pd.DataFrame({
        "ts": ts,
        "open": df["open"].astype(float),
        "high": df["high"].astype(float),
        "low": df["low"].astype(float),
        "close": df["close"].astype(float),
        "volume": df.get("volume", 0),
    })
    return out.dropna(subset=["close"]).sort_values("ts").reset_index(drop=True)[OHLCV_COLS]


class PublicProvider(MarketDataProvider):
    name = "public"

    def _yf(self, symbol: str) -> str:
        inst = resolve(symbol)
        if not inst.yf:
            raise ValueError(f"No public (yfinance) symbol for {symbol}")
        return inst.yf

    def daily_candles(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        df = yf.Ticker(self._yf(symbol)).history(
            start=str(start), end=str(end), interval="1d", auto_adjust=False)
        return _standardize(df)

    def intraday_candles(self, symbol, interval, start, end) -> pd.DataFrame:
        df = yf.Ticker(self._yf(symbol)).history(
            start=str(start), end=str(end), interval=interval, auto_adjust=False)
        return _standardize(df)

    def quote(self, symbol: str) -> dict:
        fi = yf.Ticker(self._yf(symbol)).fast_info
        return {
            "symbol": symbol,
            "source": "public",
            "last_price": float(fi.last_price),
            "prev_close": float(fi.previous_close),
            "ts": datetime.now().astimezone().isoformat(),
        }
