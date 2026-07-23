"""Momentum & volatility indicators: RSI, MACD, ATR, Bollinger, ADX, Supertrend,
VWAP, volume. New for MarketDawn (not present in v1)."""
from __future__ import annotations

import pandas as pd

from .moving_avg import sma


def _rma(series: pd.Series, window: int) -> pd.Series:
    """Wilder's smoothing, via an EWM approximation (alpha=1/window)."""
    return series.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain, loss = delta.clip(lower=0.0), -delta.clip(upper=0.0)
    avg_gain, avg_loss = _rma(gain, window), _rma(loss, window)
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    out = 100 - (100 / (1 + rs))
    out[(avg_loss == 0) & (avg_gain > 0)] = 100.0
    out[(avg_loss == 0) & (avg_gain == 0)] = 50.0
    return out


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    fast_ema = series.ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_ema = series.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return {"macd": macd_line, "signal": signal_line, "hist": macd_line - signal_line}


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    return _rma(true_range(df), window)


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0) -> dict:
    mid = sma(series, window)
    std = series.rolling(window, min_periods=window).std(ddof=0)
    return {"mid": mid, "upper": mid + num_std * std, "lower": mid - num_std * std}


def adx(df: pd.DataFrame, window: int = 14) -> pd.Series:
    up_move, down_move = df["high"].diff(), -df["low"].diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move.clip(lower=0)
    minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move.clip(lower=0)
    atr_ = atr(df, window)
    plus_di = 100 * _rma(plus_dm, window) / atr_
    minus_di = 100 * _rma(minus_dm, window) / atr_
    denom = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / denom
    return _rma(dx, window)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    hl2 = (df["high"] + df["low"]) / 2
    atr_ = atr(df, period)
    upperband, lowerband = hl2 + multiplier * atr_, hl2 - multiplier * atr_
    close = df["close"].reset_index(drop=True)
    upperband, lowerband = upperband.reset_index(drop=True), lowerband.reset_index(drop=True)
    n = len(df)
    final_upper, final_lower = upperband.copy(), lowerband.copy()
    trend: list[str | None] = [None] * n
    st = [float("nan")] * n
    for i in range(n):
        if pd.isna(atr_.iloc[i]):
            continue
        if i > 0 and not pd.isna(final_upper.iloc[i - 1]):
            if close.iloc[i - 1] <= final_upper.iloc[i - 1]:
                final_upper.iloc[i] = min(upperband.iloc[i], final_upper.iloc[i - 1])
            if close.iloc[i - 1] >= final_lower.iloc[i - 1]:
                final_lower.iloc[i] = max(lowerband.iloc[i], final_lower.iloc[i - 1])
        prev_trend = trend[i - 1] if i > 0 else None
        if prev_trend in (None, "down") and close.iloc[i] > final_upper.iloc[i]:
            trend[i] = "up"
        elif prev_trend in (None, "up") and close.iloc[i] < final_lower.iloc[i]:
            trend[i] = "down"
        else:
            trend[i] = prev_trend or ("up" if close.iloc[i] > hl2.iloc[i] else "down")
        st[i] = final_lower.iloc[i] if trend[i] == "up" else final_upper.iloc[i]
    return pd.DataFrame({"supertrend": st, "trend": trend}, index=df.index)


def vwap(df: pd.DataFrame) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum()
    cum_vol_price = (typical * df["volume"]).cumsum()
    return cum_vol_price / cum_vol.replace(0, float("nan"))


def volume_spike(df: pd.DataFrame, window: int = 20, mult: float = 1.5) -> pd.Series:
    avg_vol = df["volume"].rolling(window, min_periods=window).mean()
    return df["volume"] > (avg_vol * mult)
