"""Yahoo Finance historical adapter for research execution (Infrastructure)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    MarketDataValidationError,
    NormalizedMarketSeries,
    series_actual_bounds,
    utc_now_iso,
    validate_normalized_ohlcv,
)
from app.research_execution.price_cache import PriceCache


YAHOO_ADJUSTMENT = "auto_adjust"

OHLC_COLUMNS = ("open", "high", "low", "close")


def _drop_incomplete_ohlc_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Remove rows with missing OHLC values.

    yfinance may include the current session day with NaN OHLC before the bar
    completes. Those rows must be dropped before contract validation.
    """
    present = [col for col in OHLC_COLUMNS if col in df.columns]
    if not present:
        return df, 0
    before = len(df)
    cleaned = df.dropna(subset=present).reset_index(drop=True)
    return cleaned, before - len(cleaned)


class YahooFinanceMarketDataAdapter:
    """
    Research/demo historical-data adapter via yfinance.

    Not exchange-grade. Replaceable through MarketDataPort (Polygon, Tiingo, …).
    """

    name = "yahoo"
    source_label = "Yahoo Finance"

    def __init__(
        self,
        cache: PriceCache | None = None,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.cache = cache or PriceCache()
        self.timeout_seconds = timeout_seconds

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        symbol = symbol.upper().strip()
        key = self.cache.make_key(
            self.name, symbol, start_date, end_date, "1d", YAHOO_ADJUSTMENT
        )

        cached, _ = self.cache.get(key, allow_stale=False)
        if cached is not None:
            return cached

        try:
            series = self._download(symbol, start_date, end_date)
            self.cache.put(key, series)
            return series
        except Exception as exc:
            stale, is_stale = self.cache.get(key, allow_stale=True)
            if stale is not None and is_stale:
                from dataclasses import replace

                labeled = NormalizedMarketSeries(
                    symbol=stale.symbol,
                    frame=stale.frame,
                    provenance=replace(
                        stale.provenance,
                        cache_hit=True,
                        cache_stale=True,
                    ),
                    warnings=list(stale.warnings)
                    + [
                        "Serving labeled stale cache after live provider failure."
                    ],
                )
                return labeled
            if isinstance(exc, (MarketDataUnavailableError, MarketDataValidationError)):
                raise
            raise MarketDataUnavailableError(
                f"Yahoo Finance unavailable for {symbol}: {exc}"
            ) from exc

    def _download(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None,
    ) -> NormalizedMarketSeries:
        download_kwargs: dict = {
            "start": start_date,
            "auto_adjust": True,
            "progress": False,
            "threads": False,
            "timeout": self.timeout_seconds,
        }
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            download_kwargs["end"] = (end_dt + timedelta(days=1)).isoformat()

        try:
            raw = yf.download(symbol, **download_kwargs)
        except Exception as exc:  # noqa: BLE001 — map to unavailable
            message = str(exc).lower()
            if (
                isinstance(exc, TimeoutError)
                or "timeout" in message
                or "timed out" in message
            ):
                raise MarketDataUnavailableError(
                    f"Yahoo Finance timed out for {symbol} "
                    f"after {self.timeout_seconds}s."
                ) from exc
            raise MarketDataUnavailableError(
                f"Yahoo Finance request failed for {symbol}: {exc}"
            ) from exc

        if raw is None or raw.empty:
            raise MarketDataUnavailableError(
                f"No price data returned for ticker '{symbol}'."
            )

        df = raw.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        rename_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adjusted_close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename_map)
        if "adjusted_close" not in df.columns:
            df["adjusted_close"] = df["close"]
        df["symbol"] = symbol
        df, dropped = _drop_incomplete_ohlc_rows(df)
        warnings: list[str] = []
        if dropped:
            warnings.append(
                f"Dropped {dropped} incomplete Yahoo Finance bar(s) with missing OHLC "
                "before validation."
            )
        df = validate_normalized_ohlcv(df, symbol=symbol)

        actual_start, actual_end = series_actual_bounds(df)
        retrieved_at = utc_now_iso()
        provenance = DataProvenance(
            provider=self.name,
            symbol=symbol,
            source=self.source_label,
            retrieved_at=retrieved_at,
            requested_start=start_date,
            requested_end=end_date,
            actual_start=actual_start,
            actual_end=actual_end,
            interval="1d",
            cache_hit=False,
            cache_stale=False,
            currency="USD",
            adapter=self.name,
            canonical_symbol=symbol,
            provider_symbol=symbol,
            adjustment=YAHOO_ADJUSTMENT,
            row_count=len(df),
        )
        warnings.extend(
            [
                "Yahoo Finance / yfinance is suitable for research and portfolio demos "
                "only — not an exchange-grade production feed.",
                "Provider timeout is enforced via yfinance download(timeout=…).",
                f"Yahoo prices use yfinance auto_adjust ({YAHOO_ADJUSTMENT}).",
            ]
        )
        return NormalizedMarketSeries(
            symbol=symbol,
            frame=df,
            provenance=provenance,
            warnings=warnings,
        )
