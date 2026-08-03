"""Golden tests for the single-factor alpha/beta regression and decomposition."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.factor_validation.capm import (
    build_benchmark_period_returns,
    decompose_performance,
    period_return_series,
    regress_alpha_beta,
)


def _series(values: dict[str, float]) -> pd.Series:
    return pd.Series(values, dtype=float)


def test_regress_alpha_beta_recovers_known_parameters():
    # portfolio = alpha + beta * benchmark + tiny noise, so the fit should
    # recover both parameters almost exactly and produce a finite t-stat.
    true_alpha = 0.01
    true_beta = 0.6
    benchmark = _series(
        {
            "2020-01": 0.02,
            "2020-02": -0.01,
            "2020-03": 0.03,
            "2020-04": 0.00,
            "2020-05": 0.015,
            "2020-06": -0.02,
        }
    )
    noise = [0.0006, -0.0004, 0.0003, -0.0002, 0.0005, -0.0006]
    portfolio = _series(
        {
            date: true_alpha + true_beta * value + noise[i]
            for i, (date, value) in enumerate(benchmark.items())
        }
    )

    result = regress_alpha_beta(portfolio, benchmark)

    assert result["n_observations"] == 6
    assert result["beta"] == pytest.approx(true_beta, abs=0.05)
    assert result["alpha"] == pytest.approx(true_alpha, abs=0.003)
    assert result["alpha_annualized"] == pytest.approx(
        (1.0 + result["alpha"]) ** 12 - 1.0
    )
    assert result["t_stat_alpha"] is not None
    assert np.isfinite(result["t_stat_alpha"])
    assert result["r_squared"] is not None
    assert 0.0 <= result["r_squared"] <= 1.0
    assert result["alpha_annualized_ci_low"] is not None
    assert result["alpha_annualized_ci_high"] is not None
    assert (
        result["alpha_annualized_ci_low"]
        < result["alpha_annualized"]
        < result["alpha_annualized_ci_high"]
    )


def test_regress_alpha_beta_insufficient_observations_returns_none_fields():
    benchmark = _series({"2020-01": 0.01, "2020-02": 0.02})
    portfolio = _series({"2020-01": 0.03, "2020-02": 0.01})

    result = regress_alpha_beta(portfolio, benchmark)

    assert result["n_observations"] == 2
    assert result["alpha"] is None
    assert result["beta"] is None
    assert result["t_stat_alpha"] is None
    assert result["r_squared"] is None
    assert result["alpha_annualized_ci_low"] is None
    assert result["alpha_annualized_ci_high"] is None


def test_regress_alpha_beta_aligns_on_intersection_only():
    benchmark = _series({"2020-01": 0.01, "2020-02": 0.02, "2020-03": 0.03})
    portfolio = _series({"2020-01": 0.02, "2020-03": 0.04})  # 2020-02 missing

    result = regress_alpha_beta(portfolio, benchmark)

    assert result["n_observations"] == 2


def test_build_benchmark_period_returns_missing_periods_are_nan_not_zero():
    close = pd.Series(
        {
            pd.Timestamp("2020-01-31"): 100.0,
            pd.Timestamp("2020-02-29"): 102.0,
            pd.Timestamp("2020-03-31"): 104.0,
        }
    )
    returns = build_benchmark_period_returns(
        close,
        holding_period_months=1,
        period_labels=["2020-01", "2020-02", "2020-99"],
    )
    assert returns.loc["2020-01"] == pytest.approx(102.0 / 100.0 - 1.0)
    assert pd.isna(returns.loc["2020-99"])


def test_period_return_series_round_trip():
    payload = [{"date": "2020-01", "value": 0.05}, {"date": "2020-02", "value": -0.02}]
    series = period_return_series(payload)
    assert list(series.index) == ["2020-01", "2020-02"]
    assert series.iloc[0] == pytest.approx(0.05)


def test_decompose_performance_identity_holds():
    dates = ["2020-01", "2020-02", "2020-03"]
    gross = [{"date": d, "value": v} for d, v in zip(dates, [0.03, -0.01, 0.02])]
    net = [{"date": d, "value": v} for d, v in zip(dates, [0.025, -0.015, 0.017])]
    benchmark = _series({"2020-01": 0.02, "2020-02": -0.005, "2020-03": 0.01})
    beta = 0.5

    result = decompose_performance(
        gross_period_returns=gross,
        net_period_returns=net,
        benchmark_returns=benchmark,
        beta=beta,
    )

    assert result["dates"] == dates
    net_series = period_return_series(net)
    cum_net_expected = np.cumsum(net_series.to_numpy())
    for i in range(len(dates)):
        beta_c = result["cumulative_beta_contribution"][i]["value"]
        residual = result["cumulative_residual_alpha"][i]["value"]
        assert beta_c + residual == pytest.approx(cum_net_expected[i])

    gross_series = period_return_series(gross)
    cum_cost_expected = np.cumsum((gross_series - net_series).to_numpy())
    for i in range(len(dates)):
        assert result["cumulative_cost_drag"][i]["value"] == pytest.approx(
            cum_cost_expected[i]
        )


def test_decompose_performance_unavailable_when_beta_none():
    result = decompose_performance(
        gross_period_returns=[{"date": "2020-01", "value": 0.01}],
        net_period_returns=[{"date": "2020-01", "value": 0.01}],
        benchmark_returns=_series({"2020-01": 0.01}),
        beta=None,
    )
    assert result["dates"] == []
    assert result["cumulative_beta_contribution"] == []
    assert "Unavailable" in result["methodology"]
