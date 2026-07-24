from __future__ import annotations

import json

from app.factor_validation.benchmark import build_factor_benchmark
from app.factor_validation.quantile_portfolios import compute_quantile_portfolios
from app.factor_validation.rank_ic import compute_rank_ic_series, summarize_ic
from app.research_copilot.llm_port import LlmResult
from app.research_copilot.reviewer_service import ResearchReviewerService
from app.research_execution.benchmark import build_trend_benchmark_comparison
from app.research_guidance.service import ResearchGuidanceError, ResearchGuidanceService

import pandas as pd
import pytest


def test_trend_benchmark_retains_evidence_and_configured_thresholds():
    strategy = {
        "total_return": 0.18,
        "cagr": 0.09,
        "sharpe_ratio": 1.1,
        "annualized_volatility": 0.12,
        "maximum_drawdown": -0.12,
        "total_transaction_costs": 0.02,
        "observation_count": 500,
        "start_date": "2020-01-01",
        "end_date": "2022-01-01",
    }
    benchmark = {
        "total_return": 0.15,
        "cagr": 0.075,
        "sharpe_ratio": 0.8,
        "annualized_volatility": 0.16,
        "maximum_drawdown": -0.22,
        "observation_count": 500,
        "start_date": "2020-01-01",
        "end_date": "2022-01-01",
    }
    result = build_trend_benchmark_comparison(
        strategy,
        benchmark,
        min_excess_return=0.01,
        min_sharpe_difference=0.1,
        min_drawdown_improvement=0.05,
        min_observations=252,
        oos_sharpe_difference=0.2,
        robust_parameter_ratio=0.75,
        fatal_data_issue_count=0,
    )
    assert result["verdict"] == "pass"
    assert result["comparison"]["excess_return"] == pytest.approx(0.03)
    assert result["comparison"]["drawdown_improvement"] == pytest.approx(0.10)
    assert result["configured_success_criteria"]["min_excess_return"] == 0.01
    assert all("evidence_source" in check for check in result["checks"])


def test_trend_benchmark_marks_misaligned_periods_unavailable():
    strategy = {
        "total_return": 0.1,
        "cagr": 0.1,
        "sharpe_ratio": 1.0,
        "annualized_volatility": 0.1,
        "maximum_drawdown": -0.1,
        "total_transaction_costs": 0.01,
        "observation_count": 300,
        "start_date": "2020-01-01",
        "end_date": "2022-01-01",
    }
    benchmark = {**strategy, "start_date": "2020-02-01"}
    result = build_trend_benchmark_comparison(
        strategy,
        benchmark,
        min_excess_return=0,
        min_sharpe_difference=0,
        min_drawdown_improvement=0,
        min_observations=252,
    )
    assert result["verdict"] == "unavailable"


def test_factor_benchmark_documents_low_vol_direction_and_equal_weight():
    factor = pd.DataFrame(
        {
            "A": [-5.0, -5.0],
            "B": [-4.0, -4.0],
            "C": [-3.0, -3.0],
            "D": [-2.0, -2.0],
            "E": [-1.0, -1.0],
        },
        index=["2021-01", "2021-02"],
    )
    forward = pd.DataFrame(
        {
            "A": [-0.02, -0.01],
            "B": [-0.01, 0.00],
            "C": [0.00, 0.01],
            "D": [0.01, 0.02],
            "E": [0.03, 0.04],
        },
        index=factor.index,
    )
    rank_ic = compute_rank_ic_series(factor, forward)
    quantiles = compute_quantile_portfolios(factor, forward, cost_rate=0.001)
    result = build_factor_benchmark(
        factor_id="low_volatility",
        forward_returns=forward,
        rank_ic=rank_ic,
        ic_summary=summarize_ic(rank_ic),
        quantiles=quantiles,
        min_mean_rank_ic=0,
        min_positive_ic_ratio=0.5,
        min_net_long_short_return=0,
        min_q5_excess_return=0,
        max_mean_turnover=2,
        min_observations=2,
    )
    assert result["benchmark_type"] == "equal_weight_universe"
    assert result["ranking_convention"]["normalization"] == "factor = -realized_volatility"
    assert "Q5 always" in result["ranking_convention"]["q5_meaning"]
    assert result["comparison"]["equal_weight_universe_return"] is not None


class ValidDefinitionLlm:
    def generate(self, **_kwargs):
        return LlmResult(
            text=json.dumps(
                {
                    "research_question": "Can the defined rule improve risk-adjusted evidence?",
                    "hypothesis": "Persistent trends may improve risk-adjusted outcomes.",
                    "null_hypothesis": "The rule does not improve outcomes.",
                    "mechanism": "Lagged signals may reduce downside participation.",
                    "primary_benchmark": {
                        "name": "SPY Buy and Hold",
                        "reason": "Same asset and aligned period.",
                    },
                    "proposed_success_criteria": [
                        {
                            "criterion_id": "trend-sharpe-difference",
                            "metric": "sharpe_difference",
                            "operator": "gte",
                            "threshold": None,
                            "severity": "core",
                            "description": "Compare risk-adjusted outcomes.",
                            "source": "ai_proposed",
                            "threshold_guidance": "configured margin",
                            "reason": "Risk-adjusted comparison.",
                        }
                    ],
                    "failure_criteria": [
                        {
                            "condition": "OOS deterioration.",
                            "reason": "The hypothesis would be contradicted.",
                        }
                    ],
                    "required_validation": ["Chronological OOS."],
                    "known_limitations": ["Historical evidence only."],
                    "clarifications_needed": [],
                }
            ),
            model="fake-definition-model",
        )


def guidance_request(use_llm: bool) -> dict:
    return {
        "research_type": "trend_following",
        "universe": "SPY",
        "parameters": {"short_window": 20, "long_window": 60},
        "benchmark_type": "same_asset_buy_and_hold",
        "start_date": "2018-01-01",
        "end_date": None,
        "transaction_cost": 0.001,
        "available_validation": [],
        "known_limitations": ["Historical evidence only."],
        "use_llm": use_llm,
    }


def test_definition_guidance_works_without_llm():
    result = ResearchGuidanceService().execute(guidance_request(False))
    assert result["source"] == "template"
    assert result["primary_benchmark"] == "SPY Buy and Hold"
    assert result["success_criteria"]


def test_definition_guidance_accepts_only_structured_llm_output():
    result = ResearchGuidanceService(
        ResearchReviewerService(ValidDefinitionLlm())
    ).execute(guidance_request(True))
    assert result["source"] == "llm"
    assert result["model"] == "fake-definition-model"

    class InvalidLlm:
        def generate(self, **_kwargs):
            return LlmResult(text="not-json", model="bad")

    with pytest.raises(ResearchGuidanceError):
        ResearchGuidanceService(
            ResearchReviewerService(InvalidLlm())
        ).execute(guidance_request(True))
