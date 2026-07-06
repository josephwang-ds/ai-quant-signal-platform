from typing import Any, Optional

from app.backtest.engine import (
    run_combined_signal_backtest,
    run_ma_crossover_backtest,
    run_momentum_backtest,
)
from app.backtest.metrics import calculate_backtest_metrics, calculate_buy_and_hold_metrics

COMPARISON_INTERPRETATION = [
    "Strategy comparison helps evaluate whether a rule improves return, reduces drawdown, "
    "or simply trades more often.",
    "Higher return is not always better if drawdown and turnover increase significantly.",
]


def _drawdown_value(metrics: dict[str, Any]) -> Optional[float]:
    value = metrics.get("strategy_max_drawdown")
    if value is None:
        value = metrics.get("max_drawdown")
    return value


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Optional[str]]:
    """根据各策略指标生成规则型摘要。"""
    summary: dict[str, Optional[str]] = {
        "best_total_return": None,
        "best_sharpe": None,
        "lowest_drawdown": None,
        "fewest_trades": None,
    }

    return_candidates = [
        (row["label"], row["metrics"].get("total_return"))
        for row in results
        if row["metrics"].get("total_return") is not None
    ]
    if return_candidates:
        summary["best_total_return"] = max(return_candidates, key=lambda item: item[1])[0]

    sharpe_candidates = [
        (row["label"], row["metrics"]["sharpe_ratio"])
        for row in results
        if row["metrics"].get("sharpe_ratio") is not None
    ]
    if sharpe_candidates:
        summary["best_sharpe"] = max(sharpe_candidates, key=lambda item: item[1])[0]

    drawdown_candidates = [
        (row["label"], _drawdown_value(row["metrics"]))
        for row in results
        if _drawdown_value(row["metrics"]) is not None
    ]
    if drawdown_candidates:
        summary["lowest_drawdown"] = max(drawdown_candidates, key=lambda item: item[1])[0]

    trade_candidates = [
        (row["label"], row["metrics"].get("number_of_trades"))
        for row in results
        if row["strategy"] != "buy_and_hold"
        and row["metrics"].get("number_of_trades") is not None
    ]
    if trade_candidates:
        summary["fewest_trades"] = min(trade_candidates, key=lambda item: item[1])[0]

    return summary


def run_strategy_comparison(
    price_df,
    *,
    ticker: str,
    transaction_cost: float,
    short_window: int,
    long_window: int,
    momentum_window: int,
) -> dict[str, Any]:
    """在同一价格数据上运行固定策略集合并返回紧凑对比结果。"""
    results: list[dict[str, Any]] = []

    ma_df = run_ma_crossover_backtest(
        price_df,
        short_window=short_window,
        long_window=long_window,
        transaction_cost=transaction_cost,
    )
    results.append(
        {
            "label": f"MA Crossover {short_window}/{long_window}",
            "strategy": "ma_crossover",
            "strategy_config": {
                "strategy": "ma_crossover",
                "short_window": short_window,
                "long_window": long_window,
                "momentum_window": momentum_window,
                "combined_mode": "conservative",
                "transaction_cost": transaction_cost,
            },
            "metrics": calculate_backtest_metrics(ma_df),
        }
    )

    momentum_df = run_momentum_backtest(
        price_df,
        momentum_window=momentum_window,
        transaction_cost=transaction_cost,
    )
    results.append(
        {
            "label": f"Momentum {momentum_window}",
            "strategy": "momentum",
            "strategy_config": {
                "strategy": "momentum",
                "short_window": short_window,
                "long_window": long_window,
                "momentum_window": momentum_window,
                "combined_mode": "conservative",
                "transaction_cost": transaction_cost,
            },
            "metrics": calculate_backtest_metrics(momentum_df),
        }
    )

    for combined_mode, label in (
        ("conservative", "Combined Conservative"),
        ("aggressive", "Combined Aggressive"),
    ):
        combined_df = run_combined_signal_backtest(
            price_df,
            short_window=short_window,
            long_window=long_window,
            momentum_window=momentum_window,
            combined_mode=combined_mode,
            transaction_cost=transaction_cost,
        )
        results.append(
            {
                "label": label,
                "strategy": "combined_signal",
                "strategy_config": {
                    "strategy": "combined_signal",
                    "short_window": short_window,
                    "long_window": long_window,
                    "momentum_window": momentum_window,
                    "combined_mode": combined_mode,
                    "transaction_cost": transaction_cost,
                },
                "metrics": calculate_backtest_metrics(combined_df),
            }
        )

    results.append(
        {
            "label": "Buy & Hold",
            "strategy": "buy_and_hold",
            "strategy_config": {},
            "metrics": calculate_buy_and_hold_metrics(ma_df),
        }
    )

    return {
        "results": results,
        "summary": _build_summary(results),
        "interpretation": COMPARISON_INTERPRETATION,
    }
