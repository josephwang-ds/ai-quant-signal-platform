"""数据库状态端点 TestClient 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DATABASE_STATUS_URL = "/api/database/status"
DATA_SOURCES_STATUS_URL = "/api/data-sources/status"
BACKTEST_URL = "/api/backtest"
MARKET_WATCH_URL = "/api/market-watch"


def test_database_status_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    response = client.get(DATABASE_STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is False
    assert payload["connected"] is False
    assert payload["database"] == "supabase_postgres"
    assert "SUPABASE_DB_URL" in payload["message"]


def test_database_status_connected_mock(monkeypatch) -> None:
    def mock_check() -> dict:
        return {
            "configured": True,
            "connected": True,
            "message": "Database connection successful.",
            "database": "supabase_postgres",
        }

    monkeypatch.setattr(
        "app.api.routes.database.check_database_connection",
        mock_check,
    )

    response = client.get(DATABASE_STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["connected"] is True
    assert payload["database"] == "supabase_postgres"


def test_data_sources_status_still_works() -> None:
    response = client.get(DATA_SOURCES_STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["routing_mode"] == "asset_class"
    providers = {item["name"]: item for item in payload["providers"]}
    assert providers["yahoo"]["installed"] is True
    assert "us_equity" in providers["yahoo"]["supported_assets"]
    assert providers["akshare"]["supported_assets"] == ["cn_equity"]


@pytest.mark.live
def test_backtest_still_works() -> None:
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
    assert response.json()["ticker"] == "AAPL"


@pytest.mark.live
def test_market_watch_still_works() -> None:
    response = client.post(
        MARKET_WATCH_URL,
        json={
            "tickers": ["AAPL"],
            "lookback_days": 120,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1
