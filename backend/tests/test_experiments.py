"""Experiments Persistence v1 TestClient 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.db.repositories.backtest_runs import DatabaseUnavailableError
from app.main import app

client = TestClient(app)

EXPERIMENTS_URL = "/api/experiments/backtest-runs"
BACKTEST_URL = "/api/backtest"
MARKET_WATCH_URL = "/api/market-watch"

SAMPLE_SAVE_PAYLOAD = {
    "ticker": "AAPL",
    "data_source": "Yahoo Finance via yfinance",
    "strategy": "ma_crossover",
    "strategy_config": {
        "strategy": "ma_crossover",
        "short_window": 20,
        "long_window": 60,
        "momentum_window": 60,
        "combined_mode": "conservative",
        "transaction_cost": 0.001,
    },
    "start_date": "2022-01-01",
    "end_date": None,
    "transaction_cost": 0.001,
    "metrics": {
        "total_return": 0.12,
        "sharpe_ratio": 0.8,
        "max_drawdown": -0.15,
    },
    "notes": "demo save",
    "trade_log": [
        {
            "date": "2022-03-01",
            "action": "BUY",
            "price": 150.0,
            "signal": 1,
            "position_after": 1,
            "reason": "MA crossover bullish",
        }
    ],
}


def test_save_backtest_run_when_db_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    response = client.post(EXPERIMENTS_URL, json=SAMPLE_SAVE_PAYLOAD)

    assert response.status_code == 503
    assert "SUPABASE_DB_URL" in response.json()["detail"]


def test_list_backtest_runs_when_db_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    response = client.get(EXPERIMENTS_URL)

    assert response.status_code == 503


def test_save_and_get_backtest_run_mocked(monkeypatch) -> None:
    saved = {
        "id": "11111111-1111-1111-1111-111111111111",
        "ticker": "AAPL",
        "market": None,
        "data_source": "yahoo",
        "strategy": "ma_crossover",
        "strategy_config": SAMPLE_SAVE_PAYLOAD["strategy_config"],
        "start_date": "2022-01-01",
        "end_date": None,
        "transaction_cost": 0.001,
        "metrics": SAMPLE_SAVE_PAYLOAD["metrics"],
        "notes": "demo save",
        "created_at": "2026-07-08T12:00:00+00:00",
        "trades": [
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "trade_date": "2022-03-01",
                "action": "BUY",
                "price": 150.0,
                "signal": 1.0,
                "position_after": 1.0,
                "reason": "MA crossover bullish",
                "created_at": "2026-07-08T12:00:00+00:00",
            }
        ],
    }

    def mock_create(**kwargs) -> str:
        assert kwargs["ticker"] == "AAPL"
        assert kwargs["data_source"] == "yahoo"
        assert len(kwargs["trades"]) == 1
        return saved["id"]

    def mock_list(*, limit: int = 50, offset: int = 0):
        return [
            {
                **{k: v for k, v in saved.items() if k != "trades"},
                "trade_count": 1,
            }
        ]

    def mock_get(run_id: str):
        if run_id == saved["id"]:
            return saved
        return None

    monkeypatch.setattr(
        "app.api.routes.experiments.create_backtest_run",
        mock_create,
    )
    monkeypatch.setattr(
        "app.api.routes.experiments.list_backtest_runs",
        mock_list,
    )
    monkeypatch.setattr(
        "app.api.routes.experiments.get_backtest_run",
        mock_get,
    )

    save_response = client.post(EXPERIMENTS_URL, json=SAMPLE_SAVE_PAYLOAD)
    assert save_response.status_code == 200
    assert save_response.json()["id"] == saved["id"]

    list_response = client.get(EXPERIMENTS_URL)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["ticker"] == "AAPL"

    detail_response = client.get(f"{EXPERIMENTS_URL}/{saved['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == saved["id"]
    assert len(detail["trades"]) == 1


def test_get_backtest_run_not_found_mocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.experiments.get_backtest_run",
        lambda run_id: None,
    )

    response = client.get(
        f"{EXPERIMENTS_URL}/11111111-1111-1111-1111-111111111111"
    )
    assert response.status_code == 404


def test_delete_backtest_run_mocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.experiments.delete_backtest_run",
        lambda run_id: True,
    )

    response = client.delete(
        f"{EXPERIMENTS_URL}/11111111-1111-1111-1111-111111111111"
    )
    assert response.status_code == 200
    assert response.json()["id"] == "11111111-1111-1111-1111-111111111111"


def test_database_unavailable_maps_to_503(monkeypatch) -> None:
    def raise_unavailable(**kwargs):
        raise DatabaseUnavailableError("Database connection failed.")

    monkeypatch.setattr(
        "app.api.routes.experiments.create_backtest_run",
        raise_unavailable,
    )

    response = client.post(EXPERIMENTS_URL, json=SAMPLE_SAVE_PAYLOAD)
    assert response.status_code == 503


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
        json={"tickers": ["AAPL"], "lookback_days": 120},
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1
