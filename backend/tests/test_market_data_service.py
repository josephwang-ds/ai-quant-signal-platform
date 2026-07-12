"""MarketDataService 单元测试（含 Stooq mock）。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.services.market_data_service import MarketDataService


def _fake_ohlcv(symbol: str = "AAPL", source: str = "stooq", days: int = 5) -> pd.DataFrame:
    start = datetime(2024, 1, 2)
    rows = []
    for i in range(days):
        day = start + timedelta(days=i)
        rows.append(
            {
                "date": day,
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100.5 + i,
                "volume": 1_000_000 + i,
                "symbol": symbol,
                "ticker": symbol,
                "data_source": source,
            }
        )
    return pd.DataFrame(rows)


def test_unsupported_data_source() -> None:
    service = MarketDataService()
    with pytest.raises(ValueError, match="Unsupported data source"):
        service.get_price_history(
            symbol="AAPL",
            start_date="2022-01-01",
            data_source="unknown",
        )


def test_auto_fallback_uses_first_success(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MarketDataService()
    calls: list[str] = []

    def fake_akshare(request):
        calls.append("akshare")
        return _fake_ohlcv(source="akshare")

    def fake_yahoo(request):
        calls.append("yahoo")
        raise ValueError("yahoo down")

    def fake_stooq(request):
        calls.append("stooq")
        raise ValueError("stooq down")

    monkeypatch.setattr(service.providers["akshare"], "get_price_history", fake_akshare)
    monkeypatch.setattr(service.providers["yahoo"], "get_price_history", fake_yahoo)
    monkeypatch.setattr(service.providers["stooq"], "get_price_history", fake_stooq)

    df = service.get_price_history(symbol="AAPL", start_date="2024-01-01", data_source="auto")
    assert not df.empty
    assert df["data_source"].iloc[0] == "akshare"
    assert calls == ["akshare"]


def test_auto_fallback_skips_failed_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MarketDataService()

    def fake_akshare(request):
        raise ValueError("akshare blocked")

    def fake_yahoo(request):
        return _fake_ohlcv(source="yahoo")

    monkeypatch.setattr(service.providers["akshare"], "get_price_history", fake_akshare)
    monkeypatch.setattr(service.providers["yahoo"], "get_price_history", fake_yahoo)

    df = service.get_price_history(symbol="AAPL", start_date="2024-01-01", data_source="auto")
    assert df["data_source"].iloc[0] == "yahoo"


def test_a_share_auto_prefers_akshare(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MarketDataService()
    calls: list[str] = []

    def fake_akshare(request):
        calls.append("akshare")
        return _fake_ohlcv(symbol="600519.SS", source="akshare")

    def boom(request):
        calls.append("other")
        raise ValueError("should not be needed")

    monkeypatch.setattr(service.providers["akshare"], "get_price_history", fake_akshare)
    monkeypatch.setattr(service.providers["yahoo"], "get_price_history", boom)
    monkeypatch.setattr(service.providers["stooq"], "get_price_history", boom)

    df = service.get_price_history(
        symbol="600519.SS",
        start_date="2024-01-01",
        data_source="auto",
    )
    assert df["data_source"].iloc[0] == "akshare"
    assert calls == ["akshare"]


def test_manual_yahoo_skips_auto_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MarketDataService()
    calls: list[str] = []

    def fake_akshare(request):
        calls.append("akshare")
        raise ValueError("should not call akshare")

    def fake_yahoo(request):
        calls.append("yahoo")
        return _fake_ohlcv(source="yahoo")

    def fake_stooq(request):
        calls.append("stooq")
        raise ValueError("should not call stooq")

    monkeypatch.setattr(service.providers["akshare"], "get_price_history", fake_akshare)
    monkeypatch.setattr(service.providers["yahoo"], "get_price_history", fake_yahoo)
    monkeypatch.setattr(service.providers["stooq"], "get_price_history", fake_stooq)

    df = service.get_price_history(symbol="AAPL", start_date="2024-01-01", data_source="yahoo")
    assert df["data_source"].iloc[0] == "yahoo"
    assert calls == ["yahoo"]


def test_normalize_request_data_source() -> None:
    from app.schemas import normalize_request_data_source
    from pydantic import ValidationError

    from app.schemas import BacktestRequest

    assert normalize_request_data_source("AUTO") == "auto"
    assert normalize_request_data_source("yahoo") == "yahoo"

    with pytest.raises(ValueError, match="data_source must be"):
        normalize_request_data_source("polygon")

    with pytest.raises(ValidationError):
        BacktestRequest(ticker="AAPL", data_source="polygon")
