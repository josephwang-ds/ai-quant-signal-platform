"""Optional live Yahoo and AkShare verification — excluded from default CI.

Run all live checks:
  PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -v

Run Yahoo only:
  PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -k yahoo -v

Run AkShare only:
  PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -k akshare -v
"""

from __future__ import annotations

import pytest

from app.research_execution.live_verification import (
    AKSHARE_EXECUTION_END,
    AKSHARE_EXECUTION_START,
    AKSHARE_LIVE_END,
    AKSHARE_LIVE_START,
    YAHOO_LIVE_END,
    YAHOO_LIVE_START,
    assert_json_safe,
    assert_no_fabricated_fallback,
    assert_ohlcv_frame,
    assert_provenance_contract,
)
from app.research_execution.market_data_router import MarketDataRouter
from app.research_execution.price_cache import PriceCache
from app.research_execution.service import ResearchExecutionService

pytestmark = pytest.mark.live


@pytest.fixture()
def live_router(tmp_path) -> MarketDataRouter:
    """Fresh cache per test to avoid stale labeled hits on live fetches."""
    return MarketDataRouter(cache=PriceCache(root=tmp_path / "live_cache"))


@pytest.fixture()
def live_execution_service(live_router: MarketDataRouter) -> ResearchExecutionService:
    return ResearchExecutionService(live_router)


def test_live_yahoo_spy_ohlcv(live_router: MarketDataRouter) -> None:
    series = live_router.get_daily_ohlcv("SPY", YAHOO_LIVE_START, YAHOO_LIVE_END)

    assert series.symbol == "SPY"
    assert_ohlcv_frame(series.frame)
    assert_provenance_contract(
        series.provenance,
        expected_provider="yahoo",
        expected_asset_class="etf",
        expected_canonical_symbol="SPY",
        require_fresh_live_fetch=True,
    )
    assert_no_fabricated_fallback(series.warnings)
    assert_json_safe(series_to_dict(series))


def test_live_akshare_600519_sh_ohlcv(live_router: MarketDataRouter) -> None:
    series = live_router.get_daily_ohlcv(
        "600519.SH",
        AKSHARE_LIVE_START,
        AKSHARE_LIVE_END,
    )

    assert series.symbol == "600519.SH"
    assert_ohlcv_frame(series.frame)
    assert_provenance_contract(
        series.provenance,
        expected_provider="akshare",
        expected_asset_class="cn_equity",
        expected_canonical_symbol="600519.SH",
        expected_exchange="SH",
        expected_adjustment="qfq",
        require_fresh_live_fetch=True,
    )
    assert_no_fabricated_fallback(series.warnings)
    assert_json_safe(series_to_dict(series))


def test_live_yahoo_spy_execution(live_execution_service: ResearchExecutionService) -> None:
    result = live_execution_service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": YAHOO_LIVE_START,
            "end_date": YAHOO_LIVE_END,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0.0,
        }
    )

    assert_provenance_contract(
        result["provenance"],
        expected_provider="yahoo",
        expected_asset_class="etf",
        expected_canonical_symbol="SPY",
    )
    assert result["metrics"]["observation_count"] > 100
    assert_no_fabricated_fallback(result["warnings"])
    assert_json_safe(result)


def test_live_akshare_600519_sh_execution(
    live_execution_service: ResearchExecutionService,
) -> None:
    result = live_execution_service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "600519.SH",
            "benchmark": "600519.SH",
            "start_date": AKSHARE_EXECUTION_START,
            "end_date": AKSHARE_EXECUTION_END,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0.0,
        }
    )

    assert_provenance_contract(
        result["provenance"],
        expected_provider="akshare",
        expected_asset_class="cn_equity",
        expected_canonical_symbol="600519.SH",
        expected_exchange="SH",
        expected_adjustment="qfq",
    )
    assert result["metrics"]["observation_count"] > 100
    assert_no_fabricated_fallback(result["warnings"])
    assert_json_safe(result)


def series_to_dict(series) -> dict:
    from dataclasses import asdict

    return {
        "symbol": series.symbol,
        "provenance": asdict(series.provenance),
        "warnings": series.warnings,
        "row_count": len(series.frame),
    }
