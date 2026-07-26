"""ExecuteResearch use case for the canonical MA Crossover reference."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from app.research_execution.calculations import (
    metrics_to_dict,
    run_ma_crossover_research,
    series_to_records,
)
from app.research_execution.benchmark import build_trend_benchmark_comparison
from app.research_execution.market_data_port import (
    MarketDataPort,
    MarketDataError,
    MarketDataValidationError,
    UnsupportedSymbolError,
    clip_to_completed_daily_bars,
    utc_now_iso,
)
from app.research_reproducibility.manifest import build_reproducibility_manifest

RESEARCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

SAME_ASSET_BENCHMARK_MESSAGE = (
    "PR-008B supports only same-asset buy-and-hold benchmarking. "
    "Independent benchmark series are deferred."
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
        research_id = str(request.get("research_id") or "ma-crossover-spy").strip()
        if not RESEARCH_ID_PATTERN.fullmatch(research_id):
            raise ResearchExecutionError(
                "research_id must contain 1-128 letters, numbers, dots, "
                "underscores, or hyphens.",
                status_code=400,
            )

        symbol = str(request.get("symbol") or "SPY").upper().strip()
        benchmark = str(request.get("benchmark") or symbol).upper().strip()
        if not symbol:
            raise ResearchExecutionError("symbol must not be empty.", status_code=400)
        if benchmark != symbol:
            raise ResearchExecutionError(
                SAME_ASSET_BENCHMARK_MESSAGE,
                status_code=400,
            )
        start_date = str(request.get("start_date") or "2018-01-01")
        end_date = request.get("end_date")
        end_date = str(end_date) if end_date else None

        try:
            short_window = int(request.get("short_window", 20))
            long_window = int(request.get("long_window", 60))
            transaction_cost = float(request.get("transaction_cost", 0.001))
            risk_free_rate = float(request.get("risk_free_rate", 0.0))
            min_excess_return = float(request.get("min_excess_return", 0.0))
            min_sharpe_difference = float(
                request.get("min_sharpe_difference", 0.0)
            )
            min_drawdown_improvement = float(
                request.get("min_drawdown_improvement", 0.05)
            )
            min_observations = int(request.get("min_observations", 252))
            min_cost_adjusted_return = float(
                request.get("min_cost_adjusted_return", 0.0)
            )
            min_robust_parameter_ratio = float(
                request.get("min_robust_parameter_ratio", 0.5)
            )
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
        if min_drawdown_improvement < 0 or min_observations < 1:
            raise ResearchExecutionError(
                "min_drawdown_improvement must be >= 0 and min_observations >= 1.",
                status_code=400,
            )
        if not 0 <= min_robust_parameter_ratio <= 1:
            raise ResearchExecutionError(
                "min_robust_parameter_ratio must be between 0 and 1.",
                status_code=400,
            )
        if end_date and start_date >= end_date:
            raise ResearchExecutionError(
                "start_date must be before end_date.", status_code=400
            )

        try:
            market = self.market_data.get_daily_ohlcv(symbol, start_date, end_date)
            market = clip_to_completed_daily_bars(market, end_date=end_date)
        except UnsupportedSymbolError as exc:
            raise ResearchExecutionError(str(exc), status_code=400) from exc
        except MarketDataValidationError as exc:
            raise ResearchExecutionError(str(exc), status_code=502) from exc
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
        strategy_metrics = metrics_to_dict(backtest.strategy_metrics)
        benchmark_metrics = metrics_to_dict(backtest.benchmark_metrics)
        generated_at = utc_now_iso()
        benchmark_comparison = build_trend_benchmark_comparison(
            strategy_metrics,
            benchmark_metrics,
            min_excess_return=min_excess_return,
            min_sharpe_difference=min_sharpe_difference,
            min_drawdown_improvement=min_drawdown_improvement,
            min_observations=min_observations,
            min_cost_adjusted_return=min_cost_adjusted_return,
            min_robust_parameter_ratio=min_robust_parameter_ratio,
            evidence_timestamp=generated_at,
        )
        strategy = {
            "type": "ma_crossover",
            "symbol": symbol,
            "benchmark": symbol,
            "benchmark_type": "same_asset_buy_and_hold",
            "benchmark_label": f"{symbol} Buy & Hold",
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
        }
        provenance = asdict(market.provenance)
        reproducibility_manifest = build_reproducibility_manifest(
            data_source=provenance.get("provider") or provenance.get("source"),
            symbol=provenance.get("canonical_symbol") or provenance.get("symbol") or symbol,
            universe=None,
            requested_start_date=provenance.get("requested_start") or start_date,
            requested_end_date=provenance.get("requested_end")
            if provenance.get("requested_end") is not None
            else end_date,
            actual_start_date=provenance.get("actual_start"),
            actual_end_date=provenance.get("actual_end"),
            retrieval_timestamp=provenance.get("retrieved_at"),
            row_count=provenance.get("row_count") or len(market.frame),
            adjustment_mode=provenance.get("adjustment"),
            protocol={
                "research_id": research_id,
                "strategy_type": "ma_crossover",
                "symbol": symbol,
                "benchmark": symbol,
                "short_window": short_window,
                "long_window": long_window,
                "transaction_cost": transaction_cost,
                "risk_free_rate": risk_free_rate,
                "position_lag_days": 1,
                "annualization_trading_days": 252,
                "price_field": "adjusted_close",
            },
            frame=market.frame,
            created_at=generated_at,
        )
        return {
            "research_id": research_id,
            "strategy": strategy,
            "provenance": provenance,
            "reproducibility_manifest": reproducibility_manifest,
            "metrics": strategy_metrics,
            "benchmark_metrics": benchmark_metrics,
            "benchmark_comparison": benchmark_comparison,
            "series": series,
            "warnings": warnings,
            "generated_at": generated_at,
            "supported_evidence": {
                "historical_backtest": "completed",
                "benchmark_comparison": (
                    "historical_comparison_completed_validation_pending"
                ),
                "out_of_sample": "not_started",
                "parameter_sensitivity": "not_started",
                "transaction_cost_review": "not_started",
                "data_quality_review": "awaiting_engine",
                "evaluation": "unavailable",
            },
        }
