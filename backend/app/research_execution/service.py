"""ExecuteResearch use case for the canonical MA Crossover reference."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.research_execution.calculations import (
    metrics_to_dict,
    run_ma_crossover_research,
    series_to_records,
)
from app.research_execution.market_data_port import (
    MarketDataPort,
    MarketDataError,
    utc_now_iso,
)

CANONICAL_RESEARCH_IDS = frozenset(
    {
        "ma-crossover-spy",
        "rs-ma-crossover-001",  # compatibility alias from PR-008A catalogs
    }
)


class ResearchExecutionError(Exception):
    """Application-level execution failure with HTTP-friendly code."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class ResearchExecutionService:
    """Coordinates MarketDataPort + deterministic MA calculations."""

    def __init__(self, market_data: MarketDataPort) -> None:
        self.market_data = market_data

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        research_id = str(request.get("research_id") or "").strip()
        if research_id and research_id not in CANONICAL_RESEARCH_IDS:
            raise ResearchExecutionError(
                f"Unsupported research_id '{research_id}'. "
                f"Supported: {sorted(CANONICAL_RESEARCH_IDS)}.",
                status_code=400,
            )
        research_id = research_id or "ma-crossover-spy"

        symbol = str(request.get("symbol") or "SPY").upper().strip()
        benchmark = str(request.get("benchmark") or "SPY").upper().strip()
        start_date = str(request.get("start_date") or "2018-01-01")
        end_date = request.get("end_date")
        end_date = str(end_date) if end_date else None

        try:
            short_window = int(request.get("short_window", 20))
            long_window = int(request.get("long_window", 60))
            transaction_cost = float(request.get("transaction_cost", 0.001))
            risk_free_rate = float(request.get("risk_free_rate", 0.0))
        except (TypeError, ValueError) as exc:
            raise ResearchExecutionError(
                f"Invalid numeric parameters: {exc}", status_code=400
            ) from exc

        if short_window <= 0 or long_window <= 0:
            raise ResearchExecutionError(
                "short_window and long_window must be > 0.", status_code=400
            )
        if short_window >= long_window:
            raise ResearchExecutionError(
                "short_window must be < long_window.", status_code=400
            )
        if transaction_cost < 0:
            raise ResearchExecutionError(
                "transaction_cost must be >= 0.", status_code=400
            )
        if end_date and start_date >= end_date:
            raise ResearchExecutionError(
                "start_date must be before end_date.", status_code=400
            )

        try:
            market = self.market_data.get_daily_ohlcv(symbol, start_date, end_date)
        except MarketDataError as exc:
            raise ResearchExecutionError(str(exc), status_code=502) from exc

        try:
            backtest = run_ma_crossover_research(
                market.frame,
                short_window=short_window,
                long_window=long_window,
                transaction_cost=transaction_cost,
                risk_free_rate=risk_free_rate,
            )
        except ValueError as exc:
            raise ResearchExecutionError(str(exc), status_code=400) from exc

        warnings = list(market.warnings) + list(backtest.warnings)
        if len(backtest.frame) > 2500:
            warnings.append(
                "Series downsampled for response size; calculations used the full series."
            )

        series = series_to_records(backtest.frame)
        return {
            "research_id": research_id,
            "strategy": {
                "type": "ma_crossover",
                "symbol": symbol,
                "benchmark": benchmark,
                "short_window": short_window,
                "long_window": long_window,
                "transaction_cost": transaction_cost,
                "transaction_cost_convention": (
                    "Cost = |Δposition| × transaction_cost per trading day "
                    "(for 0/1 positions: charged on each entry or exit)."
                ),
                "position_lag_days": 1,
                "risk_free_rate": risk_free_rate,
                "annualization_trading_days": 252,
                "price_field": "adjusted_close",
            },
            "provenance": asdict(market.provenance),
            "metrics": metrics_to_dict(backtest.strategy_metrics),
            "benchmark_metrics": metrics_to_dict(backtest.benchmark_metrics),
            "series": series,
            "warnings": warnings,
            "generated_at": utc_now_iso(),
            "supported_evidence": {
                "historical_backtest": "completed",
                "benchmark_comparison": "completed",
                "out_of_sample": "not_started",
                "parameter_sensitivity": "not_started",
                "transaction_cost_review": "not_started",
                "data_quality_review": "awaiting_engine",
                "evaluation": "unavailable",
            },
        }
