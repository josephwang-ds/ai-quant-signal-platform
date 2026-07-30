"""Deterministic post-trade attribution and anomaly detection tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes.post_trade_analytics import router
from app.post_trade.schemas import (
    AnomalyDetectionRequest,
    AttributionRequest,
    DetectionDirection,
    InputDataKind,
)
from app.post_trade.service import detect_anomalies, run_performance_attribution

NOW = datetime(2026, 7, 30, 9, 30, tzinfo=timezone.utc)


def _attribution_payload() -> dict:
    return {
        "input_data_kind": "synthetic_demo",
        "group_by": "venue",
        "observations": [
            {
                "trade_id": "t1",
                "timestamp": NOW.isoformat(),
                "strategy": "alpha-a",
                "venue": "XNAS",
                "notional_usd": 1_000_000,
                "gross_pnl_bps": 8.0,
                "benchmark_pnl_bps": 2.0,
                "fees_bps": 0.5,
                "slippage_bps": 1.0,
            },
            {
                "trade_id": "t2",
                "timestamp": (NOW + timedelta(minutes=1)).isoformat(),
                "strategy": "alpha-a",
                "venue": "BATS",
                "notional_usd": 3_000_000,
                "gross_pnl_bps": 4.0,
                "benchmark_pnl_bps": 1.0,
                "fees_bps": 0.5,
                "slippage_bps": 0.5,
            },
        ],
    }


def _metric_rows(values: list[float], *, entity: str = "gateway-a") -> list[dict]:
    return [
        {
            "timestamp": (NOW + timedelta(minutes=index)).isoformat(),
            "metric": "ack_latency_ms",
            "entity": entity,
            "value": value,
        }
        for index, value in enumerate(values)
    ]


def test_attribution_reconciles_weighted_active_pnl() -> None:
    result = run_performance_attribution(
        AttributionRequest.model_validate(_attribution_payload())
    )

    assert result.input_data_kind is InputDataKind.SYNTHETIC_DEMO
    assert result.total_notional_usd == 4_000_000
    assert result.gross_edge_bps == pytest.approx(3.75)
    assert result.fee_drag_bps == pytest.approx(-0.5)
    assert result.slippage_drag_bps == pytest.approx(-0.625)
    assert result.net_active_bps == pytest.approx(2.625)
    assert result.net_active_usd == pytest.approx(1_050.0)
    assert result.reconciliation_error_usd == 0.0
    assert [item.group for item in result.groups] == ["BATS", "XNAS"]
    assert sum(item.contribution_usd for item in result.components[:3]) == pytest.approx(
        result.net_active_usd
    )


def test_attribution_can_group_by_strategy() -> None:
    payload = _attribution_payload()
    payload["group_by"] = "strategy"
    payload["observations"][1]["strategy"] = "alpha-b"
    result = run_performance_attribution(AttributionRequest.model_validate(payload))
    assert [item.group for item in result.groups] == ["alpha-b", "alpha-a"]


def test_attribution_rejects_duplicate_trade_ids_and_non_finite_values() -> None:
    duplicate = _attribution_payload()
    duplicate["observations"][1]["trade_id"] = "t1"
    with pytest.raises(ValidationError, match="trade_id values must be unique"):
        AttributionRequest.model_validate(duplicate)

    invalid = _attribution_payload()
    invalid["observations"][0]["gross_pnl_bps"] = float("nan")
    with pytest.raises(ValidationError, match="finite"):
        AttributionRequest.model_validate(invalid)


def test_anomaly_detection_uses_past_only_robust_baseline() -> None:
    values = [10.0, 10.2, 9.9, 10.1, 10.0, 10.1, 9.8, 10.2, 10.0, 35.0]
    request = AnomalyDetectionRequest.model_validate(
        {
            "observations": _metric_rows(values),
            "baseline_window": 8,
            "minimum_history": 5,
            "threshold": 3.5,
            "direction": "high",
            "input_data_kind": "synthetic_demo",
        }
    )
    result = detect_anomalies(request)

    assert result.scored_count == 5
    assert result.anomaly_count == 1
    event = result.anomalies[0]
    assert event.timestamp == NOW + timedelta(minutes=9)
    assert event.value == 35.0
    assert event.baseline_median < 10.2
    assert event.robust_z_score > request.threshold
    assert event.severity == "critical"
    assert result.series[0].status == "critical"


def test_anomaly_direction_can_detect_low_degradation() -> None:
    request = AnomalyDetectionRequest.model_validate(
        {
            "observations": _metric_rows([100, 100, 100, 100, 100, 100, 70]),
            "baseline_window": 6,
            "minimum_history": 5,
            "threshold": 3.0,
            "direction": DetectionDirection.LOW,
        }
    )
    result = detect_anomalies(request)
    assert result.anomaly_count == 1
    assert result.anomalies[0].robust_z_score == -999.0


def test_multiple_series_are_isolated() -> None:
    observations = _metric_rows([10, 10, 10, 10, 10, 10, 30], entity="gateway-a")
    observations += _metric_rows([20, 20, 20, 20, 20, 20, 20], entity="gateway-b")
    result = detect_anomalies(
        AnomalyDetectionRequest.model_validate(
            {
                "observations": observations,
                "baseline_window": 6,
                "minimum_history": 5,
                "threshold": 3.0,
            }
        )
    )
    assert result.anomaly_count == 1
    assert result.anomalies[0].entity == "gateway-a"
    by_entity = {item.entity: item for item in result.series}
    assert by_entity["gateway-a"].status == "critical"
    assert by_entity["gateway-b"].status == "normal"


def test_api_endpoints_return_typed_results() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    attribution = client.post(
        "/api/v1/post-trade/attribution",
        json=_attribution_payload(),
    )
    assert attribution.status_code == 200
    assert attribution.json()["net_active_bps"] == pytest.approx(2.625)

    anomaly = client.post(
        "/api/v1/post-trade/anomalies",
        json={
            "observations": _metric_rows([10, 10, 10, 10, 10, 10, 30]),
            "baseline_window": 6,
            "minimum_history": 5,
            "threshold": 3.0,
        },
    )
    assert anomaly.status_code == 200
    assert anomaly.json()["anomaly_count"] == 1


def test_api_rejects_inconsistent_anomaly_window() -> None:
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post(
        "/api/v1/post-trade/anomalies",
        json={
            "observations": _metric_rows([10, 10, 10, 10, 10, 10]),
            "baseline_window": 5,
            "minimum_history": 6,
        },
    )
    assert response.status_code == 422
