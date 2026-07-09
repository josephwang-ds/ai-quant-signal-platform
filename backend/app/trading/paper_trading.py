"""模拟试盘引擎：基于策略最新信号 + 五档风控。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.backtest.engine import (
    build_combined_signal,
    build_ma_signal,
    build_momentum_signal,
    run_combined_signal_backtest,
    run_ma_crossover_backtest,
    run_momentum_backtest,
)
from app.backtest.metrics import calculate_backtest_metrics
from app.data_providers.yahoo_provider import load_price_data
from app.risk.risk_monitor import (
    RiskMonitorInput,
    calculate_overall_risk_level,
    paper_action_allowed,
)
from app.risk.risk_profile import AGGRESSIVE_PROFILE
from app.trading.paper_state import (
    PaperAccountState,
    PaperTradeRecord,
    get_paper_account,
    is_in_cooldown,
    reset_paper_account,
)


def _signal_confidence(signal_value: int, ma_signal: int | None, momentum_signal: int | None) -> str:
    if ma_signal is None or momentum_signal is None:
        return "Medium" if signal_value == 1 else "Low"
    if signal_value == 1 and ma_signal == 1 and momentum_signal == 1:
        return "High"
    if signal_value == 0 and ma_signal == 0 and momentum_signal == 0:
        return "High"
    return "Medium"


def _derive_paper_action(
    target_position: int,
    current_position: int,
    risk_level: int,
    in_cooldown: bool,
) -> str:
    if in_cooldown or risk_level >= 5:
        return "SELL" if current_position > 0 else "WAIT"
    if target_position > current_position:
        desired = "BUY"
    elif target_position < current_position:
        desired = "SELL"
    else:
        desired = "HOLD"
    if not paper_action_allowed(risk_level, desired):
        if current_position > 0 and risk_level >= 3:
            return "HOLD"
        return "WAIT"
    return desired


def _run_backtest_frame(
    price_df: pd.DataFrame,
    strategy: str,
    *,
    short_window: int,
    long_window: int,
    momentum_window: int,
    combined_mode: str,
    transaction_cost: float,
) -> pd.DataFrame:
    if strategy == "ma_crossover":
        return run_ma_crossover_backtest(
            price_df,
            short_window=short_window,
            long_window=long_window,
            transaction_cost=transaction_cost,
        )
    if strategy == "momentum":
        return run_momentum_backtest(
            price_df,
            momentum_window=momentum_window,
            transaction_cost=transaction_cost,
        )
    if strategy == "combined_signal":
        return run_combined_signal_backtest(
            price_df,
            short_window=short_window,
            long_window=long_window,
            momentum_window=momentum_window,
            combined_mode=combined_mode,
            transaction_cost=transaction_cost,
        )
    raise ValueError(f"Unsupported strategy: {strategy}")


def _latest_signal_context(
    price_df: pd.DataFrame,
    strategy: str,
    *,
    short_window: int,
    long_window: int,
    momentum_window: int,
    combined_mode: str,
) -> dict[str, Any]:
    if strategy == "ma_crossover":
        frame = build_ma_signal(price_df, short_window, long_window)
        signal_col = "ma_signal"
    elif strategy == "momentum":
        frame = build_momentum_signal(price_df, momentum_window)
        signal_col = "momentum_signal"
    else:
        frame = build_combined_signal(
            price_df,
            short_window,
            long_window,
            momentum_window,
            combined_mode,
        )
        signal_col = "combined_signal"

    frame = frame.dropna(subset=["close"])
    if frame.empty:
        raise ValueError("Not enough data to evaluate paper trading signal.")

    latest = frame.iloc[-1]
    prev = frame.iloc[-2] if len(frame) > 1 else latest
    ma_signal = (
        int(latest["ma_signal"])
        if "ma_signal" in frame.columns and pd.notna(latest.get("ma_signal"))
        else None
    )
    momentum_signal = (
        int(latest["momentum_signal"])
        if "momentum_signal" in frame.columns and pd.notna(latest.get("momentum_signal"))
        else None
    )

    today_signal = int(latest[signal_col])
    target_position = int(prev[signal_col]) if pd.notna(prev[signal_col]) else 0

    trade_date = latest["date"] if "date" in frame.columns else latest.name
    if hasattr(trade_date, "strftime"):
        trade_date_str = trade_date.strftime("%Y-%m-%d")
    else:
        trade_date_str = str(trade_date)

    reason = "Strategy signal is positive; paper account would hold." if target_position == 1 else "Strategy signal is flat; paper account would stay in cash."
    if strategy == "ma_crossover":
        reason = (
            "Short MA above long MA; next-day paper position is long."
            if target_position == 1
            else "Short MA not above long MA; next-day paper position is flat."
        )

    return {
        "date": trade_date_str,
        "signal": today_signal,
        "target_position": target_position,
        "close": float(latest["close"]),
        "ma_signal": ma_signal,
        "momentum_signal": momentum_signal,
        "confidence": _signal_confidence(today_signal, ma_signal, momentum_signal),
        "reason": reason,
    }


def build_paper_dashboard(
    *,
    ticker: str,
    strategy: str,
    start_date: str = "2022-01-01",
    end_date: str | None = None,
    short_window: int = 20,
    long_window: int = 60,
    momentum_window: int = 60,
    combined_mode: str = "conservative",
    transaction_cost: float = AGGRESSIVE_PROFILE.transaction_cost_rate,
    account_id: str = "default",
    notes: str | None = None,
) -> dict[str, Any]:
    price_df = load_price_data(ticker, start_date, end_date)
    backtest_df = _run_backtest_frame(
        price_df,
        strategy,
        short_window=short_window,
        long_window=long_window,
        momentum_window=momentum_window,
        combined_mode=combined_mode,
        transaction_cost=transaction_cost,
    )
    metrics = calculate_backtest_metrics(backtest_df)
    signal_ctx = _latest_signal_context(
        price_df,
        strategy,
        short_window=short_window,
        long_window=long_window,
        momentum_window=momentum_window,
        combined_mode=combined_mode,
    )

    account = get_paper_account(account_id)
    account.ticker = ticker
    account.strategy = strategy
    if notes is not None:
        account.notes = notes

    current_price = signal_ctx["close"]
    cost_drag_ratio = None
    total_return = metrics.get("total_return")
    cost_total = metrics.get("transaction_cost_total")
    if total_return and abs(total_return) > 1e-9 and cost_total is not None:
        cost_drag_ratio = abs(cost_total / total_return)

    recent_slice = backtest_df.tail(63)
    recent_returns = recent_slice["strategy_return"].dropna()
    recent_sharpe = None
    if len(recent_returns) > 5 and recent_returns.std() > 0:
        recent_sharpe = float(recent_returns.mean() / recent_returns.std() * (252**0.5))

    risk = calculate_overall_risk_level(
        RiskMonitorInput(
            current_drawdown=account.current_drawdown(current_price),
            last_trade_loss_pct=account.last_trade_loss_pct,
            consecutive_losses=account.consecutive_losses,
            volatility=metrics.get("volatility"),
            baseline_volatility=metrics.get("volatility"),
            sharpe_ratio=metrics.get("sharpe_ratio"),
            recent_sharpe=recent_sharpe,
            cost_drag_ratio=cost_drag_ratio,
            ma_signal=signal_ctx.get("ma_signal"),
            momentum_signal=signal_ctx.get("momentum_signal"),
        )
    )

    account.last_risk_level = risk.risk_level
    account.last_risk_label = risk.risk_label

    cooldown = is_in_cooldown(account)
    paper_action = _derive_paper_action(
        signal_ctx["target_position"],
        account.position,
        risk.risk_level,
        cooldown,
    )

    return {
        "ticker": ticker,
        "strategy": strategy,
        "data_source": "yahoo",
        "start_date": start_date,
        "end_date": end_date,
        "strategy_config": {
            "strategy": strategy,
            "short_window": short_window,
            "long_window": long_window,
            "momentum_window": momentum_window,
            "combined_mode": combined_mode,
            "transaction_cost": transaction_cost,
        },
        "today_signal": {
            "date": signal_ctx["date"],
            "symbol": ticker,
            "strategy": strategy,
            "signal": "BUY" if signal_ctx["signal"] == 1 else "SELL" if signal_ctx["signal"] == 0 else "WAIT",
            "confidence": signal_ctx["confidence"],
            "risk_level": risk.risk_level,
            "reason": signal_ctx["reason"],
            "paper_action": paper_action,
            "target_position": signal_ctx["target_position"],
        },
        "risk": risk.to_dict(),
        "account": account.to_dict(current_price),
        "research_metrics": metrics,
        "trade_journal": [trade.to_dict() for trade in account.trades[-20:]],
        "disclaimer": "Paper trading simulation only. Not financial advice. No live orders.",
    }


def execute_paper_action(
    *,
    ticker: str,
    strategy: str,
    start_date: str = "2022-01-01",
    end_date: str | None = None,
    short_window: int = 20,
    long_window: int = 60,
    momentum_window: int = 60,
    combined_mode: str = "conservative",
    transaction_cost: float = AGGRESSIVE_PROFILE.transaction_cost_rate,
    account_id: str = "default",
    notes: str | None = None,
) -> dict[str, Any]:
    dashboard = build_paper_dashboard(
        ticker=ticker,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        short_window=short_window,
        long_window=long_window,
        momentum_window=momentum_window,
        combined_mode=combined_mode,
        transaction_cost=transaction_cost,
        account_id=account_id,
        notes=notes,
    )

    account = get_paper_account(account_id)
    signal = dashboard["today_signal"]
    risk = dashboard["risk"]
    current_price = dashboard["account"]["current_price"]
    paper_action = signal["paper_action"]
    trade_date = signal["date"]

    execution_message = "No paper trade executed."
    if paper_action == "BUY" and account.position == 0 and current_price:
        deploy_cash = account.cash * AGGRESSIVE_PROFILE.default_position_size
        cost = deploy_cash * transaction_cost
        shares = (deploy_cash - cost) / current_price
        account.cash -= deploy_cash
        account.shares = shares
        account.entry_price = current_price
        account.position = 1
        account.trades.append(
            PaperTradeRecord(
                trade_date=trade_date,
                symbol=ticker,
                action="BUY",
                price=current_price,
                shares=shares,
                cash_after=account.cash,
                reason=signal["reason"],
                risk_level=risk["risk_level"],
            )
        )
        execution_message = f"Paper BUY executed at {current_price:.2f}."
    elif paper_action == "SELL" and account.position > 0 and current_price:
        proceeds = account.shares * current_price
        cost = proceeds * transaction_cost
        net = proceeds - cost
        pnl = net - (account.entry_price or current_price) * account.shares
        account.cash += net
        trade_return = pnl / max((account.entry_price or current_price) * account.shares, 1e-9)
        account.realized_pnl += pnl
        account.last_trade_loss_pct = trade_return if trade_return < 0 else None
        if trade_return < 0:
            account.consecutive_losses += 1
        else:
            account.consecutive_losses = 0
        account.trades.append(
            PaperTradeRecord(
                trade_date=trade_date,
                symbol=ticker,
                action="SELL",
                price=current_price,
                shares=account.shares,
                cash_after=account.cash,
                reason=signal["reason"],
                risk_level=risk["risk_level"],
            )
        )
        account.shares = 0.0
        account.entry_price = None
        account.position = 0
        execution_message = f"Paper SELL executed at {current_price:.2f}."
        if risk["risk_level"] >= 5:
            cooldown_end = date.today() + timedelta(days=AGGRESSIVE_PROFILE.cooldown_days_after_red)
            account.cooldown_until = cooldown_end.isoformat()

    equity = account.portfolio_value(current_price)
    account.peak_equity = max(account.peak_equity, equity)

    dashboard["account"] = account.to_dict(current_price)
    dashboard["trade_journal"] = [trade.to_dict() for trade in account.trades[-20:]]
    dashboard["execution_message"] = execution_message
    return dashboard


def reset_account(account_id: str = "default") -> dict[str, Any]:
    account = reset_paper_account(account_id)
    return account.to_dict()
