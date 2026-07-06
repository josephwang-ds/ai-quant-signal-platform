import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# 标准化后的 OHLCV 列名
OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


def load_price_data(
    ticker: str,
    start_date: str = "2022-01-01",
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    从 Yahoo Finance 下载指定股票的历史价格数据。

    参数:
        ticker: 股票代码，例如 "AAPL"
        start_date: 起始日期，格式 "YYYY-MM-DD"
        end_date: 可选结束日期（含当日）；yfinance 的 end 为 exclusive，内部会 +1 日历日

    返回:
        标准化列名的 DataFrame，包含 ticker 列

    异常:
        ValueError: 未找到任何有效数据时抛出
    """
    download_kwargs: dict = {
        "start": start_date,
        "auto_adjust": True,
        "progress": False,
    }

    if end_date:
        # yfinance 的 end 为 exclusive，用户传入 inclusive end_date 时需 +1 日历日
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        download_kwargs["end"] = (end_dt + timedelta(days=1)).isoformat()

    raw_df = yf.download(ticker, **download_kwargs)

    range_label = f"{start_date} to {end_date}" if end_date else f"since {start_date}"
    if raw_df is None or raw_df.empty:
        raise ValueError(
            f"No price data found for ticker '{ticker}' ({range_label})."
        )

    df = raw_df.copy()

    # 单 ticker 下载时，yfinance 有时返回 MultiIndex 列，需展平
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 将 Date 索引转为普通列，便于后续序列化
    df = df.reset_index()

    # 统一列名为小写
    rename_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=rename_map)

    # 只保留需要的 OHLCV 列
    missing_cols = [col for col in OHLCV_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Unexpected data format for ticker '{ticker}': missing columns {missing_cols}."
        )

    df = df[OHLCV_COLUMNS].copy()

    # 添加 ticker 列，统一为大写
    df["ticker"] = ticker.upper()

    # 丢弃含缺失值的行
    df = df.dropna(subset=["open", "high", "low", "close"])

    if df.empty:
        raise ValueError(
            f"No price data found for ticker '{ticker}' ({range_label})."
        )

    return df
