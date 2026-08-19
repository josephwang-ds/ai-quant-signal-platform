"""Daily OHLCV.

Stooq serves free, keyless daily bars, which keeps the project runnable by anyone
who clones it -- no API key, no signup, no vendor account. Bars are cached to
parquet on first fetch.

Prices are adjusted for splits and dividends by the vendor. That adjustment is
itself a mild point-in-time compromise: today's adjusted history is not what a
trader saw at the time. It does not bias this study, because both the event
return and its market benchmark come from the same adjusted series and the
adjustment is multiplicative -- but it is the kind of thing worth naming rather
than discovering later.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}.us&i=d"

COLUMNS = ["ticker", "date", "open", "high", "low", "close", "volume"]


def fetch_daily(ticker: str, *, cache_dir: Path = Path("data/cache/prices"),
                timeout: int = 30) -> pd.DataFrame:
    """One issuer's full daily history, cached to parquet."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{ticker.upper()}.parquet"
    if cached.exists():
        return pd.read_parquet(cached)

    response = requests.get(STOOQ_URL.format(symbol=ticker.lower()), timeout=timeout)
    response.raise_for_status()
    raw = pd.read_csv(io.StringIO(response.text))
    if raw.empty or "Date" not in raw.columns:
        raise ValueError(f"no price history returned for {ticker}")

    frame = pd.DataFrame({
        "ticker": ticker.upper(),
        "date": pd.to_datetime(raw["Date"]).dt.date,
        "open": raw["Open"].astype(float),
        "high": raw["High"].astype(float),
        "low": raw["Low"].astype(float),
        "close": raw["Close"].astype(float),
        "volume": raw["Volume"].astype(float),
    })
    frame.to_parquet(cached, index=False)
    return frame


def load_prices(path: str | Path) -> pd.DataFrame:
    """Read a consolidated price panel and enforce its contract."""
    path = Path(path)
    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"price panel {path} is missing columns: {sorted(missing)}")
    frame["date"] = pd.to_datetime(frame["date"]).dt.date
    frame = frame.sort_values(["ticker", "date"]).reset_index(drop=True)

    dup = frame.duplicated(["ticker", "date"])
    if dup.any():
        raise ValueError(f"{int(dup.sum())} duplicated ticker/date rows in {path}")
    return frame[COLUMNS]


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Close-to-close simple returns, plus the volume baseline used for surprise.

    The rolling median is shifted by one session so that a day's own volume never
    contributes to the baseline it is measured against.
    """
    frame = prices.sort_values(["ticker", "date"]).copy()
    grouped = frame.groupby("ticker", sort=False)
    frame["ret"] = grouped["close"].pct_change()
    frame["volume_median_60"] = (
        grouped["volume"]
        .transform(lambda s: s.shift(1).rolling(60, min_periods=20).median())
    )
    return frame
