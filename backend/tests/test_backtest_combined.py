"""组合信号策略回测 TestClient 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BACKTEST_URL = "/api/backtest"


@pytest.mark.live
def test_combined_conservative_backtest_success() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "combined_signal",
            "short_window": 20,
            "long_window": 60,
            "momentum_window": 60,
            "combined_mode": "conservative",
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "combined_signal"
    assert payload["strategy_config"]["combined_mode"] == "conservative"
    assert isinstance(payload["trade_log"], list)

    first_row = payload["data"][0]
    assert "ma_signal" in first_row
    assert "momentum_signal" in first_row
    assert "combined_signal" in first_row
    assert first_row["combined_mode"] == "conservative"


@pytest.mark.live
def test_combined_aggressive_backtest_success() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "combined_signal",
            "short_window": 20,
            "long_window": 60,
            "momentum_window": 60,
            "combined_mode": "aggressive",
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy_config"]["combined_mode"] == "aggressive"
    assert payload["data"][0]["combined_mode"] == "aggressive"


def test_combined_invalid_mode() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "combined_signal",
            "combined_mode": "invalid",
        },
    )

    assert response.status_code in (400, 422)


def test_combined_invalid_windows() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "combined_signal",
            "short_window": 60,
            "long_window": 20,
            "momentum_window": 60,
        },
    )

    assert response.status_code in (400, 422)


def test_combined_invalid_momentum_window() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "combined_signal",
            "momentum_window": 4,
        },
    )

    assert response.status_code in (400, 422)
