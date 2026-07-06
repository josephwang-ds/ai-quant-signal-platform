"""样本外验证端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

OOS_URL = "/api/backtest/oos"

REQUIRED_METRIC_FIELDS = [
    "total_return",
    "benchmark_return",
    "sharpe_ratio",
    "strategy_max_drawdown",
    "benchmark_max_drawdown",
]


def test_oos_valid_request_returns_segments() -> None:
    response = client.post(
        OOS_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "split_date": "2024-01-01",
            "strategy": "ma_crossover",
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "segments" in payload
    for key in ("full_period", "in_sample", "out_of_sample"):
        assert key in payload["segments"]
        segment = payload["segments"][key]
        assert "period_start" in segment
        assert "period_end" in segment
        assert "rows" in segment
        assert segment["rows"] >= 1
        for field in REQUIRED_METRIC_FIELDS:
            assert field in segment["metrics"]

    assert isinstance(payload.get("interpretation"), list)
    assert len(payload["interpretation"]) >= 1


def test_oos_invalid_split_date_before_start_date() -> None:
    response = client.post(
        OOS_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "split_date": "2021-01-01",
            "strategy": "ma_crossover",
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code in (400, 422)


def test_oos_invalid_end_date_before_split_date() -> None:
    response = client.post(
        OOS_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "split_date": "2024-01-01",
            "end_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code in (400, 422)
