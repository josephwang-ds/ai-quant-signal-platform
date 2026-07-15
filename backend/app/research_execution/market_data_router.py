"""Asset-class market-data router behind MarketDataPort."""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from app.research_execution.akshare_adapter import AkShareMarketDataAdapter
from app.research_execution.market_data_port import (
    MarketDataPort,
    MarketDataValidationError,
    NormalizedMarketSeries,
    series_actual_bounds,
)
from app.research_execution.price_cache import PriceCache
from app.research_execution.symbol import (
    SymbolDescriptor,
    UnsupportedSymbolError,
    classify_symbol,
    resolve_provider,
)
from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter

YAHOO_ADJUSTMENT = "auto_adjust"


class _DailyOhlcvAdapter(Protocol):
    name: str

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries: ...


class MarketDataRouter:
    """
    Routes symbols to Yahoo or AkShare behind one MarketDataPort contract.

    No automatic cross-provider failover.
    """

    def __init__(
        self,
        *,
        yahoo: YahooFinanceMarketDataAdapter | None = None,
        akshare: AkShareMarketDataAdapter | None = None,
        cache: PriceCache | None = None,
        provider_override: str | None = None,
    ) -> None:
        shared_cache = cache or PriceCache()
        self.yahoo = yahoo or YahooFinanceMarketDataAdapter(cache=shared_cache)
        self.akshare = akshare or AkShareMarketDataAdapter(cache=shared_cache)
        self._provider_override = provider_override

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        try:
            descriptor = classify_symbol(symbol)
            provider = resolve_provider(descriptor, self._provider_override)
        except UnsupportedSymbolError as exc:
            raise MarketDataValidationError(str(exc)) from exc

        adapter = self._select_adapter(provider)
        series = adapter.get_daily_ohlcv(descriptor.canonical_symbol, start_date, end_date)
        return self._finalize(series, descriptor, adapter.name, provider)

    def _select_adapter(self, provider: str) -> _DailyOhlcvAdapter:
        if provider == "yahoo":
            return self.yahoo
        if provider == "akshare":
            return self.akshare
        raise MarketDataValidationError(f"Unsupported provider '{provider}'.")

    @staticmethod
    def _finalize(
        series: NormalizedMarketSeries,
        descriptor: SymbolDescriptor,
        adapter_name: str,
        routed_provider: str,
    ) -> NormalizedMarketSeries:
        actual_start, actual_end = series_actual_bounds(series.frame)
        adjustment = (
            series.provenance.adjustment
            if series.provenance.adjustment
            else (YAHOO_ADJUSTMENT if routed_provider == "yahoo" else "qfq")
        )
        provenance = replace(
            series.provenance,
            provider=routed_provider,
            adapter=adapter_name,
            symbol=descriptor.canonical_symbol,
            requested_symbol=descriptor.input_symbol,
            canonical_symbol=descriptor.canonical_symbol,
            provider_symbol=descriptor.provider_symbol,
            asset_class=descriptor.asset_class,
            exchange=descriptor.exchange,
            currency=descriptor.currency or series.provenance.currency,
            adjustment=adjustment,
            row_count=len(series.frame),
            actual_start=actual_start,
            actual_end=actual_end,
        )
        return NormalizedMarketSeries(
            symbol=descriptor.canonical_symbol,
            frame=series.frame,
            provenance=provenance,
            warnings=series.warnings,
        )


def build_default_market_data_port() -> MarketDataPort:
    """Production router wiring for research execution and validation."""
    return MarketDataRouter()
