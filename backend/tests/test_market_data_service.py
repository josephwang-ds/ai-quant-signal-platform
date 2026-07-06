"""MarketDataService 单元测试。"""

import pytest

from app.data_providers.base import REQUIRED_OHLCV_COLUMNS
from app.services.market_data_service import MarketDataService


def test_market_data_service_default_provider() -> None:
    service = MarketDataService()
    df = service.get_price_history(symbol="AAPL", start_date="2022-01-01")

    assert not df.empty
    for column in REQUIRED_OHLCV_COLUMNS:
        assert column in df.columns


def test_market_data_service_explicit_yahoo() -> None:
    service = MarketDataService()
    df = service.get_price_history(
        symbol="AAPL",
        start_date="2022-01-01",
        data_source="yahoo",
    )

    assert not df.empty
    for column in REQUIRED_OHLCV_COLUMNS:
        assert column in df.columns


def test_market_data_service_unsupported_provider() -> None:
    service = MarketDataService()

    with pytest.raises(ValueError, match="Unsupported data source: unknown"):
        service.get_price_history(
            symbol="AAPL",
            start_date="2022-01-01",
            data_source="unknown",
        )
