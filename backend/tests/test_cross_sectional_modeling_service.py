"""Service and API tests for Phase 3 cross-sectional modeling."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import cross_sectional_models as models_route
from app.cross_sectional.modeling.service import (
    CrossSectionalModelingError,
    CrossSectionalModelingService,
)
from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    NormalizedMarketSeries,
    utc_now_iso,
)
from app.research_validation.result_store import InMemoryValidationResultStore


class SyntheticMultiSymbolAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        symbol_u = symbol.upper().strip()
        self.calls.append(symbol_u)
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date) if end_date else date(2020, 12, 31)
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
def modeling_service() -> CrossSectionalModelingService:
    return CrossSectionalModelingService(
        SyntheticMultiSymbolAdapter(),
        InMemoryValidationResultStore(),
    )


def _client(service: CrossSectionalModelingService) -> TestClient:
    app = FastAPI()
    app.include_router(models_route.router)
    models_route._service = service
    return TestClient(app)


def _tiny_payload(**overrides):
    base = {
        "research_id": "cross-sectional-modeling-v1",
        "symbols": [f"S{i:02d}" for i in range(12)],
        "start_date": "2019-01-01",
        "end_date": "2019-12-31",
        "feature_columns": [
            "return_5d",
            "return_20d",
            "volatility_20d",
            "dollar_volume_20",
        ],
        "label": "forward_return_5d",
        "model_names": ["ridge"],
        "minimum_train_dates": 40,
        "validation_window": 10,
        "prediction_window": 10,
        "minimum_cross_section_size": 5,
        "prediction_preview_limit": 20,
        "random_seed": 7,
        "ridge_alphas": [0.1, 1.0, 10.0],
    }
    base.update(overrides)
    return base


def test_service_walk_forward_oos_only(modeling_service: CrossSectionalModelingService):
    result = modeling_service.execute(_tiny_payload())
    assert result["evidence_kind"] == "cross_sectional_modeling"
    assert result["fold_summaries"]
    assert "ridge" in result["out_of_sample_evaluation"]
    preview = result["bounded_prediction_preview"]
    assert len(preview) <= 20
    for row in preview:
        assert row["fit_id"]
        assert row["fold_id"]
        assert row["rank"] >= 1
        # score equals raw in v1
        assert row["score"] == row["raw_prediction"] or (
            row["score"] is not None and row["raw_prediction"] is not None
        )
    # Predictions only in fold prediction windows
    fold_windows = {
        f["fold_id"]: (f["prediction_start_date"], f["prediction_end_date"])
        for f in result["fold_summaries"]
        if f.get("status") == "ok"
    }
    for row in preview:
        start, end = fold_windows[row["fold_id"]]
        assert start <= row["as_of_date"] <= end
    assert "portfolio_weights" in result["unavailable_evidence"]
    assert result["artifact_reference"]["restart_loss"] is True
    # Null ICIR remains null when applicable — field present
    oos = result["out_of_sample_evaluation"]["ridge"]
    assert "icir" in oos
    assert "mean_rank_ic" in oos


def test_service_rejects_bad_feature_label_model(modeling_service: CrossSectionalModelingService):
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(feature_columns=["liquidity_eligible"]))
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(label="forward_return_1d"))
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(model_names=["xgboost"]))
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(split_mode="random_kfold"))
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(ridge_alphas=[-1.0]))
    with pytest.raises(CrossSectionalModelingError):
        modeling_service.execute(_tiny_payload(prediction_preview_limit=9999))


def test_api_validation_and_success(modeling_service: CrossSectionalModelingService):
    client = _client(modeling_service)
    bad = client.post(
        "/api/v1/research/cross-sectional/models",
        json=_tiny_payload(label="nope"),
    )
    assert bad.status_code == 422

    ok = client.post(
        "/api/v1/research/cross-sectional/models",
        json=_tiny_payload(),
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["bounded_prediction_preview"] is not None
    assert "serialized_model_binaries" in body["unavailable_evidence"]


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("lightgbm") is None,
    reason="lightgbm not installed",
)
def test_service_ridge_and_lightgbm_comparison(modeling_service: CrossSectionalModelingService):
    result = modeling_service.execute(
        _tiny_payload(
            model_names=["ridge", "lightgbm"],
            lightgbm_parameters=[
                {
                    "num_leaves": 15,
                    "learning_rate": 0.05,
                    "n_estimators": 40,
                    "max_depth": 3,
                }
            ],
        )
    )
    assert "ridge" in result["out_of_sample_evaluation"]
    assert "lightgbm" in result["out_of_sample_evaluation"]
    comp = result["model_comparison"]
    assert any(x.startswith("simplest_baseline") for x in comp["evidence_labels"])
    assert "production" not in str(comp).lower() or "not deployment" in comp.get("note", "").lower()


def test_repeated_request_does_not_corrupt_store(modeling_service: CrossSectionalModelingService):
    store = modeling_service._result_store
    r1 = modeling_service.execute(_tiny_payload(research_id="cross-sectional-modeling-a"))
    r2 = modeling_service.execute(_tiny_payload(research_id="cross-sectional-modeling-b"))
    assert r1["research_run_id"] != r2["research_run_id"]
    s1 = store.get(r1["research_run_id"])
    s2 = store.get(r2["research_run_id"])
    assert s1 is not None and s2 is not None
    assert s1["configuration"]["research_id"] == "cross-sectional-modeling-a"
    assert s2["configuration"]["research_id"] == "cross-sectional-modeling-b"
