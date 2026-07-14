"""
Deterministic MA crossover research calculations.

Annualization: 252 trading days.
Transaction cost: applied per unit position change (|Δposition| × cost).
  For 0/1 positions this equals cost per entry or exit (position change).
Position: signal shifted by one trading day (no look-ahead).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

TRADING_DAYS_PER_YEAR = 252


@dataclass
class MetricBundle:
    total_return: float | None
    cagr: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    maximum_drawdown: float | None
    trade_count: int | None
    win_rate: float | None
    turnover: float | None
    total_transaction_costs: float | None
    observation_count: int
    start_date: str | None
    end_date: str | None


@dataclass
class BacktestResult:
    frame: pd.DataFrame
    strategy_metrics: MetricBundle
    benchmark_metrics: MetricBundle
    warnings: list[str] = field(default_factory=list)


def _json_safe(value: float | None) -> float | None:
    if value is None:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return float(value)


def _cagr(total_return: float, n_obs: int) -> tuple[float | None, str | None]:
    years = n_obs / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return None, "CAGR undefined: non-positive observation span."
    if total_return <= -1:
        return None, "CAGR undefined: total return ≤ -100%."
    try:
        value = (1 + total_return) ** (1 / years) - 1
    except (OverflowError, ValueError):
        return None, "CAGR calculation overflow."
    safe = _json_safe(value)
    if safe is None:
        return None, "CAGR not finite."
    return safe, None


def _sharpe(
    daily_returns: pd.Series,
    risk_free_rate: float,
) -> tuple[float | None, str | None]:
    excess = daily_returns - (risk_free_rate / TRADING_DAYS_PER_YEAR)
    std = float(excess.std(ddof=1)) if len(excess) > 1 else float("nan")
    if std == 0 or math.isnan(std):
        return None, "Sharpe undefined: zero or missing return volatility."
    mean = float(excess.mean())
    value = mean / std * math.sqrt(TRADING_DAYS_PER_YEAR)
    safe = _json_safe(value)
    if safe is None:
        return None, "Sharpe not finite."
    return safe, None


def _max_drawdown(cum: pd.Series) -> float | None:
    if cum.empty:
        return None
    dd = cum / cum.cummax() - 1
    return _json_safe(float(dd.min()))


def run_ma_crossover_research(
    prices: pd.DataFrame,
    *,
    short_window: int = 20,
    long_window: int = 60,
    transaction_cost: float = 0.001,
    risk_free_rate: float = 0.0,
) -> BacktestResult:
    """
    MA crossover research backtest on normalized OHLCV.

    Price series: uses adjusted_close when present, else close.
    Trade count: number of days with turnover > 0 after warm-up
    (entries + exits); initial NaN→first-position fill is not counted.
    Win rate: among days with non-zero position, share with net_strategy_return > 0.
    """
    warnings: list[str] = []
    if short_window <= 0 or long_window <= 0:
        raise ValueError("Windows must be positive integers.")
    if short_window >= long_window:
        raise ValueError("short_window must be < long_window.")
    if transaction_cost < 0:
        raise ValueError("transaction_cost must be >= 0.")
    if len(prices) < long_window + 2:
        raise ValueError(
            f"Insufficient history: need at least {long_window + 2} rows "
            f"for long_window={long_window}; got {len(prices)}."
        )

    df = prices.copy()
    price = df["adjusted_close"] if "adjusted_close" in df.columns else df["close"]
    df = df.copy()
    df["price"] = price
    df["ma_short"] = df["price"].rolling(short_window).mean()
    df["ma_long"] = df["price"].rolling(long_window).mean()
    df["signal"] = (df["ma_short"] > df["ma_long"]).astype(int)
    # One-day lag — no look-ahead. Warm-up rows stay NaN until first valid lag.
    df["position"] = df["signal"].shift(1)

    df["daily_return"] = df["price"].pct_change()
    # Exclude warm-up where MAs or lagged position are unavailable.
    valid = df.dropna(subset=["ma_short", "ma_long", "position", "daily_return"]).copy()
    if valid.empty:
        raise ValueError("No valid observation rows after MA warm-up and position lag.")

    valid["position"] = valid["position"].astype(float)
    valid["turnover"] = valid["position"].diff().abs().fillna(0.0)
    # First valid row is not a trade inception count from NaN→value.
    valid.iloc[0, valid.columns.get_loc("turnover")] = 0.0

    valid["gross_strategy_return"] = valid["position"] * valid["daily_return"]
    valid["transaction_cost"] = valid["turnover"] * transaction_cost
    valid["net_strategy_return"] = (
        valid["gross_strategy_return"] - valid["transaction_cost"]
    )
    valid["cumulative_strategy"] = (1 + valid["net_strategy_return"]).cumprod()
    valid["cumulative_benchmark"] = (1 + valid["daily_return"]).cumprod()

    strat_total = float(valid["cumulative_strategy"].iloc[-1] - 1)
    bench_total = float(valid["cumulative_benchmark"].iloc[-1] - 1)
    n = len(valid)

    strat_cagr, w = _cagr(strat_total, n)
    if w:
        warnings.append(w)
    bench_cagr, w = _cagr(bench_total, n)
    if w:
        warnings.append(w.replace("CAGR", "Benchmark CAGR", 1))

    strat_vol = _json_safe(
        float(valid["net_strategy_return"].std(ddof=1)) * math.sqrt(TRADING_DAYS_PER_YEAR)
        if n > 1
        else float("nan")
    )
    if strat_vol is None:
        warnings.append("Strategy annualized volatility not finite.")

    bench_vol = _json_safe(
        float(valid["daily_return"].std(ddof=1)) * math.sqrt(TRADING_DAYS_PER_YEAR)
        if n > 1
        else float("nan")
    )

    sharpe, w = _sharpe(valid["net_strategy_return"], risk_free_rate)
    if w:
        warnings.append(w)
    bench_sharpe, w = _sharpe(valid["daily_return"], risk_free_rate)
    if w:
        warnings.append(w.replace("Sharpe", "Benchmark Sharpe", 1))

    # Trade count = number of non-zero position changes after warm-up.
    trade_count = int((valid["turnover"] > 0).sum())
    turnover_total = float(valid["turnover"].sum())
    total_costs = float(valid["transaction_cost"].sum())

    active = valid.loc[valid["position"] != 0, "net_strategy_return"]
    if len(active) == 0:
        win_rate = None
        warnings.append("Win rate undefined: no days with non-zero position.")
    else:
        win_rate = _json_safe(float((active > 0).mean()))

    start = str(pd.Timestamp(valid["date"].iloc[0]).date())
    end = str(pd.Timestamp(valid["date"].iloc[-1]).date())

    strategy_metrics = MetricBundle(
        total_return=_json_safe(strat_total),
        cagr=strat_cagr,
        annualized_volatility=strat_vol,
        sharpe_ratio=sharpe,
        maximum_drawdown=_max_drawdown(valid["cumulative_strategy"]),
        trade_count=trade_count,
        win_rate=win_rate,
        turnover=_json_safe(turnover_total),
        total_transaction_costs=_json_safe(total_costs),
        observation_count=n,
        start_date=start,
        end_date=end,
    )
    benchmark_metrics = MetricBundle(
        total_return=_json_safe(bench_total),
        cagr=bench_cagr,
        annualized_volatility=bench_vol,
        sharpe_ratio=bench_sharpe,
        maximum_drawdown=_max_drawdown(valid["cumulative_benchmark"]),
        trade_count=None,
        win_rate=_json_safe(float((valid["daily_return"] > 0).mean())),
        turnover=None,
        total_transaction_costs=0.0,
        observation_count=n,
        start_date=start,
        end_date=end,
    )

    return BacktestResult(
        frame=valid,
        strategy_metrics=strategy_metrics,
        benchmark_metrics=benchmark_metrics,
        warnings=warnings,
    )


def metrics_to_dict(bundle: MetricBundle) -> dict[str, Any]:
    return {
        "total_return": bundle.total_return,
        "cagr": bundle.cagr,
        "annualized_volatility": bundle.annualized_volatility,
        "sharpe_ratio": bundle.sharpe_ratio,
        "maximum_drawdown": bundle.maximum_drawdown,
        "trade_count": bundle.trade_count,
        "win_rate": bundle.win_rate,
        "turnover": bundle.turnover,
        "total_transaction_costs": bundle.total_transaction_costs,
        "observation_count": bundle.observation_count,
        "start_date": bundle.start_date,
        "end_date": bundle.end_date,
    }


def series_to_records(frame: pd.DataFrame, *, max_points: int = 2500) -> list[dict[str, Any]]:
    cols = [
        "date",
        "price",
        "signal",
        "position",
        "net_strategy_return",
        "daily_return",
        "cumulative_strategy",
        "cumulative_benchmark",
        "turnover",
        "transaction_cost",
    ]
    out = frame[cols].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    if len(out) > max_points:
        # Downsample evenly for response size; warn left to caller.
        idx = [
            int(round(i * (len(out) - 1) / (max_points - 1)))
            for i in range(max_points)
        ]
        out = out.iloc[sorted(set(idx))]
    records: list[dict[str, Any]] = []
    for row in out.itertuples(index=False):
        records.append(
            {
                "date": row.date,
                "price": _json_safe(float(row.price)),
                "signal": int(row.signal) if not math.isnan(float(row.signal)) else None,
                "position": _json_safe(float(row.position)),
                "strategy_return": _json_safe(float(row.net_strategy_return)),
                "benchmark_return": _json_safe(float(row.daily_return)),
                "cumulative_strategy": _json_safe(float(row.cumulative_strategy)),
                "cumulative_benchmark": _json_safe(float(row.cumulative_benchmark)),
                "turnover": _json_safe(float(row.turnover)),
                "transaction_cost": _json_safe(float(row.transaction_cost)),
            }
        )
    return records
