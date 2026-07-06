"""Yahoo Finance 行情数据提供方。"""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from app.data_providers.base import MarketDataRequest, REQUIRED_OHLCV_COLUMNS

# 向后兼容：模块级常量
OHLCV_COLUMNS = REQUIRED_OHLCV_COLUMNS


class YahooProvider:
    """通过 yfinance 获取 Yahoo Finance 日线 OHLCV。"""

    name = "yahoo"

    def get_price_history(self, request: MarketDataRequest) -> pd.DataFrame:
        symbol = request.symbol.upper().strip()
        start_date = request.start_date or "2022-01-01"
        end_date = request.end_date

        download_kwargs: dict = {
            "start": start_date,
            "auto_adjust": True,
            "progress": False,
        }

        if end_date:
            # yfinance 的 end 为 exclusive，用户传入 inclusive end_date 时需 +1 日历日
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            download_kwargs["end"] = (end_dt + timedelta(days=1)).isoformat()

        raw_df = yf.download(symbol, **download_kwargs)

        range_label = f"{start_date} to {end_date}" if end_date else f"since {start_date}"
        if raw_df is None or raw_df.empty:
            raise ValueError(
                f"No price data found for ticker '{symbol}' ({range_label})."
            )

        df = raw_df.copy()

        # 单 ticker 下载时，yfinance 有时返回 MultiIndex 列，需展平
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        rename_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename_map)

        missing_cols = [col for col in OHLCV_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Unexpected data format for ticker '{symbol}': missing columns {missing_cols}."
            )

        df = df[OHLCV_COLUMNS].copy()
        df["symbol"] = symbol
        df["ticker"] = symbol
        df["data_source"] = "yahoo"

        if request.market:
            df["market"] = request.market
        if request.adjustment:
            df["adjustment"] = request.adjustment

        df = df.dropna(subset=["open", "high", "low", "close"])

        if df.empty:
            raise ValueError(
                f"No price data found for ticker '{symbol}' ({range_label})."
            )

        return df


def load_price_data(
    ticker: str,
    start_date: str = "2022-01-01",
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    从 Yahoo Finance 下载指定股票的历史价格数据。

    保留向后兼容的模块级 helper；内部委托 MarketDataService。
    """
    from app.services.market_data_service import get_market_data_service

    return get_market_data_service().get_price_history(
        symbol=ticker,
        start_date=start_date,
        end_date=end_date,
        data_source="yahoo",
    )
