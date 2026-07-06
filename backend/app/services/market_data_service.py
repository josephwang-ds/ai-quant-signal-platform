"""统一行情数据服务入口。"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.data_providers.base import MarketDataRequest, REQUIRED_OHLCV_COLUMNS
from app.data_providers.yahoo_provider import YahooProvider

# 缓存层未来将包装 MarketDataService，而非直接调用提供方。


class MarketDataService:
    """按 data_source 路由到具体行情提供方。"""

    def __init__(self) -> None:
        self.providers = {
            "yahoo": YahooProvider(),
        }

    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: Optional[str] = None,
        data_source: str = "yahoo",
        adjustment: Optional[str] = None,
    ) -> pd.DataFrame:
        provider = self.providers.get(data_source)
        if provider is None:
            raise ValueError(f"Unsupported data source: {data_source}")

        request = MarketDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_source=data_source,
            adjustment=adjustment,
        )
        df = provider.get_price_history(request)

        missing_cols = [col for col in REQUIRED_OHLCV_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Provider '{data_source}' returned incomplete data: missing {missing_cols}."
            )

        return df


_default_service: Optional[MarketDataService] = None


def get_market_data_service() -> MarketDataService:
    """返回进程内单例 MarketDataService。"""
    global _default_service
    if _default_service is None:
        _default_service = MarketDataService()
    return _default_service
