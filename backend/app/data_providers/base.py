"""行情数据提供方基础接口。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

import pandas as pd

REQUIRED_OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


@dataclass
class MarketDataRequest:
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market: Optional[str] = None
    data_source: str = "yahoo"
    adjustment: Optional[str] = None


class MarketDataProvider(Protocol):
    """统一行情数据提供方接口。"""

    name: str

    def get_price_history(self, request: MarketDataRequest) -> pd.DataFrame:
        """返回标准化 OHLCV DataFrame。"""
