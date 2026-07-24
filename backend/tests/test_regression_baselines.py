"""Regression baselines for fixed research calculation inputs.

Regression fixtures protect calculation behavior.
They do not guarantee future market performance.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.factor_validation.quantile_portfolios import compute_quantile_portfolios
from app.factor_validation.rank_ic import compute_rank_ic_series, summarize_ic
from app.research_execution.calculations import run_ma_crossover_research
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter

FIXTURES = Path(__file__).parent / "fixtures"
MA_BASELINE = FIXTURES / "ma_crossover_regression_baseline.json"
FACTOR_BASELINE = FIXTURES / "factor_rank_ic_regression_baseline.json"
SPY_CSV = FIXTURES / "spy_daily_sample.csv"


def test_ma_crossover_regression_baseline():
    expected = json.loads(MA_BASELINE.read_text())
    adapter = FixtureMarketDataAdapter(SPY_CSV)
    series = adapter.get_daily_ohlcv("SPY", "2018-01-01", None)
    result = run_ma_crossover_research(
        series.frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        risk_free_rate=0.0,
    )
    strategy = result.strategy_metrics
    benchmark = result.benchmark_metrics
    assert strategy.total_return == pytest.approx(
        expected["strategy"]["total_return"]
    )
    assert benchmark.total_return == pytest.approx(
        expected["benchmark"]["total_return"]
    )
    assert strategy.sharpe_ratio == pytest.approx(
        expected["strategy"]["sharpe_ratio"]
    )
    assert strategy.maximum_drawdown == pytest.approx(
        expected["strategy"]["maximum_drawdown"]
    )
    assert strategy.trade_count == expected["strategy"]["trade_count"]
    assert strategy.total_transaction_costs == pytest.approx(
        expected["strategy"]["total_transaction_costs"]
    )


def test_factor_rank_ic_regression_baseline():
    payload = json.loads(FACTOR_BASELINE.read_text())
    factor = pd.DataFrame.from_dict(payload["factor_panel"], orient="index")
    forward = pd.DataFrame.from_dict(payload["forward_panel"], orient="index")
    expected = payload["expected"]

    ic = compute_rank_ic_series(factor, forward)
    summary = summarize_ic(ic)
    assert summary["n_periods"] == expected["n_periods"]
    assert summary["mean_rank_ic"] == pytest.approx(expected["mean_rank_ic"])
    assert summary["median_rank_ic"] == pytest.approx(expected["median_rank_ic"])
    assert summary["positive_ic_ratio"] == pytest.approx(
        expected["positive_ic_ratio"]
    )
    assert summary["icir"] is None

    quantiles = compute_quantile_portfolios(
        factor, forward, cost_rate=payload["cost_rate"]
    )
    assert quantiles["period_returns"]["Q1"][0]["value"] == pytest.approx(
        expected["q1_period_return_0"]
    )
    assert quantiles["period_returns"]["Q5"][0]["value"] == pytest.approx(
        expected["q5_period_return_0"]
    )
    assert quantiles["long_short"]["period_returns"][0]["value"] == pytest.approx(
        expected["long_short_period_0"]
    )
    assert quantiles["turnover"]["series"][0]["value"] == pytest.approx(
        expected["turnover_0"]
    )
    assert quantiles["turnover"]["series"][1]["value"] == pytest.approx(
        expected["turnover_1"]
    )
    assert quantiles["transaction_cost"]["series"][0]["value"] == pytest.approx(
        expected["transaction_cost_0"]
    )
    assert quantiles["transaction_cost"]["total"] == pytest.approx(
        expected["transaction_cost_total"]
    )
    assert quantiles["long_short"]["period_returns_net_of_cost"][0][
        "value"
    ] == pytest.approx(expected["long_short_net_period_0"])
