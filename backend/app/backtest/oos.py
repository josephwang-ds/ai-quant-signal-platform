from typing import Any

import pandas as pd

from app.backtest.engine import run_ma_crossover_backtest
from app.backtest.metrics import calculate_backtest_metrics


def _rebase_segment_for_metrics(segment_df: pd.DataFrame) -> pd.DataFrame:
    """将切片区间内的累计收益重基准化，便于分段计算指标。"""
    seg = segment_df.copy()
    seg["cumulative_strategy"] = (1 + seg["strategy_return"]).cumprod()
    seg["cumulative_benchmark"] = (1 + seg["daily_return"]).cumprod()
    seg["strategy_drawdown"] = (
        seg["cumulative_strategy"] / seg["cumulative_strategy"].cummax() - 1
    )
    seg["benchmark_drawdown"] = (
        seg["cumulative_benchmark"] / seg["cumulative_benchmark"].cummax() - 1
    )
    seg["drawdown"] = seg["strategy_drawdown"]
    return seg


def _segment_summary(segment_df: pd.DataFrame) -> dict[str, Any]:
    """计算单个时间段的回测指标摘要。"""
    if segment_df.empty:
        raise ValueError("Segment is empty after split.")

    rebased = _rebase_segment_for_metrics(segment_df)
    start = rebased["date"].iloc[0]
    end = rebased["date"].iloc[-1]

    return {
        "period_start": start.strftime("%Y-%m-%d"),
        "period_end": end.strftime("%Y-%m-%d"),
        "rows": len(rebased),
        "metrics": calculate_backtest_metrics(rebased),
    }


def generate_oos_interpretation(segments: dict[str, dict[str, Any]]) -> list[str]:
    """生成样本外验证解读语句。"""
    sentences: list[str] = []

    in_metrics = segments["in_sample"]["metrics"]
    out_metrics = segments["out_of_sample"]["metrics"]

    in_return = in_metrics.get("total_return")
    out_return = out_metrics.get("total_return")
    out_sharpe = out_metrics.get("sharpe_ratio")
    out_benchmark = out_metrics.get("benchmark_return")
    out_strategy_dd = out_metrics.get("strategy_max_drawdown")
    out_benchmark_dd = out_metrics.get("benchmark_max_drawdown")

    if in_return is not None and out_return is not None:
        if in_return > 0 and out_return < 0:
            sentences.append(
                "The strategy worked in-sample but failed out-of-sample, "
                "which may indicate overfitting or regime change."
            )

    if out_return is not None and out_return > 0 and out_sharpe is not None and out_sharpe >= 0.5:
        sentences.append(
            "The strategy remained positive out-of-sample, "
            "which is a better validation sign."
        )

    if (
        out_return is not None
        and out_benchmark is not None
        and out_benchmark > out_return
    ):
        sentences.append(
            "The strategy underperformed buy-and-hold in the out-of-sample period."
        )

    if out_strategy_dd is not None and out_benchmark_dd is not None:
        if abs(out_strategy_dd) < abs(out_benchmark_dd):
            sentences.append(
                "The strategy reduced downside risk versus buy-and-hold out-of-sample."
            )

    sentences.append(
        "Out-of-sample validation helps test whether a strategy generalizes "
        "beyond the period used for initial research."
    )

    return sentences


def run_oos_validation(
    df: pd.DataFrame,
    split_date: str,
    short_window: int,
    long_window: int,
    transaction_cost: float,
) -> dict[str, dict[str, Any]]:
    """
    对固定参数策略做样本外切分验证。

    先在全量数据上运行一次回测，再按 split_date 切分并分别计算指标。
    """
    backtest_df = run_ma_crossover_backtest(
        df,
        short_window=short_window,
        long_window=long_window,
        transaction_cost=transaction_cost,
    )

    split_ts = pd.to_datetime(split_date)
    in_sample_df = backtest_df[backtest_df["date"] < split_ts]
    out_of_sample_df = backtest_df[backtest_df["date"] >= split_ts]

    if in_sample_df.empty:
        raise ValueError("In-sample period is empty after split.")
    if out_of_sample_df.empty:
        raise ValueError("Out-of-sample period is empty after split.")

    return {
        "full_period": _segment_summary(backtest_df),
        "in_sample": _segment_summary(in_sample_df),
        "out_of_sample": _segment_summary(out_of_sample_df),
    }
