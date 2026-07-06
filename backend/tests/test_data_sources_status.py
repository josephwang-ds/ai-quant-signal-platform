"""数据源状态端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATUS_URL = "/api/data-sources/status"
BACKTEST_URL = "/api/backtest"
MARKET_WATCH_URL = "/api/market-watch"


def test_data_sources_status() -> None:
    response = client.get(STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "yahoo"

    providers = {item["name"]: item for item in payload["providers"]}
    assert providers["yahoo"]["status"] == "active"
    assert providers["akshare"]["status"] == "planned"
    assert providers["coingecko"]["status"] == "planned"
    assert providers["csv"]["status"] == "planned"


def test_backtest_backward_compatible() -> None:
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
    assert payload["ticker"] == "AAPL"
    assert "metrics" in payload


def test_market_watch_backward_compatible() -> None:
    response = client.post(
        MARKET_WATCH_URL,
        json={
            "tickers": ["AAPL", "MSFT"],
            "lookback_days": 120,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) >= 1
