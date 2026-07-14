"""RunValidation use case for the canonical MA-crossover research artifact."""

from __future__ import annotations

import math
from dataclasses import asdict
from datetime import datetime
from statistics import median
from typing import Any

import pandas as pd

from app.research_execution.calculations import (
    BacktestResult,
    metrics_to_dict,
    run_ma_crossover_research,
    summarize_return_segment,
)
from app.research_execution.market_data_port import (
    MarketDataError,
    MarketDataPort,
    clip_to_completed_daily_bars,
    utc_now_iso,
)
from app.research_execution.service import SAME_ASSET_BENCHMARK_MESSAGE

CANONICAL_RESEARCH_ID = "ma-crossover-spy"
PARAMETER_SHORT_WINDOWS = (10, 20, 30)
PARAMETER_LONG_WINDOWS = (50, 60, 100)
TRANSACTION_COST_GRID = (0.0, 0.001, 0.002, 0.005)
STAGE_ORDER = (
    "historical_backtest",
    "benchmark_comparison",
    "out_of_sample",
    "parameter_sensitivity",
    "transaction_cost_sensitivity",
    "data_quality",
)


class ResearchValidationError(Exception):
    """Application failure mapped by the HTTP adapter."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _finite_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ResearchValidationError(f"{name} must be a number.") from exc
    if not math.isfinite(number):
        raise ResearchValidationError(f"{name} must be finite.")
    return number


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ResearchValidationError(f"{name} must be an integer.")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ResearchValidationError(f"{name} must be an integer.") from exc
    if float(value) != number:
        raise ResearchValidationError(f"{name} must be an integer.")
    return number


def _date(value: Any, name: str) -> str:
    text = str(value or "").strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ResearchValidationError(f"{name} must use YYYY-MM-DD.") from exc
    return text


def _difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    value = left - right
    return float(value) if math.isfinite(value) else None


def _deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _stage(
    *,
    name: str,
    label: str,
    status: str,
    summary: str,
    evidence: dict[str, Any],
    rules: list[str],
    warnings: list[str],
    blockers: list[str],
    generated_at: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "stage": name,
        "label": label,
        "status": status,
        "summary": summary,
        "evidence": evidence,
        "rules": rules,
        "warnings": _deduplicate(warnings),
        "blockers": _deduplicate(blockers),
        "generated_at": generated_at,
        "provenance": provenance,
    }


def _approximate_missing_weekday_intervals(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Report only multi-weekday gaps to avoid treating ordinary market holidays as errors.

    This is deliberately approximate because this slice has no exchange calendar.
    """
    dates = pd.to_datetime(frame["date"]).sort_values().reset_index(drop=True)
    intervals: list[dict[str, Any]] = []
    for previous, current in zip(dates.iloc[:-1], dates.iloc[1:]):
        missing = pd.bdate_range(previous, current)[1:-1]
        if len(missing) >= 3:
            intervals.append(
                {
                    "after": previous.date().isoformat(),
                    "before": current.date().isoformat(),
                    "approximate_missing_weekdays": int(len(missing)),
                }
            )
    return intervals


class ResearchValidationService:
    """Coordinate one market-data read and deterministic validation stages."""

    def __init__(self, market_data: MarketDataPort) -> None:
        self.market_data = market_data

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        parameters = self._validate_request(request)
        try:
            market = self.market_data.get_daily_ohlcv(
                parameters["symbol"],
                parameters["start_date"],
                parameters["end_date"],
            )
            market = clip_to_completed_daily_bars(
                market, end_date=parameters["end_date"]
            )
        except MarketDataError as exc:
            raise ResearchValidationError(str(exc), status_code=502) from exc

        try:
            baseline = run_ma_crossover_research(
                market.frame,
                short_window=parameters["short_window"],
                long_window=parameters["long_window"],
                transaction_cost=parameters["transaction_cost"],
                risk_free_rate=parameters["risk_free_rate"],
            )
        except ValueError as exc:
            raise ResearchValidationError(str(exc), status_code=400) from exc

        generated_at = utc_now_iso()
        provenance = asdict(market.provenance)
        oos, oos_stage = self._build_oos(
            market.frame,
            baseline,
            parameters,
            generated_at,
            provenance,
        )
        sensitivity, sensitivity_stage = self._build_parameter_sensitivity(
            market.frame,
            parameters,
            generated_at,
            provenance,
        )
        costs, cost_stage = self._build_cost_sensitivity(
            market.frame,
            baseline,
            parameters,
            generated_at,
            provenance,
        )
        quality, quality_stage = self._build_data_quality(
            market.frame,
            provenance,
            list(market.warnings),
            generated_at,
        )

        baseline_metrics = metrics_to_dict(baseline.strategy_metrics)
        benchmark_metrics = metrics_to_dict(baseline.benchmark_metrics)
        historical_stage = _stage(
            name="historical_backtest",
            label="Historical backtest",
            status="completed",
            summary="Full-history deterministic MA-crossover evidence was calculated.",
            evidence={
                "type": "deterministic_backtest_metrics",
                "metrics": baseline_metrics,
            },
            rules=[
                "Use adjusted close when available.",
                "Shift the MA signal by one observation to prevent look-ahead.",
                "Apply cost as absolute position change times transaction_cost.",
            ],
            warnings=list(baseline.warnings),
            blockers=[],
            generated_at=generated_at,
            provenance=provenance,
        )
        benchmark_stage = _stage(
            name="benchmark_comparison",
            label="Benchmark comparison",
            status="completed",
            summary="The strategy was compared with same-asset buy-and-hold.",
            evidence={
                "type": "same_asset_buy_and_hold_comparison",
                "symbol": parameters["symbol"],
                "strategy_metrics": baseline_metrics,
                "benchmark_metrics": benchmark_metrics,
                "excess_total_return": _difference(
                    baseline.strategy_metrics.total_return,
                    baseline.benchmark_metrics.total_return,
                ),
                "excess_sharpe_ratio": _difference(
                    baseline.strategy_metrics.sharpe_ratio,
                    baseline.benchmark_metrics.sharpe_ratio,
                ),
            },
            rules=[
                "Compare against same-asset buy-and-hold over identical valid rows."
            ],
            warnings=[],
            blockers=[],
            generated_at=generated_at,
            provenance=provenance,
        )
        stages = [
            historical_stage,
            benchmark_stage,
            oos_stage,
            sensitivity_stage,
            cost_stage,
            quality_stage,
        ]
        assert tuple(stage["stage"] for stage in stages) == STAGE_ORDER
        statuses = [stage["status"] for stage in stages]
        validation_status = (
            "failed"
            if "failed" in statuses
            else "incomplete"
            if "incomplete" in statuses
            else "completed"
        )
        evidence_complete = validation_status == "completed"
        warnings = _deduplicate(
            list(market.warnings)
            + list(baseline.warnings)
            + [warning for stage in stages for warning in stage["warnings"]]
        )
        return {
            "research_id": parameters["research_id"],
            "strategy": {
                "type": "ma_crossover",
                "symbol": parameters["symbol"],
                "benchmark": parameters["benchmark"],
                "benchmark_type": "same_asset_buy_and_hold",
                "benchmark_label": f"{parameters['symbol']} Buy & Hold",
                "short_window": parameters["short_window"],
                "long_window": parameters["long_window"],
                "transaction_cost": parameters["transaction_cost"],
                "risk_free_rate": parameters["risk_free_rate"],
                "in_sample_ratio": parameters["in_sample_ratio"],
                "position_lag_days": 1,
                "annualization_trading_days": 252,
                "price_field": "adjusted_close",
                "fixed_parameters": True,
            },
            "provenance": provenance,
            "validation_status": validation_status,
            "evidence_complete": evidence_complete,
            "stages": stages,
            "oos": oos,
            "parameter_sensitivity": sensitivity,
            "transaction_cost_sensitivity": costs,
            "data_quality": quality,
            "warnings": warnings,
            "generated_at": generated_at,
        }

    def _validate_request(self, request: dict[str, Any]) -> dict[str, Any]:
        research_id = str(
            request.get("research_id", CANONICAL_RESEARCH_ID) or ""
        ).strip()
        if research_id != CANONICAL_RESEARCH_ID:
            raise ResearchValidationError(
                f"Unsupported research_id '{research_id}'. "
                f"Supported: ['{CANONICAL_RESEARCH_ID}']."
            )

        symbol = str(request.get("symbol", "SPY") or "").upper().strip()
        benchmark = str(request.get("benchmark", "SPY") or "").upper().strip()
        if not symbol:
            raise ResearchValidationError("symbol must not be empty.")
        if benchmark != symbol:
            raise ResearchValidationError(SAME_ASSET_BENCHMARK_MESSAGE)

        start_date = _date(request.get("start_date", "2018-01-01"), "start_date")
        end_raw = request.get("end_date")
        end_date = _date(end_raw, "end_date") if end_raw else None
        if end_date and start_date >= end_date:
            raise ResearchValidationError("start_date must be before end_date.")

        short_window = _integer(request.get("short_window", 20), "short_window")
        long_window = _integer(request.get("long_window", 60), "long_window")
        if short_window <= 0 or long_window <= 0:
            raise ResearchValidationError(
                "short_window and long_window must be > 0."
            )
        if short_window >= long_window:
            raise ResearchValidationError("short_window must be < long_window.")

        transaction_cost = _finite_number(
            request.get("transaction_cost", 0.001), "transaction_cost"
        )
        if transaction_cost < 0:
            raise ResearchValidationError("transaction_cost must be >= 0.")
        risk_free_rate = _finite_number(
            request.get("risk_free_rate", 0.0), "risk_free_rate"
        )
        in_sample_ratio = _finite_number(
            request.get("in_sample_ratio", 0.7), "in_sample_ratio"
        )
        if not 0.5 <= in_sample_ratio <= 0.9:
            raise ResearchValidationError(
                "in_sample_ratio must be between 0.5 and 0.9 inclusive."
            )
        return {
            "research_id": research_id,
            "symbol": symbol,
            "benchmark": benchmark,
            "start_date": start_date,
            "end_date": end_date,
            "short_window": short_window,
            "long_window": long_window,
            "transaction_cost": transaction_cost,
            "risk_free_rate": risk_free_rate,
            "in_sample_ratio": in_sample_ratio,
        }

    def _build_oos(
        self,
        prices: pd.DataFrame,
        baseline: BacktestResult,
        parameters: dict[str, Any],
        generated_at: str,
        provenance: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        split_index = math.floor(len(prices) * parameters["in_sample_ratio"])
        split_date = pd.Timestamp(prices["date"].iloc[split_index])
        split_date_text = split_date.date().isoformat()
        raw_oos_count = len(prices) - split_index
        minimum_oos = max(60, parameters["long_window"])
        full_dates = pd.to_datetime(baseline.frame["date"])
        in_sample_frame = baseline.frame.loc[full_dates < split_date]
        out_of_sample_frame = baseline.frame.loc[full_dates >= split_date]

        calculation_failures: list[str] = []
        in_sample = None
        if not in_sample_frame.empty:
            try:
                in_sample = summarize_return_segment(
                    in_sample_frame, risk_free_rate=parameters["risk_free_rate"]
                )
            except (ValueError, ArithmeticError) as exc:
                calculation_failures.append(
                    f"In-sample metric calculation failed: {exc}"
                )
        out_of_sample = None
        if not out_of_sample_frame.empty:
            try:
                out_of_sample = summarize_return_segment(
                    out_of_sample_frame, risk_free_rate=parameters["risk_free_rate"]
                )
            except (ValueError, ArithmeticError) as exc:
                calculation_failures.append(
                    f"Out-of-sample metric calculation failed: {exc}"
                )
        blockers: list[str] = []
        if len(out_of_sample_frame) < minimum_oos:
            blockers.append(
                f"Insufficient OOS history: need at least {minimum_oos} valid "
                f"return rows; got {len(out_of_sample_frame)}."
            )
        if out_of_sample_frame.empty:
            blockers.append("No valid OOS return rows after the split.")
        if in_sample_frame.empty:
            blockers.append("No valid in-sample return rows after MA warm-up.")
        blockers.extend(calculation_failures)
        status = (
            "failed"
            if calculation_failures
            else "completed"
            if not blockers
            else "incomplete"
        )
        boundary = (
            "The strategy is run once on full history, then valid return rows are "
            "sliced at split_date. The first OOS row therefore preserves its full-run "
            "position, turnover, and transaction cost against the prior in-sample row."
        )
        fixed_parameters = {
            "short_window": parameters["short_window"],
            "long_window": parameters["long_window"],
            "transaction_cost": parameters["transaction_cost"],
            "risk_free_rate": parameters["risk_free_rate"],
        }
        payload = {
            "status": status,
            "split_date": split_date_text,
            "in_sample_ratio": parameters["in_sample_ratio"],
            "minimum_oos_observations": minimum_oos,
            "in_sample_metrics": (
                metrics_to_dict(in_sample.strategy_metrics) if in_sample else None
            ),
            "out_of_sample_metrics": (
                metrics_to_dict(out_of_sample.strategy_metrics)
                if out_of_sample
                else None
            ),
            "oos_benchmark_metrics": (
                metrics_to_dict(out_of_sample.benchmark_metrics)
                if out_of_sample
                else None
            ),
            "in_sample_observation_count": len(in_sample_frame),
            "out_of_sample_observation_count": len(out_of_sample_frame),
            "warnings": blockers,
            "boundary_convention": boundary,
            "split_observation_index": split_index,
            "raw_observation_count": len(prices),
            "in_sample_raw_observation_count": split_index,
            "out_of_sample_raw_observation_count": raw_oos_count,
            "fixed_parameters": fixed_parameters,
        }
        stage = _stage(
            name="out_of_sample",
            label="Out-of-sample validation",
            status=status,
            summary=(
                "Chronological OOS evidence completed with fixed parameters."
                if status == "completed"
                else "Chronological OOS evidence calculation failed."
                if status == "failed"
                else "Chronological OOS evidence is incomplete."
            ),
            evidence={
                "type": "chronological_split",
                "split_observation_index": split_index,
                "split_date": split_date_text,
                "in_sample_ratio": parameters["in_sample_ratio"],
                "in_sample_return_rows": len(in_sample_frame),
                "out_of_sample_return_rows": len(out_of_sample_frame),
                "minimum_oos_observations": minimum_oos,
                "fixed_parameters": fixed_parameters,
                "boundary_convention": boundary,
                "in_sample_metrics": payload["in_sample_metrics"],
                "out_of_sample_metrics": payload["out_of_sample_metrics"],
                "oos_benchmark_metrics": payload["oos_benchmark_metrics"],
            },
            rules=[
                "Split chronologically at floor(observation_count × in_sample_ratio).",
                "Do not shuffle observations or tune parameters on OOS data.",
                "Require max(60, long_window) valid OOS return rows.",
                "Rebase cumulative returns independently within each segment.",
            ],
            warnings=[],
            blockers=blockers,
            generated_at=generated_at,
            provenance=provenance,
        )
        return payload, stage

    def _build_parameter_sensitivity(
        self,
        prices: pd.DataFrame,
        parameters: dict[str, Any],
        generated_at: str,
        provenance: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for short_window in PARAMETER_SHORT_WINDOWS:
            for long_window in PARAMETER_LONG_WINDOWS:
                if short_window >= long_window:
                    continue
                is_canonical = short_window == 20 and long_window == 60
                try:
                    result = run_ma_crossover_research(
                        prices,
                        short_window=short_window,
                        long_window=long_window,
                        transaction_cost=parameters["transaction_cost"],
                        risk_free_rate=parameters["risk_free_rate"],
                    )
                    metrics = metrics_to_dict(result.strategy_metrics)
                    results.append(
                        {
                            "short_window": short_window,
                            "long_window": long_window,
                            "total_return": metrics["total_return"],
                            "cagr": metrics["cagr"],
                            "sharpe_ratio": metrics["sharpe_ratio"],
                            "maximum_drawdown": metrics["maximum_drawdown"],
                            "annualized_volatility": metrics[
                                "annualized_volatility"
                            ],
                            "trade_count": metrics["trade_count"],
                            "total_transaction_costs": metrics[
                                "total_transaction_costs"
                            ],
                            "status": "completed",
                            "warnings": list(result.warnings),
                            "is_canonical": is_canonical,
                        }
                    )
                except ValueError as exc:
                    results.append(
                        {
                            "short_window": short_window,
                            "long_window": long_window,
                            "total_return": None,
                            "cagr": None,
                            "sharpe_ratio": None,
                            "maximum_drawdown": None,
                            "annualized_volatility": None,
                            "trade_count": None,
                            "total_transaction_costs": None,
                            "status": "incomplete",
                            "warnings": [str(exc)],
                            "is_canonical": is_canonical,
                        }
                    )
        completed = [item for item in results if item["status"] == "completed"]
        incomplete = [item for item in results if item["status"] != "completed"]
        canonical_result = next(
            (item for item in results if item["is_canonical"]), None
        )
        status = (
            "failed"
            if not completed
            else "completed"
            if not incomplete
            else "incomplete"
        )
        returns = [
            item["total_return"]
            for item in completed
            if item["total_return"] is not None
        ]
        sharpes = [
            item["sharpe_ratio"]
            for item in completed
            if item["sharpe_ratio"] is not None
        ]
        drawdowns = [
            item["maximum_drawdown"]
            for item in completed
            if item["maximum_drawdown"] is not None
        ]
        canonical_sharpe = (
            canonical_result["sharpe_ratio"] if canonical_result else None
        )
        canonical_percentile = (
            sum(value <= canonical_sharpe for value in sharpes) / len(sharpes)
            if canonical_sharpe is not None and sharpes
            else None
        )
        result_warnings = _deduplicate(
            [warning for item in results for warning in item["warnings"]]
        )
        payload = {
            "status": status,
            "results": results,
            "valid_combination_count": len(completed),
            "profitable_combination_count": sum(
                value > 0 for value in returns
            ),
            "positive_sharpe_count": sum(value > 0 for value in sharpes),
            "median_sharpe": median(sharpes) if sharpes else None,
            "sharpe_range": [
                min(sharpes) if sharpes else None,
                max(sharpes) if sharpes else None,
            ],
            "median_max_drawdown": median(drawdowns) if drawdowns else None,
            "canonical_percentile_by_sharpe": canonical_percentile,
            "warnings": result_warnings,
        }
        stage = _stage(
            name="parameter_sensitivity",
            label="Parameter sensitivity",
            status=status,
            summary=(
                f"{len(completed)} of {len(results)} deterministic parameter "
                "combinations produced metrics; no parameter was selected."
            ),
            evidence={
                "type": "deterministic_parameter_grid",
                "short_windows": list(PARAMETER_SHORT_WINDOWS),
                "long_windows": list(PARAMETER_LONG_WINDOWS),
                "ordering": "short_window ascending, then long_window ascending",
                "maximum_results": 9,
                "fixed_transaction_cost": parameters["transaction_cost"],
                "fixed_risk_free_rate": parameters["risk_free_rate"],
                **payload,
            },
            rules=[
                "Evaluate the fixed 3×3 grid in deterministic nested-loop order.",
                "Include only combinations where short_window < long_window.",
                "Reuse the normalized price dataset without provider reads.",
                "Report results without selecting a best parameter set.",
            ],
            warnings=result_warnings,
            blockers=(
                ["No parameter-grid combination produced valid metrics."]
                if status == "failed"
                else []
            ),
            generated_at=generated_at,
            provenance=provenance,
        )
        return payload, stage

    def _build_cost_sensitivity(
        self,
        prices: pd.DataFrame,
        baseline: BacktestResult,
        parameters: dict[str, Any],
        generated_at: str,
        provenance: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        raw_results: dict[float, BacktestResult] = {}
        calculation_failures: dict[float, str] = {}
        for transaction_cost in TRANSACTION_COST_GRID:
            try:
                raw_results[transaction_cost] = run_ma_crossover_research(
                    prices,
                    short_window=parameters["short_window"],
                    long_window=parameters["long_window"],
                    transaction_cost=transaction_cost,
                    risk_free_rate=parameters["risk_free_rate"],
                )
            except (ValueError, ArithmeticError) as exc:
                calculation_failures[transaction_cost] = (
                    f"Cost sensitivity calculation failed at "
                    f"transaction_cost={transaction_cost}: {exc}"
                )

        zero_result = raw_results.get(0.0)
        zero = zero_result.strategy_metrics if zero_result else None
        results: list[dict[str, Any]] = []
        for transaction_cost in TRANSACTION_COST_GRID:
            result = raw_results.get(transaction_cost)
            if result is None:
                results.append(
                    {
                        "transaction_cost": transaction_cost,
                        "total_return": None,
                        "cagr": None,
                        "sharpe_ratio": None,
                        "maximum_drawdown": None,
                        "trade_count": None,
                        "total_transaction_costs": None,
                        "return_degradation_from_zero": None,
                        "sharpe_degradation_from_zero": None,
                        "warnings": [calculation_failures[transaction_cost]],
                        "mathematically_valid": False,
                    }
                )
                continue

            metrics = metrics_to_dict(result.strategy_metrics)
            return_degradation = (
                _difference(zero.total_return, result.strategy_metrics.total_return)
                if zero
                else None
            )
            sharpe_degradation = (
                _difference(zero.sharpe_ratio, result.strategy_metrics.sharpe_ratio)
                if zero
                else None
            )
            mathematically_valid = (
                metrics["total_return"] is not None
                and return_degradation is not None
                and (
                    zero is not None
                    and zero.sharpe_ratio is None
                    or (
                        metrics["sharpe_ratio"] is not None
                        and sharpe_degradation is not None
                    )
                )
            )
            row_warnings = list(result.warnings)
            if zero is None:
                row_warnings.append(
                    "Zero-cost result unavailable; degradation metrics are undefined."
                )
            results.append(
                {
                    "transaction_cost": transaction_cost,
                    "total_return": metrics["total_return"],
                    "cagr": metrics["cagr"],
                    "sharpe_ratio": metrics["sharpe_ratio"],
                    "maximum_drawdown": metrics["maximum_drawdown"],
                    "trade_count": metrics["trade_count"],
                    "total_transaction_costs": metrics[
                        "total_transaction_costs"
                    ],
                    "return_degradation_from_zero": return_degradation,
                    "sharpe_degradation_from_zero": sharpe_degradation,
                    "warnings": _deduplicate(row_warnings),
                    "mathematically_valid": mathematically_valid,
                }
            )
        canonical_result = next(
            (
                item
                for item in results
                if math.isclose(
                    item["transaction_cost"],
                    parameters["transaction_cost"],
                    rel_tol=0,
                    abs_tol=1e-12,
                )
            ),
            None,
        )
        canonical_in_grid = canonical_result is not None
        if canonical_result is None:
            metrics = metrics_to_dict(baseline.strategy_metrics)
            canonical_return_degradation = (
                _difference(zero.total_return, baseline.strategy_metrics.total_return)
                if zero
                else None
            )
            canonical_sharpe_degradation = (
                _difference(zero.sharpe_ratio, baseline.strategy_metrics.sharpe_ratio)
                if zero
                else None
            )
            canonical_warnings = list(baseline.warnings)
            if zero is None:
                canonical_warnings.append(
                    "Zero-cost result unavailable; degradation metrics are undefined."
                )
            canonical_result = {
                "transaction_cost": parameters["transaction_cost"],
                "total_return": metrics["total_return"],
                "cagr": metrics["cagr"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "maximum_drawdown": metrics["maximum_drawdown"],
                "trade_count": metrics["trade_count"],
                "total_transaction_costs": metrics["total_transaction_costs"],
                "return_degradation_from_zero": canonical_return_degradation,
                "sharpe_degradation_from_zero": canonical_sharpe_degradation,
                "warnings": _deduplicate(canonical_warnings),
                "mathematically_valid": (
                    metrics["total_return"] is not None
                    and canonical_return_degradation is not None
                    and (
                        zero is not None
                        and zero.sharpe_ratio is None
                        or (
                            metrics["sharpe_ratio"] is not None
                            and canonical_sharpe_degradation is not None
                        )
                    )
                ),
            }
        completed_count = len(raw_results)
        status = (
            "completed"
            if completed_count == len(TRANSACTION_COST_GRID)
            else "failed"
            if completed_count == 0
            else "incomplete"
        )
        mathematically_valid_count = sum(
            item["mathematically_valid"] for item in results
        )
        summary = {
            "tested_costs": list(TRANSACTION_COST_GRID),
            "completed_results": completed_count,
            "mathematically_valid_results": mathematically_valid_count,
            "canonical_transaction_cost": parameters["transaction_cost"],
            "canonical_in_grid": canonical_in_grid,
            "zero_cost_total_return": zero.total_return if zero else None,
            "zero_cost_sharpe_ratio": zero.sharpe_ratio if zero else None,
        }
        payload_warnings = _deduplicate(
            [warning for item in results for warning in item["warnings"]]
        )
        payload = {
            "status": status,
            "results": results,
            "canonical_cost": parameters["transaction_cost"],
            "canonical_cost_result": canonical_result,
            "warnings": payload_warnings,
        }
        stage = _stage(
            name="transaction_cost_sensitivity",
            label="Transaction-cost sensitivity",
            status=status,
            summary=(
                f"{completed_count} of {len(TRANSACTION_COST_GRID)} deterministic "
                "transaction-cost levels produced metrics."
            ),
            evidence={
                "type": "deterministic_transaction_cost_grid",
                "fixed_short_window": parameters["short_window"],
                "fixed_long_window": parameters["long_window"],
                "fixed_risk_free_rate": parameters["risk_free_rate"],
                "cost_grid": list(TRANSACTION_COST_GRID),
                **payload,
                "descriptive_summary": summary,
            },
            rules=[
                "Evaluate costs [0, 0.001, 0.002, 0.005] in ascending order.",
                "Keep MA windows and risk-free rate fixed.",
                "Measure degradation relative to the zero-cost run.",
                "Reuse the normalized price dataset without provider reads.",
            ],
            warnings=payload["warnings"],
            blockers=list(calculation_failures.values()),
            generated_at=generated_at,
            provenance=provenance,
        )
        return payload, stage

    def _build_data_quality(
        self,
        prices: pd.DataFrame,
        provenance: dict[str, Any],
        provider_warnings: list[str],
        generated_at: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        intervals = _approximate_missing_weekday_intervals(prices)
        checks: list[dict[str, Any]] = [
            {
                "name": "Normalized OHLCV contract",
                "severity": "fatal",
                "status": "passed",
                "summary": "Required normalized OHLCV fields passed validation.",
                "evidence": {"observation_count": len(prices)},
            },
            {
                "name": "Unique ascending dates",
                "severity": "fatal",
                "status": "passed",
                "summary": "Observation dates are unique and ascending.",
                "evidence": {
                    "actual_start": provenance["actual_start"],
                    "actual_end": provenance["actual_end"],
                },
            },
            {
                "name": "Positive price fields",
                "severity": "fatal",
                "status": "passed",
                "summary": "Normalized price fields are positive.",
                "evidence": {"price_fields": ["open", "high", "low", "close"]},
            },
            {
                "name": "Source provenance",
                "severity": "info",
                "status": "passed",
                "summary": "Provider, source, retrieval time, and requested bounds are recorded.",
                "evidence": provenance,
            },
        ]
        limitations: list[str] = []
        if provenance.get("cache_stale"):
            message = "The provider returned a labeled stale cache result."
            limitations.append(message)
            checks.append(
                {
                    "name": "Cache freshness",
                    "severity": "warning",
                    "status": "warning",
                    "summary": message,
                    "evidence": {
                        "cache_hit": provenance.get("cache_hit"),
                        "cache_stale": provenance.get("cache_stale"),
                    },
                }
            )
        else:
            checks.append(
                {
                    "name": "Cache freshness",
                    "severity": "info",
                    "status": "passed",
                    "summary": "No stale-cache condition is reported.",
                    "evidence": {
                        "cache_hit": provenance.get("cache_hit"),
                        "cache_stale": provenance.get("cache_stale"),
                    },
                }
            )
        zero_volume_count = int((prices["volume"] == 0).sum())
        if zero_volume_count:
            message = (
                f"{zero_volume_count} normalized volume observations are zero; "
                "source null volume may have been filled."
            )
            limitations.append(message)
            checks.append(
                {
                    "name": "Volume completeness",
                    "severity": "warning",
                    "status": "warning",
                    "summary": message,
                    "evidence": {"zero_volume_observation_count": zero_volume_count},
                }
            )
        else:
            checks.append(
                {
                    "name": "Volume completeness",
                    "severity": "info",
                    "status": "passed",
                    "summary": "No zero normalized volume observations were found.",
                    "evidence": {"zero_volume_observation_count": 0},
                }
            )
        requested_start = provenance.get("requested_start")
        actual_start = provenance.get("actual_start")
        coverage_gap = (
            len(pd.bdate_range(requested_start, actual_start)) - 1
            if requested_start and actual_start and actual_start > requested_start
            else 0
        )
        if coverage_gap >= 3:
            message = (
                f"Actual coverage begins {actual_start}, after requested start "
                f"{requested_start}."
            )
            limitations.append(message)
            checks.append(
                {
                    "name": "Requested range coverage",
                    "severity": "warning",
                    "status": "warning",
                    "summary": message,
                    "evidence": {
                        "requested_start": requested_start,
                        "actual_start": actual_start,
                    },
                }
            )
        else:
            checks.append(
                {
                    "name": "Requested range coverage",
                    "severity": "info",
                    "status": "passed",
                    "summary": "The actual series starts at the requested bound.",
                    "evidence": {
                        "requested_start": requested_start,
                        "actual_start": actual_start,
                    },
                }
            )
        if intervals:
            message = (
                "Approximate multi-weekday gaps detected. This is a conservative "
                "limitation check without a full exchange calendar."
            )
            limitations.append(message)
            checks.append(
                {
                    "name": "Approximate weekday continuity",
                    "severity": "warning",
                    "status": "warning",
                    "summary": message,
                    "evidence": {
                        "intervals": intervals,
                        "calendar_limitation": "No full exchange calendar is applied.",
                    },
                }
            )
        else:
            checks.append(
                {
                    "name": "Approximate weekday continuity",
                    "severity": "info",
                    "status": "passed",
                    "summary": (
                        "No multi-weekday gaps were detected by the conservative "
                        "weekday approximation."
                    ),
                    "evidence": {
                        "calendar_limitation": "No full exchange calendar is applied."
                    },
                }
            )
        for index, warning in enumerate(provider_warnings, start=1):
            limitations.append(warning)
            checks.append(
                {
                    "name": f"Provider warning {index}",
                    "severity": "warning",
                    "status": "warning",
                    "summary": warning,
                    "evidence": {
                        "provider": provenance.get("provider"),
                        "source": provenance.get("source"),
                    },
                }
            )
        fatal_failures = [
            check
            for check in checks
            if check["severity"] == "fatal" and check["status"] == "failed"
        ]
        warning_checks = [
            check for check in checks if check["severity"] == "warning"
        ]
        status = (
            "failed"
            if fatal_failures
            else "incomplete"
            if limitations
            else "completed"
        )
        payload = {
            "status": status,
            "fatal_issues": [check["summary"] for check in fatal_failures],
            "warnings": _deduplicate(limitations),
            "informational": {
                "provider": provenance.get("provider"),
                "source": provenance.get("source"),
                "symbol": provenance.get("symbol"),
                "requested_start": provenance.get("requested_start"),
                "requested_end": provenance.get("requested_end"),
                "actual_start": provenance.get("actual_start"),
                "actual_end": provenance.get("actual_end"),
                "observation_count": len(prices),
                "cache_hit": provenance.get("cache_hit"),
                "cache_stale": provenance.get("cache_stale"),
                "retrieved_at": provenance.get("retrieved_at"),
            },
            "checks": checks,
        }
        stage = _stage(
            name="data_quality",
            label="Data quality",
            status=status,
            summary=(
                f"Data-quality review found {len(fatal_failures)} fatal issues "
                f"and {len(payload['warnings'])} non-fatal limitations."
            ),
            evidence={
                "checks": checks,
                "informational": payload["informational"],
            },
            rules=[
                "Fatal checks determine failure.",
                "Warnings and documented limitations determine incomplete status.",
                "Provider warnings never become fatal failures.",
                "Weekday continuity is approximate without an exchange calendar.",
            ],
            warnings=payload["warnings"],
            blockers=[check["summary"] for check in fatal_failures],
            generated_at=generated_at,
            provenance=provenance,
        )
        return payload, stage
