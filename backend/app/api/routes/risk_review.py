"""POST /api/v1/risk/review — backtest metrics → five-level risk assessment."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.backtest.engine import (
    run_combined_signal_backtest,
    run_ma_crossover_backtest,
    run_momentum_backtest,
)
from app.backtest.metrics import TRADING_DAYS_PER_YEAR, calculate_backtest_metrics
from app.data_providers.yahoo_provider import load_price_data
from app.risk.risk_monitor import RiskMonitorInput, calculate_overall_risk_level
from app.risk.risk_profile import resolve_risk_profile
from app.schemas import BacktestRequest, RiskReviewRequest

router = APIRouter(prefix="/api/v1/risk", tags=["risk-review"])

COMPONENT_KEYS = (
    "drawdown",
    "single_trade_loss",
    "consecutive_losses",
    "volatility",
    "sharpe_decline",
    "cost_drag",
    "signal_conflict",
)

RECENT_VOL_WINDOW = 60
MIN_RECENT_VOL_OBS = 20


def _resolve_data_source_label(df: pd.DataFrame) -> str:
    if df is None or getattr(df, "empty", True) or "data_source" not in df.columns:
        return "auto"
    raw = str(df["data_source"].iloc[0]).strip().lower()
    labels = {
        "stooq": "Stooq",
        "yahoo": "Yahoo Finance via yfinance",
        "akshare": "AKShare",
        "auto": "auto",
    }
    return labels.get(raw, raw or "auto")


def _run_backtest_frame(price_df: pd.DataFrame, request: BacktestRequest) -> pd.DataFrame:
    if request.strategy == "ma_crossover":
        return run_ma_crossover_backtest(
            price_df,
            short_window=request.short_window,
            long_window=request.long_window,
            transaction_cost=request.transaction_cost,
        )
    if request.strategy == "momentum":
        return run_momentum_backtest(
            price_df,
            momentum_window=request.momentum_window,
            transaction_cost=request.transaction_cost,
        )
    if request.strategy == "combined_signal":
        return run_combined_signal_backtest(
            price_df,
            short_window=request.short_window,
            long_window=request.long_window,
            momentum_window=request.momentum_window,
            combined_mode=request.combined_mode,
            transaction_cost=request.transaction_cost,
        )
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported strategy: '{request.strategy}'.",
    )


def _round_trip_returns(backtest_df: pd.DataFrame) -> list[float]:
    """Completed BUY→SELL round-trip returns from authentic close prices."""
    if backtest_df.empty or "trade_action" not in backtest_df.columns:
        return []

    returns: list[float] = []
    entry_price: float | None = None
    for _, row in backtest_df.iterrows():
        action = row.get("trade_action")
        if action is None or (isinstance(action, float) and math.isnan(action)):
            continue
        if action == "BUY":
            entry_price = float(row["close"])
        elif action == "SELL" and entry_price is not None and entry_price > 0:
            returns.append(float(row["close"]) / entry_price - 1.0)
            entry_price = None
    return returns


def _consecutive_losses_and_last_loss(
    backtest_df: pd.DataFrame,
) -> tuple[int, float | None]:
    """Trailing consecutive losing round-trips; last loss pct or None."""
    returns = _round_trip_returns(backtest_df)
    if not returns:
        return 0, None

    consecutive = 0
    for ret in reversed(returns):
        if ret < 0:
            consecutive += 1
        else:
            break

    last = returns[-1]
    last_trade_loss_pct = float(last) if last < 0 else None
    return consecutive, last_trade_loss_pct


def _gross_return(backtest_df: pd.DataFrame) -> float | None:
    """Pre-cost cumulative strategy return when the column exists."""
    if backtest_df.empty or "strategy_return_before_cost" not in backtest_df.columns:
        return None
    series = backtest_df["strategy_return_before_cost"].dropna()
    if series.empty:
        return None
    return float((1.0 + series).prod() - 1.0)


def _cost_drag_ratio(metrics: dict[str, Any], backtest_df: pd.DataFrame) -> float | None:
    cost_total = metrics.get("transaction_cost_total")
    gross = _gross_return(backtest_df)
    if cost_total is None or gross is None or gross <= 0:
        return None
    return float(cost_total) / float(gross)


def _annualized_volatility(returns: pd.Series) -> float | None:
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if len(clean) < MIN_RECENT_VOL_OBS:
        return None
    std = float(clean.std())
    if not math.isfinite(std) or std <= 0:
        return None
    return std * math.sqrt(TRADING_DAYS_PER_YEAR)


def _recent_vs_baseline_volatility(
    metrics: dict[str, Any],
    backtest_df: pd.DataFrame,
) -> tuple[float | None, float | None]:
    """
    Recent (~60d) annualized vol vs full-period metrics volatility.

    Returns (None, None) when either side is insufficient — honest degrade.
    """
    baseline_raw = metrics.get("volatility")
    if baseline_raw is None:
        return None, None
    try:
        baseline = float(baseline_raw)
    except (TypeError, ValueError):
        return None, None
    if not math.isfinite(baseline) or baseline <= 0:
        return None, None

    if backtest_df.empty or "daily_return" not in backtest_df.columns:
        return None, None

    recent = _annualized_volatility(backtest_df["daily_return"].tail(RECENT_VOL_WINDOW))
    if recent is None:
        return None, None
    return recent, baseline


def _current_drawdown_from_curve(backtest_df: pd.DataFrame) -> float:
    """Latest point on the strategy drawdown curve (0.0 if unavailable)."""
    for dd_col in ("strategy_drawdown", "drawdown"):
        if dd_col in backtest_df.columns and not backtest_df.empty:
            latest = backtest_df[dd_col].iloc[-1]
            if latest is not None and not (
                isinstance(latest, float) and math.isnan(latest)
            ):
                return float(latest)
    return 0.0


def _historical_max_drawdown(metrics: dict[str, Any]) -> float:
    value = metrics.get("strategy_max_drawdown")
    if value is None:
        value = metrics.get("max_drawdown")
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_risk_monitor_input(
    metrics: dict[str, Any],
    backtest_df: pd.DataFrame,
    *,
    drawdown_mode: str = "current",
) -> RiskMonitorInput:
    """Map real backtest metrics into RiskMonitorInput — never invent values."""
    if drawdown_mode == "historical":
        drawdown = _historical_max_drawdown(metrics)
    else:
        # Default: latest drawdown on the equity curve (live posture), not full-history min.
        drawdown = _current_drawdown_from_curve(backtest_df)

    consecutive_losses, last_trade_loss_pct = _consecutive_losses_and_last_loss(
        backtest_df
    )
    recent_vol, baseline_vol = _recent_vs_baseline_volatility(metrics, backtest_df)

    return RiskMonitorInput(
        current_drawdown=float(drawdown),
        last_trade_loss_pct=last_trade_loss_pct,
        consecutive_losses=consecutive_losses,
        volatility=recent_vol,
        baseline_volatility=baseline_vol,
        sharpe_ratio=metrics.get("sharpe_ratio"),
        recent_sharpe=None,
        cost_drag_ratio=_cost_drag_ratio(metrics, backtest_df),
        ma_signal=None,
        momentum_signal=None,
    )


@router.post("/review")
def review_risk(request: RiskReviewRequest) -> dict[str, Any]:
    """
    Run one backtest, map authentic metrics into the risk engine, return assessment.
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None
    profile = resolve_risk_profile(
        request.risk_profile,
        drawdown_mode=request.drawdown_mode,
    )

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
            data_source=request.data_source,
        )
        backtest_df = _run_backtest_frame(price_df, request)
        metrics = calculate_backtest_metrics(backtest_df)
        assessment = calculate_overall_risk_level(
            build_risk_monitor_input(
                metrics,
                backtest_df,
                drawdown_mode=request.drawdown_mode,
            ),
            profile=profile,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run risk review for '{request.ticker}': {exc}",
        ) from exc

    return {
        "ticker": request.ticker,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "end_date": normalized_end_date,
        "data_source": _resolve_data_source_label(price_df),
        "drawdown_mode": request.drawdown_mode,
        "risk_profile": request.risk_profile,
        "metrics": metrics,
        "risk": assessment.to_dict(),
    }
