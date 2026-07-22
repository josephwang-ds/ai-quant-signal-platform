"""Risk review API tests (offline — monkeypatch load_price_data)."""

from __future__ import annotations

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.risk_review import COMPONENT_KEYS, build_risk_monitor_input, router
from app.risk.risk_monitor import calculate_overall_risk_level

risk_app = FastAPI()
risk_app.include_router(router)
client = TestClient(risk_app)

REVIEW_URL = "/api/v1/risk/review"


def _sample_price_frame() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=120, freq="B")
    # Mild oscillation so MA crossover produces some trades without inventing metrics.
    close = pd.Series(
        [100 + ((i % 20) - 10) * 0.8 + i * 0.05 for i in range(120)],
        index=dates,
        dtype=float,
    )
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1_000_000,
            "data_source": "yahoo",
        }
    )


def test_risk_review_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.risk_review.load_price_data",
        lambda *args, **kwargs: _sample_price_frame(),
    )

    response = client.post(
        REVIEW_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 5,
            "long_window": 20,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["strategy"] == "ma_crossover"
    assert "metrics" in payload
    assert "volatility" in payload["metrics"]
    assert "max_drawdown" in payload["metrics"]
    assert "sharpe_ratio" in payload["metrics"]

    risk = payload["risk"]
    assert 1 <= risk["risk_level"] <= 5
    assert isinstance(risk["risk_label"], str) and risk["risk_label"]
    assert isinstance(risk["allowed_action"], str) and risk["allowed_action"]
    assert isinstance(risk["risk_reasons"], list)
    assert set(risk["component_levels"].keys()) == set(COMPONENT_KEYS)
    for key in COMPONENT_KEYS:
        assert 1 <= risk["component_levels"][key] <= 5


def test_risk_review_missing_optional_metrics_degrade_to_level_one() -> None:
    """Absent optional inputs must not raise; related components stay at level 1."""
    metrics = {
        "max_drawdown": 0.0,
        "strategy_max_drawdown": 0.0,
        # volatility / sharpe intentionally omitted
        "transaction_cost_total": 0.0,
        "total_return": 0.0,
    }
    empty_df = pd.DataFrame(
        {
            "close": [100.0, 101.0],
            "trade_action": [None, None],
            "strategy_return_before_cost": [0.0, 0.0],
        }
    )
    assessment = calculate_overall_risk_level(
        build_risk_monitor_input(metrics, empty_df)
    )
    assert assessment.risk_level >= 1
    assert assessment.component_levels["volatility"] == 1
    assert assessment.component_levels["sharpe_decline"] == 1
    assert assessment.component_levels["signal_conflict"] == 1
    assert assessment.component_levels["cost_drag"] == 1
    assert assessment.component_levels["single_trade_loss"] == 1
    assert assessment.component_levels["consecutive_losses"] == 1


def test_risk_review_no_price_data_returns_404(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise ValueError("No price data found for ticker 'ZZZZ' (2023-01-01 → latest).")

    monkeypatch.setattr("app.api.routes.risk_review.load_price_data", _raise)

    response = client.post(
        REVIEW_URL,
        json={
            "ticker": "ZZZZ",
            "start_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 5,
            "long_window": 20,
        },
    )

    assert response.status_code == 404
    assert "No price data found" in response.json()["detail"]
