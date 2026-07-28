"""Service / API boundary tests for cross-sectional dataset."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import cross_sectional_dataset as cs_route
from app.cross_sectional.constants import MAX_PREVIEW_ROWS, MAX_REQUEST_SYMBOLS, UNIVERSE_ID_LIQUID_31
from app.cross_sectional.dataset import CrossSectionalDatasetService
from app.cross_sectional.universe import US_LIQUID_31_V1
from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    NormalizedMarketSeries,
    utc_now_iso,
)
from app.research_validation.result_store import InMemoryValidationResultStore


class SyntheticMultiSymbolAdapter:
    """Deterministic OHLCV for requested symbols — offline only."""

    def __init__(self, *, fail_symbols: set[str] | None = None) -> None:
        self.fail_symbols = {s.upper() for s in (fail_symbols or set())}
        self.calls: list[str] = []

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        symbol_u = symbol.upper().strip()
        self.calls.append(symbol_u)
        if symbol_u in self.fail_symbols:
            raise MarketDataUnavailableError(f"Synthetic failure for {symbol_u}")
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date) if end_date else date(2020, 6, 30)
        seed = sum(ord(c) for c in symbol_u) % 17
        rows = []
        px = 50.0 + seed
        d = start
        while d <= end:
            if d.weekday() < 5:
                px *= 1.0 + ((seed - 8) * 0.0004) + ((d.toordinal() % 7) - 3) * 0.0003
                rows.append(
                    {
                        "symbol": symbol_u,
                        "date": pd.Timestamp(d),
                        "open": px,
                        "high": px * 1.01,
                        "low": px * 0.99,
                        "close": px,
                        "volume": 1_500_000 + seed * 1000,
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
                source="SyntheticMultiSymbolAdapter",
                retrieved_at=utc_now_iso(),
                requested_start=start_date,
                requested_end=end_date,
                actual_start=str(frame["date"].iloc[0].date()),
                actual_end=str(frame["date"].iloc[-1].date()),
            ),
        )


@pytest.fixture
def dataset_service() -> CrossSectionalDatasetService:
    return CrossSectionalDatasetService(
        SyntheticMultiSymbolAdapter(),
        InMemoryValidationResultStore(),
    )


def _client(service: CrossSectionalDatasetService) -> TestClient:
    app = FastAPI()
    app.include_router(cs_route.router)
    cs_route._service = service
    return TestClient(app)


def test_service_builds_panel_summary_and_preview(dataset_service: CrossSectionalDatasetService):
    result = dataset_service.execute(
        {
            "research_id": "cross-sectional-equity-liquid-v1",
            "universe_id": UNIVERSE_ID_LIQUID_31,
            "symbols": ["AAPL", "MSFT", "NVDA"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 5,
            "liquidity_dollar_volume_floor": 1.0,
            "min_history_days": 60,
        }
    )
    assert result["evidence_kind"] == "cross_sectional_dataset"
    assert result["dataset_run_id"]
    assert result["configuration"]["universe_version"] == UNIVERSE_ID_LIQUID_31
    assert result["dataset_summary"]["universe_version"] == UNIVERSE_ID_LIQUID_31
    assert result["dataset_summary"]["n_symbols"] == 3
    assert result["dataset_summary"]["n_rows"] > 0
    assert len(result["records_preview"]) == 5
    assert "sector" in result["unavailable_evidence"]
    assert any("demonstration universe" in w.lower() or "Static" in w for w in result["warnings"])
    assert "panel" not in result
    assert "records" not in result
    # Warm-up factor nulls serialize as null, not zero
    warm = next(
        r for r in result["records_preview"] if r.get("return_60d") is None
    )
    assert "return_60d" in warm
    assert warm["return_60d"] is None


def test_service_reports_provider_failure_incomplete_coverage():
    store = InMemoryValidationResultStore()
    # Pre-seed unrelated research state that must not be mutated/cleared.
    prior_id = store.save({"evidence_kind": "factor_validation", "keep": True})
    service = CrossSectionalDatasetService(
        SyntheticMultiSymbolAdapter(fail_symbols={"MSFT"}),
        store,
    )
    result = service.execute(
        {
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 0,
            "liquidity_dollar_volume_floor": 1.0,
        }
    )
    assert result["coverage_summary"]["n_loaded_symbols"] == 1
    assert result["coverage_summary"]["universe_coverage"] == pytest.approx(0.5)
    assert result["provenance"]["provider_failures"]
    assert "full_universe_ohlcv" in result["unavailable_evidence"]
    assert result["quality_summary"]["status"] in {"incomplete", "failed", "completed"}
    # Unrelated prior artifact still present
    assert store.get(prior_id)["keep"] is True


def test_duplicate_requested_symbols_normalized():
    adapter = SyntheticMultiSymbolAdapter()
    service = CrossSectionalDatasetService(adapter, InMemoryValidationResultStore())
    result = service.execute(
        {
            "symbols": ["aapl", "AAPL", "msft"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 0,
            "liquidity_dollar_volume_floor": 1.0,
        }
    )
    assert result["configuration"]["symbols"] == ["AAPL", "MSFT"]
    assert adapter.calls == ["AAPL", "MSFT"]


def test_api_endpoint_happy_path_and_null_serialization():
    client = _client(
        CrossSectionalDatasetService(
            SyntheticMultiSymbolAdapter(),
            InMemoryValidationResultStore(),
        )
    )
    response = client.post(
        "/api/v1/research/cross-sectional/dataset",
        json={
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 3,
            "liquidity_dollar_volume_floor": 1.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["evidence_kind"] == "cross_sectional_dataset"
    assert body["dataset_summary"]["n_symbols"] == 2
    assert len(body["records_preview"]) == 3
    # JSON nulls for warm-up factors
    assert any(row.get("return_60d") is None for row in body["records_preview"])
    assert "panel" not in body


def test_api_rejects_unknown_fields_and_date_order_and_limits():
    client = _client(
        CrossSectionalDatasetService(
            SyntheticMultiSymbolAdapter(),
            InMemoryValidationResultStore(),
        )
    )
    assert (
        client.post(
            "/api/v1/research/cross-sectional/dataset",
            json={"symbols": ["AAPL"], "not_a_field": 1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/research/cross-sectional/dataset",
            json={
                "symbols": ["AAPL"],
                "start_date": "2020-06-01",
                "end_date": "2020-01-01",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/research/cross-sectional/dataset",
            json={"symbols": ["AAPL"], "preview_rows": MAX_PREVIEW_ROWS + 1},
        ).status_code
        == 422
    )
    oversized = [f"S{i}" for i in range(MAX_REQUEST_SYMBOLS + 1)]
    assert (
        client.post(
            "/api/v1/research/cross-sectional/dataset",
            json={
                "symbols": oversized,
                "start_date": "2020-01-01",
                "end_date": "2020-06-30",
            },
        ).status_code
        == 422
    )


def test_api_partial_failure_not_complete_coverage():
    client = _client(
        CrossSectionalDatasetService(
            SyntheticMultiSymbolAdapter(fail_symbols={"MSFT"}),
            InMemoryValidationResultStore(),
        )
    )
    response = client.post(
        "/api/v1/research/cross-sectional/dataset",
        json={
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "preview_rows": 0,
            "liquidity_dollar_volume_floor": 1.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["coverage_summary"]["n_loaded_symbols"] == 1
    assert body["provenance"]["provider_failures"]
    assert body["validation_status"] != "completed" or body["coverage_summary"][
        "universe_coverage"
    ] < 1.0


def test_insufficient_history_quality_warning():
    service = CrossSectionalDatasetService(
        SyntheticMultiSymbolAdapter(),
        InMemoryValidationResultStore(),
    )
    # Very short window → insufficient_history check fails
    result = service.execute(
        {
            "symbols": ["AAPL"],
            "start_date": "2020-01-01",
            "end_date": "2020-01-15",
            "preview_rows": 0,
            "liquidity_dollar_volume_floor": 1.0,
            "min_history_days": 60,
        }
    )
    checks = {c["id"]: c for c in result["quality_summary"]["checks"]}
    assert checks["insufficient_history"]["status"] == "fail"
    assert result["quality_summary"]["status"] in {"incomplete", "failed"}


def test_default_universe_membership_count():
    assert len(US_LIQUID_31_V1) == 31
    assert len(set(US_LIQUID_31_V1)) == 31
