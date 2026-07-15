"""AKShare historical adapter for mainland A-share research execution."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pandas as pd

from app.research_execution.market_data_port import (
    DataProvenance,
    InsufficientHistoryError,
    InvalidProviderResponseError,
    MarketDataUnavailableError,
    MarketDataValidationError,
    NormalizedMarketSeries,
    ProviderNotConfiguredError,
    series_actual_bounds,
    utc_now_iso,
    validate_normalized_ohlcv,
)
from app.research_execution.price_cache import PriceCache
from app.research_execution.symbol import (
    SymbolDescriptor,
    UnsupportedSymbolError,
    classify_symbol,
)

# Default adjustment for mainland A-shares — forward-adjusted (qfq).
# Recorded in provenance; do not mix with incompatible benchmark series.
AKSHARE_ADJUSTMENT_DEFAULT = "qfq"

_AKSHARE_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
}


class AkShareMarketDataAdapter:
    """
    Research Infrastructure adapter for mainland China A-share daily bars.

    Uses ak.stock_zh_a_hist with qfq adjustment by default.
    """

    name = "akshare"
    source_label = "AKShare"

    def __init__(
        self,
        cache: PriceCache | None = None,
        *,
        adjustment: str = AKSHARE_ADJUSTMENT_DEFAULT,
    ) -> None:
        self.cache = cache or PriceCache()
        self.adjustment = adjustment

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        descriptor = classify_symbol(symbol)
        if descriptor.asset_class != "cn_equity":
            raise UnsupportedSymbolError(
                f"AkShare adapter only supports cn_equity symbols; "
                f"got '{descriptor.canonical_symbol}' ({descriptor.asset_class})."
            )

        key = self.cache.make_key(
            self.name,
            descriptor.canonical_symbol,
            start_date,
            end_date,
            "1d",
            self.adjustment,
        )

        cached, _ = self.cache.get(key, allow_stale=False)
        if cached is not None:
            return self._with_descriptor(cached, descriptor)

        try:
            series = self._download(descriptor, start_date, end_date)
            self.cache.put(key, series)
            return series
        except Exception as exc:
            stale, is_stale = self.cache.get(key, allow_stale=True)
            if stale is not None and is_stale:
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
                return self._with_descriptor(labeled, descriptor)
            if isinstance(
                exc,
                (
                    MarketDataUnavailableError,
                    MarketDataValidationError,
                    UnsupportedSymbolError,
                ),
            ):
                raise
            raise MarketDataUnavailableError(
                f"AKShare unavailable for {descriptor.canonical_symbol}: {exc}"
            ) from exc

    def _download(
        self,
        descriptor: SymbolDescriptor,
        start_date: str,
        end_date: str | None,
    ) -> NormalizedMarketSeries:
        try:
            import akshare as ak
        except ImportError as exc:
            raise ProviderNotConfiguredError(
                "AKShare is not installed. Add `akshare` to backend requirements."
            ) from exc

        end_value = end_date or datetime.utcnow().strftime("%Y-%m-%d")
        try:
            raw = ak.stock_zh_a_hist(
                symbol=descriptor.provider_symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_value.replace("-", ""),
                adjust=self.adjustment,
            )
        except Exception as exc:
            raise MarketDataUnavailableError(
                f"AKShare request failed for {descriptor.canonical_symbol}: {exc}"
            ) from exc

        if raw is None or raw.empty:
            raise MarketDataUnavailableError(
                f"No AKShare data returned for '{descriptor.canonical_symbol}'."
            )

        missing_cols = [c for c in _AKSHARE_COLUMN_MAP if c not in raw.columns]
        if missing_cols:
            raise InvalidProviderResponseError(
                f"AKShare response missing columns {missing_cols} for "
                f"'{descriptor.canonical_symbol}'."
            )

        df = raw.rename(columns=_AKSHARE_COLUMN_MAP)
        df = df.drop_duplicates(subset=["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df["symbol"] = descriptor.canonical_symbol
        df = validate_normalized_ohlcv(df, symbol=descriptor.canonical_symbol)

        df = df[df["date"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["date"] <= pd.Timestamp(end_date)]
        df = df.reset_index(drop=True)
        if df.empty:
            raise InsufficientHistoryError(
                f"No AKShare rows for '{descriptor.canonical_symbol}' "
                f"in range {start_date} to {end_date or 'latest'}."
            )

        actual_start, actual_end = series_actual_bounds(df)
        provenance = DataProvenance(
            provider=self.name,
            symbol=descriptor.canonical_symbol,
            source=self.source_label,
            retrieved_at=utc_now_iso(),
            requested_start=start_date,
            requested_end=end_date,
            actual_start=actual_start,
            actual_end=actual_end,
            interval="1d",
            cache_hit=False,
            cache_stale=False,
            currency=descriptor.currency,
            adapter=self.name,
            requested_symbol=descriptor.input_symbol,
            canonical_symbol=descriptor.canonical_symbol,
            provider_symbol=descriptor.provider_symbol,
            asset_class=descriptor.asset_class,
            exchange=descriptor.exchange,
            adjustment=self.adjustment,
            row_count=len(df),
        )
        warnings: list[str] = [
            "AKShare is a free community data source suitable for research demos "
            "only — not an exchange-grade production feed.",
            f"Mainland A-share prices use {self.adjustment} adjustment by default.",
        ]
        return NormalizedMarketSeries(
            symbol=descriptor.canonical_symbol,
            frame=df,
            provenance=provenance,
            warnings=warnings,
        )

    @staticmethod
    def _with_descriptor(
        series: NormalizedMarketSeries,
        descriptor: SymbolDescriptor,
    ) -> NormalizedMarketSeries:
        return NormalizedMarketSeries(
            symbol=descriptor.canonical_symbol,
            frame=series.frame,
            provenance=replace(
                series.provenance,
                symbol=descriptor.canonical_symbol,
                requested_symbol=descriptor.input_symbol or series.provenance.requested_symbol,
                canonical_symbol=descriptor.canonical_symbol,
                provider_symbol=descriptor.provider_symbol,
                asset_class=descriptor.asset_class,
                exchange=descriptor.exchange,
                currency=descriptor.currency,
            ),
            warnings=series.warnings,
        )
