import pandas as pd


def run_ma_crossover_backtest(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 60,
    transaction_cost: float = 0.001,
) -> pd.DataFrame:
    """
    双均线交叉策略回测（无前瞻偏差：当日信号次日持仓）。

    参数:
        df: 含 close 列的价格 DataFrame
        short_window: 短期均线窗口
        long_window: 长期均线窗口
        transaction_cost: 单边交易成本比例

    返回:
        含信号、持仓、收益与累计净值列的 DataFrame
    """
    result = df.copy()
    close = result["close"]

    result["ma_short"] = close.rolling(short_window).mean()
    result["ma_long"] = close.rolling(long_window).mean()

    # 短期均线在长期均线上方则做多，否则空仓
    result["signal"] = (result["ma_short"] > result["ma_long"]).astype(int)

    # 次日生效，避免 look-ahead bias
    result["position"] = result["signal"].shift(1).fillna(0)

    result["daily_return"] = close.pct_change().fillna(0)
    result["trade"] = result["position"].diff().abs().fillna(0)

    result["strategy_return_before_cost"] = result["position"] * result["daily_return"]
    result["cost"] = result["trade"] * transaction_cost
    result["strategy_return"] = result["strategy_return_before_cost"] - result["cost"]

    result["cumulative_strategy"] = (1 + result["strategy_return"]).cumprod()
    result["cumulative_benchmark"] = (1 + result["daily_return"]).cumprod()

    result["strategy_drawdown"] = (
        result["cumulative_strategy"] / result["cumulative_strategy"].cummax() - 1
    )
    result["benchmark_drawdown"] = (
        result["cumulative_benchmark"] / result["cumulative_benchmark"].cummax() - 1
    )
    # 向后兼容：drawdown 为 strategy_drawdown 别名
    result["drawdown"] = result["strategy_drawdown"]

    # 滚动窗口未就绪的行不参与回测统计
    result = result.dropna(subset=["ma_short", "ma_long"])

    if result.empty:
        raise ValueError(
            "Not enough data to run backtest after applying moving average windows."
        )

    return result


def run_momentum_backtest(
    df: pd.DataFrame,
    momentum_window: int = 60,
    transaction_cost: float = 0.001,
) -> pd.DataFrame:
    """
    动量策略回测（无前瞻偏差：当日信号次日持仓）。

    参数:
        df: 含 close 列的价格 DataFrame
        momentum_window: 动量回看窗口（日）
        transaction_cost: 单边交易成本比例

    返回:
        含动量信号、持仓、收益与累计净值列的 DataFrame
    """
    result = df.copy()
    close = result["close"]

    result["daily_return"] = close.pct_change().fillna(0)
    result["momentum_return"] = close.pct_change(momentum_window)

    # 过去 N 日收益为正则做多，否则空仓
    result["signal"] = (result["momentum_return"] > 0).astype(int)

    # 次日生效，避免 look-ahead bias
    result["position"] = result["signal"].shift(1).fillna(0)
    result["trade"] = result["position"].diff().abs().fillna(0)

    result["strategy_return_before_cost"] = result["position"] * result["daily_return"]
    result["cost"] = result["trade"] * transaction_cost
    result["strategy_return"] = result["strategy_return_before_cost"] - result["cost"]

    result["cumulative_strategy"] = (1 + result["strategy_return"]).cumprod()
    result["cumulative_benchmark"] = (1 + result["daily_return"]).cumprod()

    result["strategy_drawdown"] = (
        result["cumulative_strategy"] / result["cumulative_strategy"].cummax() - 1
    )
    result["benchmark_drawdown"] = (
        result["cumulative_benchmark"] / result["cumulative_benchmark"].cummax() - 1
    )
    result["drawdown"] = result["strategy_drawdown"]

    result = result.dropna(subset=["momentum_return"])

    if result.empty:
        raise ValueError(
            "Not enough data to run backtest after applying momentum window."
        )

    return result
