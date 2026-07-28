"""API / service tests for Phase 2 cross-sectional factor research."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import cross_sectional_dataset as cs_dataset_route
from app.api.routes import cross_sectional_factors as cs_factors_route
from app.cross_sectional.dataset import CrossSectionalDatasetService
from app.cross_sectional.research.schemas import CrossSectionalFactorResearchRequest
from app.cross_sectional.research.service import CrossSectionalFactorResearchService
from app.research_execution.market_data_port import (
    DataProvenance,
    NormalizedMarketSeries,
    utc_now_iso,
)
from app.research_validation.result_store import InMemoryValidationResultStore


class SyntheticMultiSymbolAdapter:
    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        symbol_u = symbol.upper().strip()
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date) if end_date else date(2020, 6, 30)
        seed = sum(ord(c) for c in symbol_u) % 17
        rows = []
        px = 50.0 + seed
        d = start
        while d <= end:
            if d.weekday() < 5:
                px *= 1.0 + ((seed - 8) * 0.0005) + ((d.toordinal() % 7) - 3) * 0.0004
                rows.append(
                    {
                        "symbol": symbol_u,
                        "date": pd.Timestamp(d),
                        "open": px,
                        "high": px * 1.01,
                        "low": px * 0.99,
                        "close": px,
                        "volume": 2_000_000 + seed * 1000,
                    }
                )
            d += timedelta(days=1)
        frame = pd.DataFrame(rows)
        return NormalizedMarketSeries(
            symbol=symbol_u,
            frame=frame,
            provenance=DataProvenance(
                provider="synthetic",
                symbol=symbol_u,
                source="SyntheticMultiSymbolAdapter",
                retrieved_at=utc_now_iso(),
                requested_start=start_date,
                requested_end=end_date,
                actual_start=str(frame["date"].iloc[0].date()),
                actual_end=str(frame["date"].iloc[-1].date()),
            ),
        )


def _service() -> CrossSectionalFactorResearchService:
    return CrossSectionalFactorResearchService(
        SyntheticMultiSymbolAdapter(),
        InMemoryValidationResultStore(),
    )


def test_research_service_runs_on_phase1_panel():
    result = _service().execute(
        {
            "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V", "MA"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "factor_columns": ["return_5d", "volatility_20d"],
            "label_horizons": [5, 20],
            "minimum_cross_section_size": 5,
            "minimum_quantile_size": 1,
            "quantile_count": 5,
            "preview_rows": 5,
            "apply_liquidity_filter": False,
            "minimum_stability_period_dates": 5,
            "minimum_turnover_overlap": 5,
        }
    )
    assert result["evidence_kind"] == "cross_sectional_factor_research"
    assert result["research_run_id"]
    assert result["dataset_summary"]["n_symbols"] == 10
    assert "return_5d|5" in result["rank_ic_summary"]
    assert "decay_summary" in result
    assert "sector_analysis" in result["unavailable_evidence"]
    assert len(result["previews"]["rank_ic"]) <= 5
    # Nulls remain null in unavailable previews when present
    assert "panel" not in result


def test_request_validation_rejects_bad_inputs():
    with pytest.raises(Exception):
        CrossSectionalFactorResearchRequest(factor_columns=["not_a_factor"])
    with pytest.raises(Exception):
        CrossSectionalFactorResearchRequest(label_horizons=[7])
    with pytest.raises(Exception):
        CrossSectionalFactorResearchRequest(quantile_count=1)
    with pytest.raises(Exception):
        CrossSectionalFactorResearchRequest(
            minimum_cross_section_size=4,
            quantile_count=5,
            minimum_quantile_size=2,
        )
    with pytest.raises(Exception):
        CrossSectionalFactorResearchRequest(factor_columns=["liquidity_eligible"])


def test_api_endpoint_and_phase1_unchanged():
    app = FastAPI()
    app.include_router(cs_factors_route.router)
    app.include_router(cs_dataset_route.router)
    store = InMemoryValidationResultStore()
    prior = store.save({"evidence_kind": "factor_validation", "keep": True})
    cs_factors_route._service = CrossSectionalFactorResearchService(
        SyntheticMultiSymbolAdapter(), store
    )
    cs_dataset_route._service = CrossSectionalDatasetService(
        SyntheticMultiSymbolAdapter(), InMemoryValidationResultStore()
    )
    client = TestClient(app)

    research = client.post(
        "/api/v1/research/cross-sectional/factors",
        json={
            "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V", "MA"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "factor_columns": ["return_20d"],
            "label_horizons": [5],
            "minimum_cross_section_size": 5,
            "minimum_quantile_size": 1,
            "preview_rows": 3,
            "minimum_stability_period_dates": 5,
            "minimum_turnover_overlap": 5,
        },
    )
    assert research.status_code == 200
    body = research.json()
    assert body["evidence_kind"] == "cross_sectional_factor_research"
    assert body["configuration"]["universe_id"] == "us_liquid_31_v1"

    dataset = client.post(
        "/api/v1/research/cross-sectional/dataset",
        json={
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 2,
            "liquidity_dollar_volume_floor": 1.0,
        },
    )
    assert dataset.status_code == 200
    assert dataset.json()["evidence_kind"] == "cross_sectional_dataset"
    assert store.get(prior)["keep"] is True

    bad = client.post(
        "/api/v1/research/cross-sectional/factors",
        json={"factor_columns": ["bogus"], "symbols": ["AAPL"]},
    )
    assert bad.status_code == 422
