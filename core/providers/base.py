"""Provider interface — everything above the data layer is source-agnostic.

Candle frames are standardized to columns OHLCV_COLS with `ts` a tz-aware
Asia/Kolkata timestamp, ascending. Concrete providers (Kite, public) implement
what they support; unsupported calls raise NotImplementedError.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

import pandas as pd

OHLCV_COLS = ["ts", "open", "high", "low", "close", "volume"]


class MarketDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def daily_candles(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Daily OHLCV for [start, end], tz-aware IST, ascending. Columns OHLCV_COLS."""

    def intraday_candles(
        self, symbol: str, interval: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        raise NotImplementedError(f"{self.name} has no intraday_candles")

    @abstractmethod
    def quote(self, symbol: str) -> dict:
        """Latest snapshot: at least symbol, source, last_price, prev_close, ts (IST)."""

    def option_chain(self, symbol: str, expiry: date | None = None) -> dict:
        raise NotImplementedError(f"{self.name} has no option_chain")
