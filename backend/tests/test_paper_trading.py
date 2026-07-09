"""模拟试盘 API 测试（mock 行情数据）。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.paper_trading import router
from app.trading.paper_state import reset_paper_account

paper_app = FastAPI()
paper_app.include_router(router)
client = TestClient(paper_app)

PAPER_DASHBOARD_URL = "/api/paper/dashboard"
PAPER_EXECUTE_URL = "/api/paper/execute"
PAPER_RESET_URL = "/api/paper/reset"


def _sample_price_frame():
    import pandas as pd

    dates = pd.date_range("2023-01-01", periods=120, freq="B")
    close = pd.Series(range(100, 220), index=dates, dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1_000_000,
        }
    )


def test_paper_dashboard_mocked(monkeypatch) -> None:
    reset_paper_account("test-dashboard")
    monkeypatch.setattr(
        "app.trading.paper_trading.load_price_data",
        lambda *args, **kwargs: _sample_price_frame(),
    )

    response = client.post(
        PAPER_DASHBOARD_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 5,
            "long_window": 20,
            "account_id": "test-dashboard",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["today_signal"]["symbol"] == "AAPL"
    assert 1 <= payload["risk"]["risk_level"] <= 5
    assert payload["account"]["initial_capital"] == 100000


def test_paper_reset() -> None:
    response = client.post(f"{PAPER_RESET_URL}?account_id=default")
    assert response.status_code == 200
    assert response.json()["account"]["cash"] == 100000
