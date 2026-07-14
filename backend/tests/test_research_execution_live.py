"""Optional live Yahoo Finance smoke test — excluded from default CI.

Run:
  PYTHONPATH=. python -m pytest tests/test_research_execution_live.py -v -m live
"""

from __future__ import annotations

import pytest

from app.research_execution.service import ResearchExecutionService
from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter

pytestmark = pytest.mark.live


@pytest.mark.live
def test_live_yahoo_spy_ma_execution() -> None:
    service = ResearchExecutionService(YahooFinanceMarketDataAdapter())
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": "2018-01-01",
            "end_date": None,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0,
        }
    )
    assert result["provenance"]["symbol"] == "SPY"
    assert "Yahoo" in result["provenance"]["source"] or result["provenance"][
        "provider"
    ] in {"yahoo", "Yahoo Finance"}
    assert result["metrics"]["observation_count"] > 500
    assert result["supported_evidence"]["evaluation"] == "unavailable"
