import math

import pandas as pd

# 年化因子：交易日数量（用于波动率年化）
TRADING_DAYS_PER_YEAR = 252


def calculate_rsi(price: pd.Series, window: int = 14) -> pd.Series:
    """
    计算相对强弱指数（RSI）。

    参数:
        price: 收盘价序列
        window: 滚动窗口长度，默认 14

    返回:
        RSI 序列，取值范围 0–100
    """
    delta = price.diff()

    # 上涨幅度（正 delta）与下跌幅度（负 delta 取绝对值）
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    在 OHLCV DataFrame 上计算常用技术指标。

    新增列:
        daily_return, return_20d, return_60d,
        ma20, ma60, volatility_20d,
        volume_ma20, volume_change, rsi_14
    """
    result = df.copy()
    close = result["close"]
    volume = result["volume"]

    # 收益率类指标
    result["daily_return"] = close.pct_change()
    result["return_20d"] = close.pct_change(20)
    result["return_60d"] = close.pct_change(60)

    # 移动平均线
    result["ma20"] = close.rolling(20).mean()
    result["ma60"] = close.rolling(60).mean()

    # 20 日年化波动率
    result["volatility_20d"] = (
        result["daily_return"].rolling(20).std() * math.sqrt(TRADING_DAYS_PER_YEAR)
    )

    # 成交量相对变化
    result["volume_ma20"] = volume.rolling(20).mean()
    result["volume_change"] = volume / result["volume_ma20"] - 1

    # RSI
    result["rsi_14"] = calculate_rsi(close, window=14)

    return result
