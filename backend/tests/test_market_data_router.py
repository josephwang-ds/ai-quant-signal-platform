"""Offline tests for symbol classification and market-data routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import pytest

from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    MarketDataValidationError,
    NormalizedMarketSeries,
    UnsupportedSymbolError,
    utc_now_iso,
    validate_normalized_ohlcv,
)
from app.research_execution.market_data_router import MarketDataRouter
from app.research_execution.price_cache import PriceCache
from app.research_execution.symbol import classify_symbol, resolve_provider


def _sample_frame(symbol: str) -> pd.DataFrame:
    return validate_normalized_ohlcv(
        pd.DataFrame(
            {
                "symbol": [symbol, symbol],
                "date": ["2024-01-02", "2024-01-03"],
                "open": [10.0, 10.5],
                "high": [10.5, 11.0],
                "low": [9.8, 10.2],
                "close": [10.2, 10.8],
                "volume": [1000, 1100],
            }
        ),
        symbol=symbol,
    )


@dataclass
class RecordingAdapter:
    name: str
    calls: list[dict[str, Any]] = field(default_factory=list)
    fail: bool = False

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        self.calls.append(
            {"symbol": symbol, "start_date": start_date, "end_date": end_date}
        )
        if self.fail:
            raise MarketDataUnavailableError(f"{self.name} unavailable for test.")

        frame = _sample_frame(symbol)
        return NormalizedMarketSeries(
            symbol=symbol,
            frame=frame,
            provenance=DataProvenance(
                provider=self.name,
                symbol=symbol,
                source=self.name,
                retrieved_at=utc_now_iso(),
                requested_start=start_date,
                requested_end=end_date,
                actual_start="2024-01-02",
                actual_end="2024-01-03",
                adapter=self.name,
                canonical_symbol=symbol,
                provider_symbol=symbol,
                adjustment="auto_adjust" if self.name == "yahoo" else "qfq",
                row_count=len(frame),
            ),
            warnings=[],
        )


@pytest.mark.parametrize(
    ("symbol", "asset_class", "provider"),
    [
        ("AAPL", "us_equity", "yahoo"),
        ("SPY", "etf", "yahoo"),
        ("0700.HK", "hk_equity", "yahoo"),
        ("BTC-USD", "crypto", "yahoo"),
        ("000001.SZ", "cn_equity", "akshare"),
        ("600519.SH", "cn_equity", "akshare"),
    ],
)
def test_symbol_classification(symbol: str, asset_class: str, provider: str) -> None:
    descriptor = classify_symbol(symbol)
    assert descriptor.asset_class == asset_class
    assert descriptor.preferred_provider == provider
    assert descriptor.canonical_symbol == symbol.upper()


def test_symbol_rejects_malformed() -> None:
    with pytest.raises(UnsupportedSymbolError):
        classify_symbol("")
    with pytest.raises(UnsupportedSymbolError):
        classify_symbol("600519")
    with pytest.raises(UnsupportedSymbolError):
        classify_symbol("not a symbol!")


def test_router_invokes_only_selected_adapter() -> None:
    yahoo = RecordingAdapter("yahoo")
    akshare = RecordingAdapter("akshare")
    router = MarketDataRouter(yahoo=yahoo, akshare=akshare)  # type: ignore[arg-type]

    router.get_daily_ohlcv("SPY", "2024-01-01")
    assert len(yahoo.calls) == 1
    assert yahoo.calls[0]["symbol"] == "SPY"
    assert akshare.calls == []

    router.get_daily_ohlcv("600519.SH", "2024-01-01")
    assert len(akshare.calls) == 1
    assert akshare.calls[0]["symbol"] == "600519.SH"
    assert len(yahoo.calls) == 1


def test_router_preserves_canonical_symbol_and_provenance() -> None:
    yahoo = RecordingAdapter("yahoo")
    akshare = RecordingAdapter("akshare")
    router = MarketDataRouter(yahoo=yahoo, akshare=akshare)  # type: ignore[arg-type]

    series = router.get_daily_ohlcv("000001.SZ", "2024-01-01")
    assert series.symbol == "000001.SZ"
    assert series.provenance.canonical_symbol == "000001.SZ"
    assert series.provenance.provider_symbol == "000001"
    assert series.provenance.asset_class == "cn_equity"
    assert series.provenance.provider == "akshare"
    assert series.provenance.exchange == "SZ"
    assert series.provenance.adjustment == "qfq"


def test_router_provider_override_validated() -> None:
    descriptor = classify_symbol("AAPL")
    with pytest.raises(UnsupportedSymbolError):
        resolve_provider(descriptor, "akshare")


def test_router_no_silent_cross_provider_fallback() -> None:
    yahoo = RecordingAdapter("yahoo", fail=True)
    akshare = RecordingAdapter("akshare")
    router = MarketDataRouter(yahoo=yahoo, akshare=akshare)  # type: ignore[arg-type]

    with pytest.raises(MarketDataUnavailableError):
        router.get_daily_ohlcv("AAPL", "2024-01-01")
    assert akshare.calls == []


def test_cache_key_includes_provider_and_adjustment(tmp_path) -> None:
    cache = PriceCache(root=tmp_path)
    yahoo_key = cache.make_key("yahoo", "SPY", "2024-01-01", None, "1d", "auto_adjust")
    akshare_key = cache.make_key(
        "akshare", "600519.SH", "2024-01-01", None, "1d", "qfq"
    )
    assert yahoo_key != akshare_key
    assert "auto_adjust" in yahoo_key
    assert "qfq" in akshare_key


def test_router_unsupported_symbol_maps_to_validation_error() -> None:
    router = MarketDataRouter(
        yahoo=RecordingAdapter("yahoo"),
        akshare=RecordingAdapter("akshare"),
    )  # type: ignore[arg-type]
    with pytest.raises(MarketDataValidationError):
        router.get_daily_ohlcv("!!!!", "2024-01-01")


def test_execution_route_uses_router_not_yahoo_directly() -> None:
    import inspect

    from app.api.routes import research_execution as route

    source = inspect.getsource(route.get_research_execution_service)
    assert "MarketDataRouter" in source or "build_default_market_data_port" in source
    assert "YahooFinanceMarketDataAdapter()" not in source
