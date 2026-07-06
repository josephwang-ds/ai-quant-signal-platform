"""策略对比端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

COMPARE_URL = "/api/backtest/compare-strategies"
BACKTEST_URL = "/api/backtest"


def test_compare_strategies_success() -> None:
    response = client.post(
        COMPARE_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "transaction_cost": 0.001,
            "short_window": 20,
            "long_window": 60,
            "momentum_window": 60,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert isinstance(payload["results"], list)
    assert len(payload["results"]) >= 5
    assert "summary" in payload
    assert "interpretation" in payload

    strategies = {row["strategy"] for row in payload["results"]}
    assert "ma_crossover" in strategies
    assert "momentum" in strategies
    assert "buy_and_hold" in strategies

    combined_modes = {
        row["strategy_config"].get("combined_mode")
        for row in payload["results"]
        if row["strategy"] == "combined_signal"
    }
    assert "conservative" in combined_modes
    assert "aggressive" in combined_modes

    for row in payload["results"]:
        assert row["label"]
        assert row["strategy"]
        assert "metrics" in row
        assert "strategy_config" in row
        assert "total_return" in row["metrics"]


def test_compare_strategies_invalid_windows() -> None:
    response = client.post(
        COMPARE_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "short_window": 60,
            "long_window": 20,
        },
    )

    assert response.status_code in (400, 422)


def test_single_backtest_still_works() -> None:
    response = client.post(
        BACKTEST_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "strategy": "ma_crossover",
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "trade_log" in payload
    assert payload["strategy"] == "ma_crossover"
