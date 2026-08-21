"""Daily OHLCV.

Free price data has no service level, so this tries more than one source rather
than betting the pipeline on any single one. Stooq was the original choice for
being keyless -- and promptly started answering 404 for symbols it serves fine in
a browser. yfinance leads now; Stooq stays as a fallback. Neither needs an
account, which is what keeps the project runnable by whoever clones it.

Bars are cached to parquet on first fetch, so a rerun costs nothing.

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

DEFAULT_SOURCES = ("yfinance", "stooq")


class PriceUnavailable(RuntimeError):
    """No configured source would serve this ticker."""


def fetch_daily(ticker: str, *, cache_dir: Path = Path("data/cache/prices"),
                timeout: int = 30,
                sources: tuple[str, ...] = DEFAULT_SOURCES) -> pd.DataFrame:
    """One issuer's full daily history, cached to parquet.

    Sources are tried in order and the first that answers wins. A failure here is
    per-ticker, not fatal: the ingest loop records it and carries on, because one
    delisted symbol must not cost an hour-long pull.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{ticker.upper()}.parquet"
    if cached.exists():
        return pd.read_parquet(cached)

    problems = []
    for source in sources:
        try:
            frame = _SOURCES[source](ticker, timeout)
        except KeyError:
            raise ValueError(f"unknown price source {source!r}; "
                             f"available: {', '.join(_SOURCES)}") from None
        except Exception as error:                              # noqa: BLE001
            problems.append(f"{source}: {error}")
            continue

        if frame is not None and not frame.empty:
            frame.to_parquet(cached, index=False)
            return frame
        problems.append(f"{source}: returned no rows")

    raise PriceUnavailable(f"no price history for {ticker} -- " + "; ".join(problems))


def _from_yfinance(ticker: str, timeout: int) -> pd.DataFrame:
    import yfinance

    raw = yfinance.Ticker(ticker).history(period="max", auto_adjust=True,
                                          raise_errors=True)
    if raw.empty:
        return raw
    raw = raw.reset_index()
    return pd.DataFrame({
        "ticker": ticker.upper(),
        "date": pd.to_datetime(raw["Date"]).dt.date,
        "open": raw["Open"].astype(float),
        "high": raw["High"].astype(float),
        "low": raw["Low"].astype(float),
        "close": raw["Close"].astype(float),
        "volume": raw["Volume"].astype(float),
    })


def _from_stooq(ticker: str, timeout: int) -> pd.DataFrame:
    response = requests.get(STOOQ_URL.format(symbol=ticker.lower()), timeout=timeout)
    response.raise_for_status()
    if "Date" not in response.text[:64]:
        # Stooq answers rate limiting with a 200 and a sentence of prose.
        raise RuntimeError(response.text.strip()[:120] or "empty response")
    raw = pd.read_csv(io.StringIO(response.text))
    return pd.DataFrame({
        "ticker": ticker.upper(),
        "date": pd.to_datetime(raw["Date"]).dt.date,
        "open": raw["Open"].astype(float),
        "high": raw["High"].astype(float),
        "low": raw["Low"].astype(float),
        "close": raw["Close"].astype(float),
        "volume": raw["Volume"].astype(float),
    })


_SOURCES = {"yfinance": _from_yfinance, "stooq": _from_stooq}


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
