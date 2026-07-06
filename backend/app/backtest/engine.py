import pandas as pd

MA_BUY_REASON = (
    "Short moving average is above long moving average; strategy enters position."
)
MA_SELL_REASON = (
    "Short moving average is below or equal to long moving average; strategy exits position."
)
MOMENTUM_BUY_REASON = "Past momentum return is positive; strategy enters position."
MOMENTUM_SELL_REASON = "Past momentum return is non-positive; strategy exits position."
COMBINED_CONSERVATIVE_BUY_REASON = (
    "Both MA crossover and momentum signals are positive; strategy enters position."
)
COMBINED_CONSERVATIVE_SELL_REASON = (
    "At least one of MA crossover or momentum signals is no longer positive; "
    "strategy exits position."
)
COMBINED_AGGRESSIVE_BUY_REASON = (
    "At least one of MA crossover or momentum signals is positive; strategy enters position."
)
COMBINED_AGGRESSIVE_SELL_REASON = (
    "Both MA crossover and momentum signals are non-positive; strategy exits position."
)


def build_ma_signal(
    df: pd.DataFrame,
    short_window: int,
    long_window: int,
) -> pd.DataFrame:
    """计算双均线及均线交叉信号列。"""
    result = df.copy()
    close = result["close"]
    result["ma_short"] = close.rolling(short_window).mean()
    result["ma_long"] = close.rolling(long_window).mean()
    result["ma_signal"] = (result["ma_short"] > result["ma_long"]).astype(int)
    return result


def build_momentum_signal(df: pd.DataFrame, momentum_window: int) -> pd.DataFrame:
    """计算动量收益与动量信号列。"""
    result = df.copy()
    close = result["close"]
    result["momentum_return"] = close / close.shift(momentum_window) - 1
    result["momentum_signal"] = (result["momentum_return"] > 0).astype(int)
    return result


def build_combined_signal(
    df: pd.DataFrame,
    short_window: int,
    long_window: int,
    momentum_window: int,
    combined_mode: str,
) -> pd.DataFrame:
    """合并均线与动量信号，生成组合信号列。"""
    result = build_ma_signal(df, short_window, long_window)
    momentum_part = build_momentum_signal(df, momentum_window)
    result["momentum_return"] = momentum_part["momentum_return"]
    result["momentum_signal"] = momentum_part["momentum_signal"]

    if combined_mode == "conservative":
        result["combined_signal"] = (
            (result["ma_signal"] == 1) & (result["momentum_signal"] == 1)
        ).astype(int)
    else:
        result["combined_signal"] = (
            (result["ma_signal"] == 1) | (result["momentum_signal"] == 1)
        ).astype(int)

    result["combined_mode"] = combined_mode
    return result


def _add_trade_columns(
    result: pd.DataFrame,
    buy_reason: str,
    sell_reason: str,
) -> pd.DataFrame:
    """根据持仓变化生成买卖动作与原因列。"""
    position_diff = result["position"].diff().fillna(0)
    result["trade_action"] = None
    result["trade_reason"] = None
    result.loc[position_diff == 1, "trade_action"] = "BUY"
    result.loc[position_diff == 1, "trade_reason"] = buy_reason
    result.loc[position_diff == -1, "trade_action"] = "SELL"
    result.loc[position_diff == -1, "trade_reason"] = sell_reason
    return result


def apply_position_and_returns(
    result: pd.DataFrame,
    signal_col: str,
    transaction_cost: float,
    buy_reason: str,
    sell_reason: str,
) -> pd.DataFrame:
    """将信号列转为次日持仓，并计算收益、回撤与交易列。"""
    close = result["close"]

    result["signal"] = result[signal_col].astype(int)
    result["position"] = result["signal"].shift(1).fillna(0)

    if "daily_return" not in result.columns:
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
    result["drawdown"] = result["strategy_drawdown"]

    return _add_trade_columns(result, buy_reason, sell_reason)


def run_ma_crossover_backtest(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 60,
    transaction_cost: float = 0.001,
) -> pd.DataFrame:
    """
    双均线交叉策略回测（无前瞻偏差：当日信号次日持仓）。
    """
    result = build_ma_signal(df, short_window, long_window)
    result = apply_position_and_returns(
        result,
        signal_col="ma_signal",
        transaction_cost=transaction_cost,
        buy_reason=MA_BUY_REASON,
        sell_reason=MA_SELL_REASON,
    )
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
    """
    result = build_momentum_signal(df, momentum_window)
    result = apply_position_and_returns(
        result,
        signal_col="momentum_signal",
        transaction_cost=transaction_cost,
        buy_reason=MOMENTUM_BUY_REASON,
        sell_reason=MOMENTUM_SELL_REASON,
    )
    result = result.dropna(subset=["momentum_return"])

    if result.empty:
        raise ValueError(
            "Not enough data to run backtest after applying momentum window."
        )

    return result


def run_combined_signal_backtest(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 60,
    momentum_window: int = 60,
    combined_mode: str = "conservative",
    transaction_cost: float = 0.001,
) -> pd.DataFrame:
    """
    组合信号策略回测（均线 + 动量，保守或进取模式）。
    """
    if combined_mode == "conservative":
        buy_reason = COMBINED_CONSERVATIVE_BUY_REASON
        sell_reason = COMBINED_CONSERVATIVE_SELL_REASON
    else:
        buy_reason = COMBINED_AGGRESSIVE_BUY_REASON
        sell_reason = COMBINED_AGGRESSIVE_SELL_REASON

    result = build_combined_signal(
        df,
        short_window=short_window,
        long_window=long_window,
        momentum_window=momentum_window,
        combined_mode=combined_mode,
    )
    result = apply_position_and_returns(
        result,
        signal_col="combined_signal",
        transaction_cost=transaction_cost,
        buy_reason=buy_reason,
        sell_reason=sell_reason,
    )
    result = result.dropna(subset=["ma_short", "ma_long", "momentum_return"])

    if result.empty:
        raise ValueError(
            "Not enough data to run backtest after applying combined signal windows."
        )

    return result
