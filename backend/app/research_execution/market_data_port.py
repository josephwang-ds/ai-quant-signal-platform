"""
Research Execution — Application-facing market-data contract.

Infrastructure adapters implement MarketDataPort.
Domain/Application code must not import yfinance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Protocol, Sequence

import pandas as pd


REQUIRED_COLUMNS = (
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


@dataclass(frozen=True)
class DataProvenance:
    provider: str
    symbol: str
    source: str
    retrieved_at: str
    requested_start: str
    requested_end: str | None
    actual_start: str
    actual_end: str
    interval: str = "1d"
    cache_hit: bool = False
    cache_stale: bool = False
    currency: str | None = "USD"


@dataclass
class NormalizedMarketSeries:
    """Normalized OHLCV series with provenance metadata."""

    symbol: str
    frame: pd.DataFrame
    provenance: DataProvenance
    warnings: list[str] = field(default_factory=list)


class MarketDataPort(Protocol):
    """Port for historical market data used by research execution."""

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        """Return a validated, ascending daily OHLCV series."""


class MarketDataError(Exception):
    """Base market-data failure (provider, empty, invalid)."""


class MarketDataValidationError(MarketDataError):
    """Normalized series failed contract validation."""


class MarketDataUnavailableError(MarketDataError):
    """Provider timeout, missing ticker, or empty payload."""


def _to_date_str(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)[:10]
    datetime.strptime(text, "%Y-%m-%d")
    return text


def validate_normalized_ohlcv(frame: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    """
    Validate and normalize an OHLCV frame.

    Raises MarketDataValidationError on contract violations.
    Duplicate dates are rejected (not silently merged).
    """
    if frame is None or frame.empty:
        raise MarketDataValidationError("Market data result is empty.")

    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise MarketDataValidationError(f"Missing required columns: {missing}.")

    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if out["date"].isna().any():
        raise MarketDataValidationError("One or more dates could not be parsed.")

    if out["date"].duplicated().any():
        raise MarketDataValidationError(
            "Duplicate dates detected; duplicates must be handled explicitly."
        )

    for col in ("open", "high", "low", "close"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
        if out[col].isna().any() or (out[col] <= 0).any():
            raise MarketDataValidationError(f"Column '{col}' must be positive and valid.")

    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0)

    if "adjusted_close" not in out.columns:
        out["adjusted_close"] = out["close"]
    else:
        out["adjusted_close"] = pd.to_numeric(out["adjusted_close"], errors="coerce")
        out["adjusted_close"] = out["adjusted_close"].fillna(out["close"])
        if (out["adjusted_close"] <= 0).any():
            raise MarketDataValidationError("adjusted_close must be positive.")

    out["symbol"] = symbol.upper().strip()
    out = out.sort_values("date").reset_index(drop=True)

    dates = out["date"].dt.date.tolist()
    if dates != sorted(dates):
        raise MarketDataValidationError("Dates must be sorted ascending.")
    if len(set(dates)) != len(dates):
        raise MarketDataValidationError("Dates must be unique.")

    return out


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def series_actual_bounds(frame: pd.DataFrame) -> tuple[str, str]:
    start = _to_date_str(frame["date"].iloc[0])
    end = _to_date_str(frame["date"].iloc[-1])
    return start, end
