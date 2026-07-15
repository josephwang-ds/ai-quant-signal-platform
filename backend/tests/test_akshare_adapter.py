"""Offline tests for AkShare market-data adapter normalization."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.research_execution.akshare_adapter import (
    AKSHARE_ADJUSTMENT_DEFAULT,
    AkShareMarketDataAdapter,
)
from app.research_execution.market_data_port import (
    InsufficientHistoryError,
    InvalidProviderResponseError,
    MarketDataValidationError,
)
from app.research_execution.price_cache import PriceCache


def _akshare_raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "日期": [
                "2024-01-02",
                "2024-01-03",
                "2024-01-03",
                "2024-01-04",
            ],
            "开盘": [10.0, 10.5, 10.5, 10.8],
            "最高": [10.5, 11.0, 11.0, 11.2],
            "最低": [9.8, 10.2, 10.2, 10.5],
            "收盘": [10.2, 10.8, 10.8, 11.0],
            "成交量": [1000, 1100, 1100, 1200],
        }
    )


@pytest.fixture()
def adapter(tmp_path) -> AkShareMarketDataAdapter:
    return AkShareMarketDataAdapter(cache=PriceCache(root=tmp_path))


def test_akshare_normalizes_chinese_columns(monkeypatch, adapter) -> None:
    mock_ak = MagicMock()
    mock_ak.stock_zh_a_hist.return_value = _akshare_raw_frame()
    monkeypatch.setitem(
        __import__("sys").modules,
        "akshare",
        mock_ak,
    )

    series = adapter.get_daily_ohlcv("600519.SH", "2024-01-02", "2024-01-04")
    assert set(series.frame.columns) == {
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    }
    assert len(series.frame) == 3
    assert series.frame["date"].is_monotonic_increasing


def test_akshare_records_adjustment_and_provenance(monkeypatch, adapter) -> None:
    mock_ak = MagicMock()
    mock_ak.stock_zh_a_hist.return_value = _akshare_raw_frame()
    monkeypatch.setitem(__import__("sys").modules, "akshare", mock_ak)

    series = adapter.get_daily_ohlcv("000001.SZ", "2024-01-02", "2024-01-04")
    assert series.provenance.adjustment == AKSHARE_ADJUSTMENT_DEFAULT
    assert series.provenance.asset_class == "cn_equity"
    assert series.provenance.provider_symbol == "000001"
    assert series.provenance.exchange == "SZ"
    mock_ak.stock_zh_a_hist.assert_called_once()
    kwargs = mock_ak.stock_zh_a_hist.call_args.kwargs
    assert kwargs["adjust"] == "qfq"


def test_akshare_rejects_invalid_provider_response(monkeypatch, adapter) -> None:
    mock_ak = MagicMock()
    mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({"wrong": [1]})
    monkeypatch.setitem(__import__("sys").modules, "akshare", mock_ak)

    with pytest.raises(InvalidProviderResponseError):
        adapter.get_daily_ohlcv("600519.SH", "2024-01-02", "2024-01-04")


def test_akshare_rejects_non_cn_symbol(adapter) -> None:
    with pytest.raises(MarketDataValidationError):
        adapter.get_daily_ohlcv("AAPL", "2024-01-02")


def test_akshare_empty_range_is_insufficient(monkeypatch, adapter) -> None:
    mock_ak = MagicMock()
    mock_ak.stock_zh_a_hist.return_value = _akshare_raw_frame()
    monkeypatch.setitem(__import__("sys").modules, "akshare", mock_ak)

    with pytest.raises(InsufficientHistoryError):
        adapter.get_daily_ohlcv("600519.SH", "2025-01-01", "2025-01-02")
