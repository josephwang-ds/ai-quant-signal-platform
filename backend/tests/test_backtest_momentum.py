"""动量策略回测端点 TestClient 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BACKTEST_URL = "/api/backtest"


@pytest.mark.live
def test_momentum_backtest_success() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "momentum",
            "momentum_window": 60,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "momentum"
    assert "metrics" in payload
    assert len(payload["data"]) >= 1

    first_row = payload["data"][0]
    assert "momentum_return" in first_row
    assert "momentum_signal" in first_row
    assert "cumulative_strategy" in first_row
    assert "cumulative_benchmark" in first_row
    assert "strategy_drawdown" in first_row
    assert "benchmark_drawdown" in first_row
    assert payload["parameters"]["momentum_window"] == 60


def test_momentum_backtest_invalid_window_too_small() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "momentum",
            "momentum_window": 4,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code in (400, 422)


def test_momentum_backtest_invalid_window_too_large() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "momentum",
            "momentum_window": 300,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code in (400, 422)
