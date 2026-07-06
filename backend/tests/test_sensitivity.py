"""参数敏感性分析端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SENSITIVITY_URL = "/api/backtest/sensitivity"

REQUIRED_ROW_FIELDS = [
    "short_window",
    "long_window",
    "total_return",
    "benchmark_return",
    "cagr",
    "sharpe_ratio",
    "max_drawdown",
    "volatility",
    "number_of_trades",
]


def test_sensitivity_default_parameter_sets() -> None:
    response = client.post(
        SENSITIVITY_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "end_date": None,
            "strategy": "ma_crossover",
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert len(payload["results"]) >= 1

    for row in payload["results"]:
        for field in REQUIRED_ROW_FIELDS:
            assert field in row


def test_sensitivity_custom_parameter_sets() -> None:
    parameter_sets = [
        {"short_window": 10, "long_window": 30},
        {"short_window": 20, "long_window": 60},
    ]

    response = client.post(
        SENSITIVITY_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "ma_crossover",
            "transaction_cost": 0.001,
            "parameter_sets": parameter_sets,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    pairs = {(row["short_window"], row["long_window"]) for row in payload["results"]}
    assert pairs == {(10, 30), (20, 60)}


def test_sensitivity_invalid_windows() -> None:
    response = client.post(
        SENSITIVITY_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "ma_crossover",
            "transaction_cost": 0.001,
            "parameter_sets": [{"short_window": 60, "long_window": 20}],
        },
    )

    assert response.status_code in (400, 422)


def test_sensitivity_too_many_parameter_sets() -> None:
    parameter_sets = [
        {"short_window": 5, "long_window": 10 + index} for index in range(21)
    ]

    response = client.post(
        SENSITIVITY_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "ma_crossover",
            "transaction_cost": 0.001,
            "parameter_sets": parameter_sets,
        },
    )

    assert response.status_code in (400, 422)
