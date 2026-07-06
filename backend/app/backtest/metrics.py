import math
from typing import Any, Optional

import pandas as pd

# 年化交易日数
TRADING_DAYS_PER_YEAR = 252


def _strategy_drawdown_series(df: pd.DataFrame) -> pd.Series:
    """获取策略回撤序列；兼容旧版 drawdown 列。"""
    if "strategy_drawdown" in df.columns:
        return df["strategy_drawdown"]
    if "drawdown" in df.columns:
        return df["drawdown"]
    raise ValueError("Strategy drawdown data is not available.")


def _benchmark_drawdown_series(df: pd.DataFrame) -> pd.Series:
    """获取基准回撤序列；缺失时由 cumulative_benchmark 计算。"""
    if "benchmark_drawdown" in df.columns:
        return df["benchmark_drawdown"]
    return df["cumulative_benchmark"] / df["cumulative_benchmark"].cummax() - 1


def calculate_backtest_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """
    从回测结果 DataFrame 计算绩效指标。

    异常:
        ValueError: 数据为空时无法计算
    """
    if df.empty:
        raise ValueError("Not enough data to calculate backtest metrics.")

    total_return = float(df["cumulative_strategy"].iloc[-1]) - 1
    benchmark_return = float(df["cumulative_benchmark"].iloc[-1]) - 1

    years = len(df) / TRADING_DAYS_PER_YEAR
    cagr: Optional[float]
    if years <= 0:
        cagr = None
    else:
        cagr = (1 + total_return) ** (1 / years) - 1

    strategy_return = df["strategy_return"]
    std = float(strategy_return.std())

    volatility = std * math.sqrt(TRADING_DAYS_PER_YEAR)

    if std == 0 or math.isnan(std):
        sharpe_ratio: Optional[float] = None
    else:
        sharpe_ratio = (
            float(strategy_return.mean()) / std * math.sqrt(TRADING_DAYS_PER_YEAR)
        )

    strategy_drawdown = _strategy_drawdown_series(df)
    benchmark_drawdown = _benchmark_drawdown_series(df)

    strategy_max_drawdown = float(strategy_drawdown.min())
    benchmark_max_drawdown = float(benchmark_drawdown.min())

    win_rate = float((strategy_return > 0).mean())
    number_of_trades = float(df["trade"].sum())
    transaction_cost_total = float(df["cost"].sum())

    return {
        "total_return": round(total_return, 6),
        "benchmark_return": round(benchmark_return, 6),
        "cagr": round(cagr, 6) if cagr is not None else None,
        "volatility": round(volatility, 6),
        "sharpe_ratio": round(sharpe_ratio, 6) if sharpe_ratio is not None else None,
        "max_drawdown": round(strategy_max_drawdown, 6),
        "strategy_max_drawdown": round(strategy_max_drawdown, 6),
        "benchmark_max_drawdown": round(benchmark_max_drawdown, 6),
        "win_rate": round(win_rate, 6),
        "number_of_trades": round(number_of_trades, 4),
        "transaction_cost_total": round(transaction_cost_total, 6),
    }
