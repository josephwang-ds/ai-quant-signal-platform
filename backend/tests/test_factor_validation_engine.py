"""Golden tests for RankIC and quantile portfolio pure engines."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from app.factor_validation.quantile_portfolios import compute_quantile_portfolios
from app.factor_validation.rank_ic import (
    compute_rank_ic_series,
    rolling_ic,
    summarize_ic,
)


def _panel(rows: dict[str, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


def test_rank_ic_perfect_positive_correlation():
    factor = _panel(
        {
            "2020-01": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
            "2020-02": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
        }
    )
    forward = _panel(
        {
            "2020-01": {"A": 0.01, "B": 0.02, "C": 0.03, "D": 0.04, "E": 0.05},
            "2020-02": {"A": 0.0, "B": 0.1, "C": 0.2, "D": 0.3, "E": 0.4},
        }
    )
    ic = compute_rank_ic_series(factor, forward)
    assert list(ic.values) == pytest.approx([1.0, 1.0])
    summary = summarize_ic(ic)
    assert summary["mean_rank_ic"] == pytest.approx(1.0)
    assert summary["median_rank_ic"] == pytest.approx(1.0)
    assert summary["positive_ic_ratio"] == pytest.approx(1.0)
    assert summary["icir"] is None  # std = 0
    assert summary["n_periods"] == 2


def test_rank_ic_skips_thin_cross_section():
    factor = _panel({"2020-01": {"A": 1.0, "B": 2.0}})
    forward = _panel({"2020-01": {"A": 0.1, "B": 0.2}})
    ic = compute_rank_ic_series(factor, forward)
    assert ic.empty
    assert summarize_ic(ic)["mean_rank_ic"] is None


def test_rank_ic_icir_and_rolling():
    # Alternating +1 / -1 RankIC via perfect / inverse rankings
    dates = [f"2020-{m:02d}" for m in range(1, 15)]
    factor_rows = {}
    forward_rows = {}
    for i, d in enumerate(dates):
        factor_rows[d] = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
        if i % 2 == 0:
            forward_rows[d] = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
        else:
            forward_rows[d] = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
    ic = compute_rank_ic_series(_panel(factor_rows), _panel(forward_rows))
    assert len(ic) == 14
    summary = summarize_ic(ic)
    assert summary["mean_rank_ic"] == pytest.approx(0.0)
    assert summary["positive_ic_ratio"] == pytest.approx(0.5)
    assert summary["icir"] == pytest.approx(0.0)
    rolled = rolling_ic(ic, window=12)
    assert len(rolled) == 3
    assert rolled.iloc[0] == pytest.approx(0.0)


def test_quantile_long_short_and_turnover_first_build():
    # High factor → high forward return → Q5 beats Q1
    factor = _panel(
        {
            "2020-01": {
                "A": 1,
                "B": 2,
                "C": 3,
                "D": 4,
                "E": 5,
                "F": 6,
                "G": 7,
                "H": 8,
                "I": 9,
                "J": 10,
            },
            "2020-02": {
                "A": 1,
                "B": 2,
                "C": 3,
                "D": 4,
                "E": 5,
                "F": 6,
                "G": 7,
                "H": 8,
                "I": 9,
                "J": 10,
            },
        }
    )
    forward = _panel(
        {
            "2020-01": {
                "A": 0.0,
                "B": 0.01,
                "C": 0.02,
                "D": 0.03,
                "E": 0.04,
                "F": 0.05,
                "G": 0.06,
                "H": 0.07,
                "I": 0.08,
                "J": 0.09,
            },
            "2020-02": {
                "A": 0.0,
                "B": 0.01,
                "C": 0.02,
                "D": 0.03,
                "E": 0.04,
                "F": 0.05,
                "G": 0.06,
                "H": 0.07,
                "I": 0.08,
                "J": 0.09,
            },
        }
    )
    result = compute_quantile_portfolios(factor, forward, cost_rate=0.001)
    assert result["n_rebalances"] == 2
    # 10 names → 2 per quantile; Q1={A,B} mean 0.005; Q5={I,J} mean 0.085
    assert result["period_returns"]["Q1"][0]["value"] == pytest.approx(0.005)
    assert result["period_returns"]["Q5"][0]["value"] == pytest.approx(0.085)
    assert result["long_short"]["period_returns"][0]["value"] == pytest.approx(0.08)
    # First build: |+0.5|+|+0.5|+|-0.5|+|-0.5| = 2 → turnover 1.0
    assert result["turnover"]["series"][0]["value"] == pytest.approx(1.0)
    # Second period identical weights → turnover 0
    assert result["turnover"]["series"][1]["value"] == pytest.approx(0.0)
    assert result["transaction_cost"]["series"][0]["value"] == pytest.approx(0.001)
    assert result["transaction_cost"]["total"] == pytest.approx(0.001)
    # Cumulative LS: (1.08)*(1.08)-1
    expected_cum = 1.08 * 1.08 - 1.0
    assert result["long_short"]["cumulative_final"] == pytest.approx(expected_cum)


def test_quantile_rejects_negative_cost():
    factor = _panel({"2020-01": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}})
    forward = _panel({"2020-01": {"A": 0.1, "B": 0.1, "C": 0.1, "D": 0.1, "E": 0.1}})
    with pytest.raises(ValueError):
        compute_quantile_portfolios(factor, forward, cost_rate=-0.01)


def test_quantile_skips_missing_forward_members():
    factor = _panel(
        {
            "2020-01": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
        }
    )
    # E missing forward → period skipped entirely
    forward = _panel(
        {
            "2020-01": {"A": 0.1, "B": 0.1, "C": 0.1, "D": 0.1, "E": float("nan")},
        }
    )
    result = compute_quantile_portfolios(factor, forward, cost_rate=0.001)
    assert result["n_rebalances"] == 0


def test_quantile_net_long_short_deducts_turnover_cost():
    factor = _panel(
        {
            "2020-01": {
                "A": 1,
                "B": 2,
                "C": 3,
                "D": 4,
                "E": 5,
                "F": 6,
                "G": 7,
                "H": 8,
                "I": 9,
                "J": 10,
            },
        }
    )
    forward = _panel(
        {
            "2020-01": {
                "A": 0.0,
                "B": 0.01,
                "C": 0.02,
                "D": 0.03,
                "E": 0.04,
                "F": 0.05,
                "G": 0.06,
                "H": 0.07,
                "I": 0.08,
                "J": 0.09,
            },
        }
    )
    result = compute_quantile_portfolios(factor, forward, cost_rate=0.001)
    gross = result["long_short"]["period_returns"][0]["value"]
    net = result["long_short"]["period_returns_net_of_cost"][0]["value"]
    cost = result["transaction_cost"]["series"][0]["value"]
    assert net == pytest.approx(gross - cost)
    assert result["long_short"]["cumulative_final_net_of_cost"] == pytest.approx(net)


def test_momentum_higher_past_return_ranks_higher():
    from app.factor_validation.factors import build_momentum_factor

    idx = pd.date_range("2019-01-31", periods=14, freq="ME")
    # Build daily-ish panel with month ends only for simplicity
    prices = pd.DataFrame(
        {
            "A": np.linspace(100, 110, len(idx)),
            "B": np.linspace(100, 200, len(idx)),
        },
        index=idx,
    )
    factor = build_momentum_factor(prices, lookback_months=12, skip_months=1)
    last = factor.dropna(how="all").iloc[-1]
    assert last["B"] > last["A"]


def test_low_volatility_negates_vol_so_low_vol_ranks_higher():
    from app.factor_validation.factors import build_low_volatility_factor

    idx = pd.bdate_range("2020-01-01", periods=120)
    rng = np.random.RandomState(0)
    calm = 100 * np.cumprod(1 + rng.normal(0, 0.002, size=len(idx)))
    noisy = 100 * np.cumprod(1 + rng.normal(0, 0.02, size=len(idx)))
    prices = pd.DataFrame({"CALM": calm, "NOISY": noisy}, index=idx)
    factor = build_low_volatility_factor(prices, window_days=60)
    last = factor.dropna(how="all").iloc[-1]
    assert last["CALM"] > last["NOISY"]


def test_no_lookahead_factor_uses_only_past_prices():
    from app.factor_validation.factors import (
        align_factor_and_forward,
        build_monthly_forward_returns,
        build_momentum_factor,
    )

    idx = pd.bdate_range("2018-01-01", periods=400)
    prices = pd.DataFrame(
        {sym: np.linspace(50, 100, len(idx)) + i for i, sym in enumerate("ABCDE")},
        index=idx,
    )
    # Corrupt the future after a cut date — factor at cut must be unchanged
    cut = idx[250]
    factor_full = build_momentum_factor(prices)
    prices_future_tampered = prices.copy()
    prices_future_tampered.loc[prices_future_tampered.index > cut] *= 10.0
    factor_tampered = build_momentum_factor(prices_future_tampered)
    # Formation dates on/before cut should match
    common = factor_full.index.intersection(factor_tampered.index)
    before = common[common <= cut]
    if len(before) == 0:
        pytest.skip("no overlapping month-ends before cut")
    pd.testing.assert_frame_equal(
        factor_full.loc[before],
        factor_tampered.loc[before],
    )
    forward = build_monthly_forward_returns(prices, holding_period_months=1)
    f, r = align_factor_and_forward(factor_full, forward)
    # Forward at t uses prices after t; factor at t must not include those
    assert f.index.equals(r.index)
