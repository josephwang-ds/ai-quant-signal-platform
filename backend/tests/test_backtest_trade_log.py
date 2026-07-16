"""回测交易记录 TestClient 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BACKTEST_URL = "/api/backtest"

REQUIRED_TRADE_LOG_FIELDS = [
    "date",
    "action",
    "price",
    "reason",
    "position_after",
]


@pytest.mark.live
def test_ma_crossover_backtest_includes_trade_log() -> None:
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
    assert isinstance(payload["trade_log"], list)

    trade_log = payload["trade_log"]
    if trade_log:
        for row in trade_log:
            for field in REQUIRED_TRADE_LOG_FIELDS:
                assert field in row
            assert row["action"] in ("BUY", "SELL")
            assert isinstance(row["price"], (int, float))
            assert row["reason"]

    first_data_row = payload["data"][0]
    assert "trade_action" in first_data_row
    assert "trade_reason" in first_data_row
    assert "ma_signal" in first_data_row
