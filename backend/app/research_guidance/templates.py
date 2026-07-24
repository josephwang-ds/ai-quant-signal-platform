from __future__ import annotations

from typing import Any


def build_definition_template(request: dict[str, Any]) -> dict[str, Any]:
    universe = str(request["universe"]).strip()
    limitations = [
        str(item).strip()
        for item in request.get("known_limitations", [])
        if str(item).strip()
    ]
    validations = [
        str(item).strip()
        for item in request.get("available_validation", [])
        if str(item).strip()
    ]
    if request["research_type"] == "cross_sectional_factor":
        factor = str(request.get("parameters", {}).get("factor_id") or "factor")
        low_vol = factor == "low_volatility"
        return {
            "research_question": (
                f"Does {factor.replace('_', ' ')} produce positive RankIC and a "
                f"cost-adjusted Q5-minus-Q1 spread across {universe} over the "
                "configured evaluation period?"
            ),
            "hypothesis": (
                "Lower-volatility rankings may produce more stable risk-adjusted "
                "outcomes, although raw long-short return may not remain positive."
                if low_vol
                else "Relative performance persistence may produce positive average "
                "RankIC and a positive cost-adjusted Q5-minus-Q1 return."
            ),
            "null_hypothesis": (
                "The factor ranking has no meaningful relationship with subsequent "
                "return ranking, and the cost-adjusted long-short spread is not positive."
            ),
            "mechanism": (
                "The ranking is normalized so Q5 always represents the exposure "
                "expected to perform better under the stated factor hypothesis."
            ),
            "primary_benchmark": "Equal-weight universe return",
            "success_criteria": [
                {
                    "metric": "mean_rank_ic",
                    "operator": ">=",
                    "threshold_placeholder": "configured minimum above zero",
                    "reason": "Tests cross-sectional directional association.",
                },
                {
                    "metric": "positive_ic_ratio",
                    "operator": ">=",
                    "threshold_placeholder": "configured ratio",
                    "reason": "Tests consistency across rebalance periods.",
                },
                {
                    "metric": "q5_minus_q1_after_cost",
                    "operator": ">",
                    "threshold_placeholder": "0",
                    "reason": "Tests whether separation survives stated costs.",
                },
            ],
            "failure_criteria": [
                "Cost-adjusted Q5-minus-Q1 return is non-positive.",
                "Factor direction contradicts the hypothesis.",
                "Turnover eliminates the raw spread.",
                "Evidence is concentrated in one subperiod.",
            ],
            "required_validation": validations
            or [
                "RankIC and positive IC ratio",
                "Q1-Q5 equal-weight portfolios",
                "Turnover and cost review",
                "Chronological subperiod stability",
            ],
            "known_limitations": limitations,
            "clarifications_needed": [],
            "source": "template",
            "model": None,
        }

    symbol = universe
    return {
        "research_question": (
            f"Does the configured moving-average rule improve risk-adjusted "
            f"performance for {symbol} relative to same-asset Buy and Hold after "
            "transaction costs over the configured period?"
        ),
        "hypothesis": (
            "Persistent medium-term trends may reduce downside participation and "
            "improve risk-adjusted return, although the rule may lag during rapid "
            "reversals or strongly rising markets."
        ),
        "null_hypothesis": (
            "After costs, the strategy does not produce materially better "
            "risk-adjusted performance or drawdown control than Buy and Hold."
        ),
        "mechanism": (
            "A lagged moving-average signal participates in persistent trends and "
            "moves to cash when the short average falls below the long average."
        ),
        "primary_benchmark": f"{symbol} Buy and Hold",
        "success_criteria": [
            {
                "metric": "excess_return",
                "operator": ">=",
                "threshold_placeholder": "configured minimum",
                "reason": "Tests return improvement after stated costs.",
            },
            {
                "metric": "sharpe_difference",
                "operator": ">=",
                "threshold_placeholder": "configured margin",
                "reason": "Tests risk-adjusted improvement.",
            },
            {
                "metric": "drawdown_improvement",
                "operator": ">=",
                "threshold_placeholder": "configured material improvement",
                "reason": "Tests the downside-control mechanism.",
            },
        ],
        "failure_criteria": [
            "Benchmark underperformance occurs without meaningful risk reduction.",
            "Transaction costs eliminate the result.",
            "Out-of-sample evidence materially deteriorates.",
            "Nearby parameters reverse the conclusion.",
        ],
        "required_validation": validations
        or [
            "Aligned Buy-and-Hold comparison",
            "Chronological out-of-sample validation",
            "Parameter sensitivity",
            "Transaction-cost sensitivity",
            "Data-quality review",
        ],
        "known_limitations": limitations,
        "clarifications_needed": [],
        "source": "template",
        "model": None,
    }
