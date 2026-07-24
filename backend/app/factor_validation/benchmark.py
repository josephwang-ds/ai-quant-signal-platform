"""Deterministic benchmark evidence for cross-sectional factor research."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _compound(values: list[float]) -> float | None:
    if not values:
        return None
    equity = 1.0
    for value in values:
        equity *= 1.0 + float(value)
    return float(equity - 1.0)


def _status(observed: float | None, threshold: float, operator: str) -> str:
    if observed is None or not np.isfinite(observed):
        return "unavailable"
    if operator == "<=":
        return "pass" if observed <= threshold else "fail"
    return "pass" if observed >= threshold else "fail"


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
    status = _status(observed, threshold, operator)
    explanation = (
        "The required metric was not calculated."
        if status == "unavailable"
        else (
            f"Observed {observed:.6f} {operator} configured threshold "
            f"{threshold:.6f}: {status}."
        )
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


def build_factor_benchmark(
    *,
    factor_id: str,
    forward_returns: pd.DataFrame,
    rank_ic: pd.Series,
    ic_summary: dict[str, Any],
    quantiles: dict[str, Any],
    min_mean_rank_ic: float,
    min_positive_ic_ratio: float,
    min_net_long_short_return: float,
    min_q5_excess_return: float,
    max_mean_turnover: float,
    min_observations: int,
    min_icir: float = 0.0,
    evidence_timestamp: str | None = None,
) -> dict[str, Any]:
    """Compare factor evidence with equal-weight universe and zero baselines."""
    quantile_dates = {str(value) for value in quantiles.get("dates", [])}
    aligned_forward = forward_returns.loc[
        [str(index) in quantile_dates for index in forward_returns.index]
    ]
    equal_weight_period = aligned_forward.mean(axis=1, skipna=True).dropna()
    universe_final = _compound([float(value) for value in equal_weight_period])

    def _final_quantile(label: str) -> float | None:
        series = quantiles["cumulative_returns"].get(label) or []
        return float(series[-1]["value"]) if series else None

    q5_final = _final_quantile("Q5")
    q1_final = _final_quantile("Q1")
    q5_excess = (
        q5_final - universe_final
        if q5_final is not None and universe_final is not None
        else None
    )
    q1_excess = (
        q1_final - universe_final
        if q1_final is not None and universe_final is not None
        else None
    )
    net_ls = quantiles["long_short"].get("cumulative_final_net_of_cost")
    mean_turnover = quantiles["turnover"].get("mean")
    mean_rank_ic = ic_summary.get("mean_rank_ic")
    positive_ic_ratio = ic_summary.get("positive_ic_ratio")

    # Directional stability: both chronological halves must retain non-negative IC.
    half = len(rank_ic) // 2
    subperiod_means = (
        [float(rank_ic.iloc[:half].mean()), float(rank_ic.iloc[half:].mean())]
        if half > 0 and len(rank_ic.iloc[half:]) > 0
        else []
    )
    stable_subperiods = (
        min(subperiod_means) if len(subperiod_means) == 2 else None
    )

    period_means: list[float] = []
    for label in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        values = quantiles["period_returns"].get(label) or []
        if not values:
            period_means = []
            break
        period_means.append(float(np.mean([item["value"] for item in values])))
    monotonic_steps = (
        sum(
            1
            for left, right in zip(period_means, period_means[1:])
            if right >= left
        )
        / 4.0
        if len(period_means) == 5
        else None
    )

    checks = [
        _check(
            "q5_vs_equal_weight",
            "Q5 return versus equal-weight universe",
            q5_excess,
            min_q5_excess_return,
            evidence_source=(
                "quantiles.cumulative_returns.Q5 - "
                "benchmark.equal_weight_universe_return"
            ),
            metric_unit="decimal_return",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "mean_rank_ic",
            "Mean RankIC versus zero",
            mean_rank_ic,
            min_mean_rank_ic,
            evidence_source="ic.summary.mean_rank_ic",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "positive_ic_ratio",
            "Positive IC ratio",
            positive_ic_ratio,
            min_positive_ic_ratio,
            evidence_source="ic.summary.positive_ic_ratio",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "icir",
            "IC information ratio",
            ic_summary.get("icir"),
            min_icir,
            severity="supporting",
            evidence_source="ic.summary.icir",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "long_short_after_cost",
            "Q5 minus Q1 return after costs",
            net_ls,
            min_net_long_short_return,
            evidence_source="long_short.cumulative_final_net_of_cost",
            metric_unit="decimal_return",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "quantile_monotonicity",
            "Directional quantile ordering",
            monotonic_steps,
            0.75,
            severity="supporting",
            evidence_source="mean period returns for Q1 through Q5",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "turnover",
            "Mean long-short turnover",
            mean_turnover,
            max_mean_turnover,
            operator="<=",
            severity="supporting",
            evidence_source="quantiles.turnover.mean",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "subperiod_stability",
            "RankIC direction across chronological halves",
            stable_subperiods,
            0.0,
            severity="core",
            evidence_source="minimum mean RankIC across two chronological halves",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "observation_count",
            "Factor observation count",
            float(ic_summary.get("n_periods") or 0),
            float(min_observations),
            evidence_source="ic.summary.n_periods",
            metric_unit="periods",
            evidence_timestamp=evidence_timestamp,
        ),
        _check(
            "factor_direction_integrity",
            "Normalized factor direction",
            1.0,
            1.0,
            severity="blocking",
            evidence_source="benchmark.ranking_convention",
            metric_unit="boolean",
            evidence_timestamp=evidence_timestamp,
        ),
        {
            "check_id": "universe_quality_limitation",
            "name": "Historical universe membership quality",
            "status": "inconclusive",
            "observed_value": None,
            "configured_threshold": None,
            "threshold": None,
            "operator": "documented",
            "metric_unit": "limitation",
            "explanation": (
                "The sector-ETF preset is static and does not reconstruct "
                "historical index membership."
            ),
            "evidence_source": "provenance.universe_symbols",
            "severity": "guardrail",
            "evidence_timestamp": evidence_timestamp,
        },
    ]

    n_periods = int(ic_summary.get("n_periods") or 0)
    core = [item for item in checks if item["severity"] == "core"]
    available_core = [item for item in core if item["status"] != "unavailable"]
    passed_core = [item for item in available_core if item["status"] == "pass"]
    failed_core = [item for item in available_core if item["status"] == "fail"]
    if n_periods < min_observations:
        verdict = "inconclusive"
        rationale = (
            f"Only {n_periods} factor periods are available; the configured "
            f"minimum is {min_observations}."
        )
    elif len(available_core) < len(core):
        verdict = "inconclusive"
        rationale = "At least one core factor benchmark metric is unavailable."
    elif any(
        item["severity"] == "blocking" and item["status"] == "fail"
        for item in checks
    ):
        verdict = "fail"
        rationale = "A blocking factor-integrity criterion failed."
    elif not failed_core:
        verdict = "pass"
        rationale = "All configured core factor benchmark checks passed."
    elif not passed_core:
        verdict = "fail"
        rationale = "All configured core factor benchmark checks failed."
    else:
        verdict = "partial"
        rationale = "Core factor evidence is mixed; inspect each check."

    return {
        "benchmark_type": "equal_weight_universe",
        "primary_benchmark": "Equal-weight universe return",
        "why_appropriate": (
            "It represents the selected cross-section without imposing the "
            "factor ranking, allowing Q5 and Q1 outcomes to be compared with "
            "the same investable universe."
        ),
        "comparison_period": {
            "start_date": str(aligned_forward.index[0])
            if len(aligned_forward.index)
            else None,
            "end_date": str(aligned_forward.index[-1])
            if len(aligned_forward.index)
            else None,
            "factor_periods": n_periods,
        },
        "cost_assumption": (
            "Long-short net returns subtract turnover × configured cost rate "
            "at each rebalance."
        ),
        "risk_adjusted_method": (
            "Factor validity uses RankIC/ICIR, directional quantile ordering, "
            "turnover, and chronological stability rather than strategy Sharpe."
        ),
        "ranking_convention": {
            "raw_direction": (
                "lower raw volatility is better"
                if factor_id == "low_volatility"
                else "higher raw momentum is better"
            ),
            "normalization": (
                "factor = -realized_volatility"
                if factor_id == "low_volatility"
                else "factor = trailing 12-1 momentum"
            ),
            "q5_meaning": "Q5 always represents the strongest expected exposure.",
            "q1_meaning": "Q1 always represents the weakest expected exposure.",
        },
        "configured_success_criteria": {
            "min_mean_rank_ic": min_mean_rank_ic,
            "min_positive_ic_ratio": min_positive_ic_ratio,
            "min_net_long_short_return": min_net_long_short_return,
            "min_q5_excess_return": min_q5_excess_return,
            "max_mean_turnover": max_mean_turnover,
            "min_observations": min_observations,
            "min_icir": min_icir,
        },
        "comparison": {
            "equal_weight_universe_return": universe_final,
            "q5_return": q5_final,
            "q1_return": q1_final,
            "q5_excess_return": q5_excess,
            "q1_excess_return": q1_excess,
            "q5_minus_q1_gross": quantiles["long_short"].get("cumulative_final"),
            "q5_minus_q1_after_cost": net_ls,
            "cost_drag": (
                None
                if quantiles["long_short"].get("cumulative_final") is None
                or net_ls is None
                else quantiles["long_short"]["cumulative_final"] - net_ls
            ),
        },
        "checks": checks,
        "verdict": verdict,
        "rationale": rationale,
        "passed_criteria": [
            item["check_id"] for item in checks if item["status"] == "pass"
        ],
        "failed_criteria": [
            item["check_id"] for item in checks if item["status"] == "fail"
        ],
        "inconclusive_criteria": [
            item["check_id"]
            for item in checks
            if item["status"] == "inconclusive"
        ],
        "unavailable_criteria": [
            item["check_id"]
            for item in checks
            if item["status"] == "unavailable"
        ],
        "supporting_metrics": {
            "ic_summary": ic_summary,
            "comparison": {
                "equal_weight_universe_return": universe_final,
                "q5_return": q5_final,
                "q1_return": q1_final,
                "q5_excess_return": q5_excess,
                "q1_excess_return": q1_excess,
                "q5_minus_q1_gross": quantiles["long_short"].get(
                    "cumulative_final"
                ),
                "q5_minus_q1_after_cost": net_ls,
                "mean_turnover": mean_turnover,
                "transaction_cost": quantiles["transaction_cost"].get("total"),
                "subperiod_mean_rank_ic": subperiod_means,
            },
        },
    }
