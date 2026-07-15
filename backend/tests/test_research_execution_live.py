"""Backward-compatible entry point — see tests/test_market_data_live.py.

The canonical live verification suite lives in test_market_data_live.py and
uses MarketDataRouter (Yahoo + AkShare). This module re-exports the Yahoo
execution smoke for older commands.
"""

from __future__ import annotations

import pytest

from app.research_execution.live_verification import (
    YAHOO_LIVE_END,
    YAHOO_LIVE_START,
    assert_no_fabricated_fallback,
    assert_provenance_contract,
)
from app.research_execution.market_data_router import MarketDataRouter
from app.research_execution.price_cache import PriceCache
from app.research_execution.service import ResearchExecutionService

pytestmark = pytest.mark.live


@pytest.mark.live
def test_live_yahoo_spy_ma_execution(tmp_path) -> None:
    router = MarketDataRouter(cache=PriceCache(root=tmp_path / "cache"))
    service = ResearchExecutionService(router)
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": YAHOO_LIVE_START,
            "end_date": YAHOO_LIVE_END,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0,
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
    assert result["supported_evidence"]["evaluation"] == "unavailable"
