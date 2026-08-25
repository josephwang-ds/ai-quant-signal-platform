"""Transparent buy-and-hold context, not a strategy backtest."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def historical_picture(
    prices: pd.DataFrame,
    ticker: str,
    benchmark: str = "SPY",
    years: int = 5,
    initial_investment: float = 10_000.0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Calculate same-period asset and benchmark history from adjusted closes."""
    required = {"ticker", "date", "close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"price panel missing columns: {sorted(missing)}")
    if years <= 0 or initial_investment <= 0:
        raise ValueError("years and initial_investment must be positive")

    symbols = [ticker.upper(), benchmark.upper()]
    frame = prices[prices["ticker"].str.upper().isin(symbols)].copy()
    frame["ticker"] = frame["ticker"].str.upper()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.pivot_table(index="date", columns="ticker", values="close", aggfunc="last")
    if any(symbol not in frame.columns for symbol in symbols):
        absent = [symbol for symbol in symbols if symbol not in frame.columns]
        raise ValueError(f"no price history for: {', '.join(absent)}")
    frame = frame[symbols].dropna()
    if frame.empty:
        raise ValueError("asset and benchmark have no overlapping observations")

    end = frame.index.max()
    start_boundary = end - pd.DateOffset(years=years)
    frame = frame.loc[frame.index >= start_boundary]
    if len(frame) < 2:
        raise ValueError("not enough overlapping price history")
    if (frame <= 0).any().any():
        raise ValueError("close prices must be positive")

    normalized = frame / frame.iloc[0]
    returns = frame.pct_change().dropna()
    asset_ret = returns[symbols[0]]
    benchmark_ret = returns[symbols[1]]
    elapsed_years = (frame.index[-1] - frame.index[0]).days / 365.2425

    asset_metrics = _series_metrics(normalized[symbols[0]], asset_ret, elapsed_years)
    benchmark_metrics = _series_metrics(
        normalized[symbols[1]], benchmark_ret, elapsed_years
    )
    benchmark_variance = float(benchmark_ret.var(ddof=1))
    beta = (
        float(asset_ret.cov(benchmark_ret) / benchmark_variance)
        if benchmark_variance > 0
        else None
    )
    correlation = float(asset_ret.corr(benchmark_ret))

    metrics: dict[str, Any] = {
        "initial_investment": initial_investment,
        "ending_value": float(initial_investment * normalized[symbols[0]].iloc[-1]),
        "asset": asset_metrics,
        "benchmark": benchmark_metrics,
        "relative_total_return": asset_metrics["total_return"]
        - benchmark_metrics["total_return"],
        "beta": beta,
        "correlation": correlation if not math.isnan(correlation) else None,
        "observations": len(frame),
        "dividends": "included when supplied by the adjusted-price vendor",
    }
    growth = [
        {
            "date": date.date().isoformat(),
            "asset_value": float(initial_investment * row[symbols[0]]),
            "benchmark_value": float(initial_investment * row[symbols[1]]),
        }
        for date, row in normalized.iterrows()
    ]
    return metrics, growth


def _series_metrics(
    normalized: pd.Series, returns: pd.Series, elapsed_years: float
) -> dict[str, float | int | None]:
    total_return = float(normalized.iloc[-1] - 1.0)
    cagr = float(normalized.iloc[-1] ** (1.0 / elapsed_years) - 1.0)
    volatility = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))
    drawdown = normalized / normalized.cummax() - 1.0
    worst_date = drawdown.idxmin()
    recovery = _recovery_sessions(normalized, worst_date)
    return {
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": volatility,
        "max_drawdown": float(drawdown.min()),
        "current_drawdown": float(drawdown.iloc[-1]),
        "max_drawdown_date": worst_date.date().isoformat(),
        "recovery_sessions": recovery,
        "worst_day": float(returns.min()),
    }


def _recovery_sessions(normalized: pd.Series, trough_date: pd.Timestamp) -> int | None:
    through_trough = normalized.loc[:trough_date]
    peak_date = through_trough.idxmax()
    peak_value = float(normalized.loc[peak_date])
    after_trough = normalized.loc[trough_date:]
    recovered = after_trough[after_trough >= peak_value]
    if recovered.empty:
        return None
    return int(normalized.loc[peak_date : recovered.index[0]].shape[0] - 1)
