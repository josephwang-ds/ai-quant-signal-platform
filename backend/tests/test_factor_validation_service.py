"""Service / API tests for factor validation with synthetic multi-symbol data."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import factor_validation as factor_route
from app.factor_validation.factors import US_SECTOR_ETFS
from app.factor_validation.service import FactorValidationService
from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    NormalizedMarketSeries,
    utc_now_iso,
)
from app.research_validation.result_store import InMemoryValidationResultStore


class SyntheticUniverseAdapter:
    """Deterministic OHLCV for every requested symbol — offline only."""

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        symbol_u = symbol.upper().strip()
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date) if end_date else date(2023, 12, 29)
        # Seed drift by symbol so factors differ across names
        seed = sum(ord(c) for c in symbol_u) % 17
        rows = []
        px = 50.0 + seed
        d = start
        while d <= end:
            if d.weekday() < 5:
                px *= 1.0 + ((seed - 8) * 0.0003) + ((d.toordinal() % 7) - 3) * 0.0002
                rows.append(
                    {
                        "symbol": symbol_u,
                        "date": pd.Timestamp(d),
                        "open": px,
                        "high": px * 1.01,
                        "low": px * 0.99,
                        "close": px,
                        "volume": 1_000_000,
                    }
                )
            d += timedelta(days=1)
        if not rows:
            raise MarketDataUnavailableError("empty")
        frame = pd.DataFrame(rows)
        return NormalizedMarketSeries(
            symbol=symbol_u,
            frame=frame,
            provenance=DataProvenance(
                provider="synthetic",
                symbol=symbol_u,
                source="SyntheticUniverseAdapter",
                retrieved_at=utc_now_iso(),
                requested_start=start_date,
                requested_end=end_date,
                actual_start=str(frame["date"].iloc[0].date()),
                actual_end=str(frame["date"].iloc[-1].date()),
            ),
        )


@pytest.fixture
def factor_service() -> FactorValidationService:
    return FactorValidationService(
        SyntheticUniverseAdapter(),
        InMemoryValidationResultStore(),
    )


def test_service_momentum_returns_ic_and_quantiles(factor_service: FactorValidationService):
    result = factor_service.execute(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "universe_id": "us_sector_etfs",
            "factor_id": "momentum",
            "start_date": "2019-01-01",
            "end_date": "2023-12-29",
            "holding_period_months": 1,
            "transaction_cost": 0.001,
        }
    )
    assert result["template"] == "cross_sectional_factor"
    assert result["factor_id"] == "momentum"
    assert result["validation_run_id"]
    assert result["ic"]["summary"]["n_periods"] > 0
    assert result["quantiles"]["n_rebalances"] > 0
    assert "Q1" in result["quantiles"]["cumulative_returns"]
    assert result["long_short"]["cumulative_final"] is not None
    assert set(result["provenance"]["symbols_used"]) <= set(US_SECTOR_ETFS)

    capm = result["capm"]
    assert capm["benchmark_symbol"] == "SPY"
    assert result["provenance"]["benchmark_symbol"] == "SPY"
    regression = capm["regression"]
    assert regression["n_observations"] > 0
    assert regression["beta"] is not None
    decomposition = capm["decomposition"]
    assert len(decomposition["dates"]) == len(
        result["long_short"]["period_returns_net_of_cost"]
    )
    assert "methodology" in decomposition

    portfolio_risk = result["portfolio_risk"]
    assert portfolio_risk["sharpe_ratio_net"] is not None
    assert portfolio_risk["max_drawdown_net"] is not None
    assert portfolio_risk["max_drawdown_net"] <= 0


def test_service_honors_custom_benchmark_symbol(factor_service: FactorValidationService):
    result = factor_service.execute(
        {
            "factor_id": "momentum",
            "start_date": "2019-01-01",
            "end_date": "2023-12-29",
            "benchmark_symbol": "qqq",
        }
    )
    assert result["capm"]["benchmark_symbol"] == "QQQ"
    assert result["provenance"]["benchmark_symbol"] == "QQQ"


def test_service_degrades_honestly_when_benchmark_unavailable():
    class NoBenchmarkAdapter(SyntheticUniverseAdapter):
        def get_daily_ohlcv(self, symbol, start_date, end_date=None):
            if symbol.upper() == "SPY":
                raise MarketDataUnavailableError("benchmark feed down")
            return super().get_daily_ohlcv(symbol, start_date, end_date)

    service = FactorValidationService(
        NoBenchmarkAdapter(), InMemoryValidationResultStore()
    )
    result = service.execute(
        {
            "factor_id": "momentum",
            "start_date": "2019-01-01",
            "end_date": "2023-12-29",
        }
    )
    assert result["capm"]["regression"]["alpha"] is None
    assert result["capm"]["regression"]["beta"] is None
    assert result["capm"]["decomposition"]["dates"] == []
    assert any("benchmark SPY" in warning for warning in result["warnings"])


def test_service_rejects_value_coming_soon(factor_service: FactorValidationService):
    with pytest.raises(Exception) as exc:
        factor_service.execute({"factor_id": "value"})
    assert "Coming Soon" in str(exc.value)


def test_factor_validation_http_endpoint(monkeypatch):
    svc = FactorValidationService(
        SyntheticUniverseAdapter(),
        InMemoryValidationResultStore(),
    )
    monkeypatch.setattr(factor_route, "get_factor_validation_service", lambda: svc)
    app = FastAPI()
    app.include_router(factor_route.router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/research/factor-validation",
        json={
            "factor_id": "low_volatility",
            "start_date": "2019-01-01",
            "end_date": "2023-12-29",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["factor_id"] == "low_volatility"
    assert body["ic"]["summary"]["n_periods"] > 0

    blocked = client.post(
        "/api/v1/research/factor-validation",
        json={"factor_id": "value"},
    )
    assert blocked.status_code == 400
    assert "Coming Soon" in blocked.json()["detail"]
