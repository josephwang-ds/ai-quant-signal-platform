"""Transparent deterministic benchmark comparison for trend-following research."""

from __future__ import annotations

from typing import Any


def _difference(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _check(
    check_id: str,
    name: str,
    observed: float | None,
    threshold: float,
    *,
    operator: str = ">=",
    severity: str = "core",
    evidence_source: str,
    metric_unit: str = "ratio",
    evidence_timestamp: str | None = None,
) -> dict[str, Any]:
    if observed is None:
        status = "unavailable"
        explanation = "The required metric was not calculated."
    else:
        passed = observed >= threshold if operator == ">=" else observed <= threshold
        status = "pass" if passed else "fail"
        explanation = (
            f"Observed {observed:.6f} {operator} configured threshold "
            f"{threshold:.6f}: {status}."
        )
    return {
        "check_id": check_id,
        "name": name,
        "status": status,
        "observed_value": observed,
        "configured_threshold": threshold,
        "threshold": threshold,
        "metric_unit": metric_unit,
        "operator": operator,
        "explanation": explanation,
        "evidence_source": evidence_source,
        "severity": severity,
        "evidence_timestamp": evidence_timestamp,
    }


def build_trend_benchmark_comparison(
    strategy: dict[str, Any],
    benchmark: dict[str, Any],
    *,
    min_excess_return: float,
    min_sharpe_difference: float,
    min_drawdown_improvement: float,
    min_observations: int,
    min_cost_adjusted_return: float = 0.0,
    min_robust_parameter_ratio: float = 0.5,
    oos_sharpe_difference: float | None = None,
    robust_parameter_ratio: float | None = None,
    fatal_data_issue_count: int | None = None,
    evidence_timestamp: str | None = None,
) -> dict[str, Any]:
    """Compare aligned, backend-calculated strategy and buy-and-hold metrics."""
    comparable_period = (
        strategy.get("start_date") == benchmark.get("start_date")
        and strategy.get("end_date") == benchmark.get("end_date")
        and strategy.get("observation_count") == benchmark.get("observation_count")
    )
    excess_return = _difference(
        strategy.get("total_return"), benchmark.get("total_return")
    )
    excess_cagr = _difference(strategy.get("cagr"), benchmark.get("cagr"))
    sharpe_difference = _difference(
        strategy.get("sharpe_ratio"), benchmark.get("sharpe_ratio")
    )
    # Drawdowns are negative. -0.20 - (-0.30) = +0.10 improvement.
    drawdown_improvement = _difference(
        strategy.get("maximum_drawdown"), benchmark.get("maximum_drawdown")
    )
    volatility_difference = _difference(
        strategy.get("annualized_volatility"),
        benchmark.get("annualized_volatility"),
    )

    checks = [
        _check(
            "benchmark_return",
            "Return after costs versus Buy and Hold",
            excess_return,
            min_excess_return,
            evidence_source="metrics.total_return - benchmark_metrics.total_return",
            metric_unit="decimal_return",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "risk_adjusted",
            "Sharpe improvement versus Buy and Hold",
            sharpe_difference,
            min_sharpe_difference,
            evidence_source="metrics.sharpe_ratio - benchmark_metrics.sharpe_ratio",
            metric_unit="sharpe_ratio",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "drawdown",
            "Maximum drawdown improvement",
            drawdown_improvement,
            min_drawdown_improvement,
            severity="supporting",
            evidence_source=(
                "metrics.maximum_drawdown - benchmark_metrics.maximum_drawdown"
            ),
            metric_unit="decimal_return",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "cost_resilience",
            "Return after configured transaction costs",
            strategy.get("total_return"),
            min_cost_adjusted_return,
            evidence_source="metrics.total_return",
            metric_unit="decimal_return",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "out_of_sample_consistency",
            "Out-of-sample Sharpe versus benchmark",
            oos_sharpe_difference,
            min_sharpe_difference,
            evidence_source=(
                "validation.oos.strategy_sharpe - "
                "validation.oos.benchmark_sharpe"
            ),
            metric_unit="sharpe_ratio",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "parameter_robustness",
            "Positive-Sharpe share across bounded parameter grid",
            robust_parameter_ratio,
            min_robust_parameter_ratio,
            evidence_source=(
                "validation.parameter_sensitivity.positive_sharpe_count / "
                "valid_combination_count"
            ),
            metric_unit="ratio",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "sample_sufficiency",
            "Aligned observation count",
            float(strategy.get("observation_count") or 0),
            float(min_observations),
            evidence_source="metrics.observation_count",
            metric_unit="observations",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "data_quality_integrity",
            "Fatal data-quality issue count",
            None
            if fatal_data_issue_count is None
            else float(fatal_data_issue_count),
            0.0,
            operator="<=",
            severity="blocking",
            evidence_source="validation.data_quality.fatal_issues",
            metric_unit="count",
            evidence_timestamp=evidence_timestamp,
        ),
    ]

    observation_count = int(strategy.get("observation_count") or 0)
    if not comparable_period:
        verdict = "unavailable"
        rationale = "Strategy and benchmark periods are not directly comparable."
    elif observation_count < min_observations:
        verdict = "inconclusive"
        rationale = (
            f"Only {observation_count} observations are available; the configured "
            f"minimum is {min_observations}."
        )
    else:
        core = [
            item
            for item in checks
            if item["severity"] in {"core", "blocking"}
        ]
        available = [item for item in core if item["status"] != "unavailable"]
        passed = [item for item in available if item["status"] == "pass"]
        failed = [item for item in available if item["status"] == "fail"]
        missing = [item for item in core if item["status"] == "unavailable"]
        if missing:
            verdict = "inconclusive"
            rationale = (
                "Required OOS, robustness, or data-quality evidence is unavailable."
            )
        elif any(item["severity"] == "blocking" for item in failed):
            verdict = "fail"
            rationale = "A blocking data-integrity criterion failed."
        elif not failed:
            verdict = "pass"
            rationale = "All configured core benchmark criteria passed."
        elif not passed:
            verdict = "fail"
            rationale = "The configured core benchmark criteria failed."
        else:
            verdict = "partial"
            rationale = "Core benchmark evidence is mixed; inspect each criterion."

    passed_criteria = [
        item["check_id"] for item in checks if item["status"] == "pass"
    ]
    failed_criteria = [
        item["check_id"] for item in checks if item["status"] == "fail"
    ]
    inconclusive_criteria = [
        item["check_id"] for item in checks if item["status"] == "inconclusive"
    ]
    unavailable_criteria = [
        item["check_id"] for item in checks if item["status"] == "unavailable"
    ]

    return {
        "benchmark_type": "same_asset_buy_and_hold",
        "primary_benchmark": "Buy and Hold on the same asset",
        "why_appropriate": (
            "It uses the same asset, price series, and aligned period, isolating "
            "the effect of the trend rule and stated transaction costs."
        ),
        "comparison_period": {
            "start_date": strategy.get("start_date"),
            "end_date": strategy.get("end_date"),
            "observation_count": observation_count,
            "aligned": comparable_period,
        },
        "cost_assumption": (
            "Strategy metrics are net of |position change| × transaction_cost; "
            "buy-and-hold transaction cost is reported as zero in this study."
        ),
        "risk_adjusted_method": "Annualized Sharpe difference using 252 trading days.",
        "configured_success_criteria": {
            "min_excess_return": min_excess_return,
            "min_sharpe_difference": min_sharpe_difference,
            "min_drawdown_improvement": min_drawdown_improvement,
            "min_observations": min_observations,
            "min_cost_adjusted_return": min_cost_adjusted_return,
            "min_robust_parameter_ratio": min_robust_parameter_ratio,
        },
        "comparison": {
            "excess_return": excess_return,
            "excess_cagr": excess_cagr,
            "sharpe_difference": sharpe_difference,
            "drawdown_improvement": drawdown_improvement,
            "volatility_difference": volatility_difference,
            "cost_drag": strategy.get("total_transaction_costs"),
            "benchmark_outperformance": (
                excess_return is not None and excess_return > 0
            ),
            "risk_adjusted_outperformance": (
                sharpe_difference is not None
                and sharpe_difference >= min_sharpe_difference
            ),
        },
        "checks": checks,
        "verdict": verdict,
        "rationale": rationale,
        "passed_criteria": passed_criteria,
        "failed_criteria": failed_criteria,
        "inconclusive_criteria": inconclusive_criteria,
        "unavailable_criteria": unavailable_criteria,
        "supporting_metrics": {
            "strategy": strategy,
            "benchmark": benchmark,
            "comparison": {
                "excess_return": excess_return,
                "excess_cagr": excess_cagr,
                "sharpe_difference": sharpe_difference,
                "drawdown_improvement": drawdown_improvement,
                "volatility_difference": volatility_difference,
            },
        },
        "cash_reference": {
            "type": "zero_return",
            "total_return": 0.0,
            "note": "Reference baseline only; not the primary benchmark.",
        },
    }
