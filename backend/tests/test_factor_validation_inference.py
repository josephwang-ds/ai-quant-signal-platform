"""Tests for HAC inference.

The central claim these protect: on an autocorrelated series the HAC
t-statistic must be materially smaller than the naive iid one. If that
relationship ever inverts, the correction is not being applied and every
verdict built on it is overstated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.factor_validation.inference import (
    MIN_OBSERVATIONS_FOR_INFERENCE,
    breakeven_capital,
    incremental_signal_value,
    lag_sensitivity,
    naive_iid_tstat,
    net_economic_value_bps,
    newey_west_lag,
    newey_west_mean_tstat,
)


def _ar1(n: int, phi: float, mean: float, sigma: float, seed: int) -> pd.Series:
    """AR(1) series with a planted mean."""
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0.0, sigma, n)
    out = np.empty(n)
    out[0] = shocks[0]
    for i in range(1, n):
        out[i] = phi * out[i - 1] + shocks[i]
    return pd.Series(out + mean)


class TestLagRule:
    def test_matches_newey_west_1994_rule(self):
        assert newey_west_lag(100) == 4
        assert newey_west_lag(250) == 4
        assert newey_west_lag(1000) == 6  # 4 * 10^(2/9) = 6.67 -> 6

    def test_is_deterministic_in_n(self):
        assert newey_west_lag(240) == newey_west_lag(240)

    def test_degenerate_inputs(self):
        assert newey_west_lag(0) == 0
        assert newey_west_lag(-5) == 0


class TestNeweyWestMean:
    def test_hac_penalises_positive_autocorrelation(self):
        """The headline property. Persistent series -> smaller t-statistic."""
        series = _ar1(400, phi=0.7, mean=0.02, sigma=0.05, seed=7)
        hac = newey_west_mean_tstat(series)["tstat"]
        naive = naive_iid_tstat(series)
        assert hac is not None and naive is not None
        assert abs(hac) < abs(naive)
        assert abs(hac) < 0.85 * abs(naive)  # materially, not marginally

    def test_iid_series_barely_penalised(self):
        series = _ar1(400, phi=0.0, mean=0.02, sigma=0.05, seed=11)
        hac = newey_west_mean_tstat(series)["tstat"]
        naive = naive_iid_tstat(series)
        assert abs(hac - naive) / abs(naive) < 0.25

    def test_recovers_a_planted_mean(self):
        series = _ar1(500, phi=0.3, mean=0.04, sigma=0.02, seed=3)
        result = newey_west_mean_tstat(series)
        assert result["mean"] == pytest.approx(0.04, abs=0.01)
        assert result["tstat"] > 2.0

    def test_zero_mean_series_is_not_significant(self):
        series = _ar1(400, phi=0.2, mean=0.0, sigma=0.05, seed=5)
        assert abs(newey_west_mean_tstat(series)["tstat"]) < 2.0

    def test_reports_lags_and_n(self):
        result = newey_west_mean_tstat(_ar1(200, 0.4, 0.01, 0.03, seed=1))
        assert result["n_observations"] == 200
        assert result["lags"] == newey_west_lag(200)
        assert result["method"] == "newey_west"


class TestUnavailableRatherThanWrong:
    def test_empty_series(self):
        result = newey_west_mean_tstat(pd.Series(dtype=float))
        assert result["tstat"] is None
        assert result["unavailable_reason"] == "no observations"

    def test_short_series_refuses_to_claim(self):
        result = newey_west_mean_tstat(pd.Series([0.1] * 5))
        assert result["tstat"] is None
        assert str(MIN_OBSERVATIONS_FOR_INFERENCE) in result["unavailable_reason"]

    def test_constant_series(self):
        result = newey_west_mean_tstat(pd.Series([0.02] * 50))
        assert result["tstat"] is None
        assert result["unavailable_reason"] == "zero variance"

    def test_nans_are_dropped_not_propagated(self):
        values = [0.01, np.nan, 0.02, np.nan] * 20
        result = newey_west_mean_tstat(pd.Series(values))
        assert result["n_observations"] == 40
        assert result["tstat"] is not None

    def test_never_returns_zero_in_place_of_unavailable(self):
        """Anti-fabrication: absence must not look like a measurement."""
        for series in (pd.Series(dtype=float), pd.Series([1.0] * 3)):
            assert newey_west_mean_tstat(series)["tstat"] is not True
            assert newey_west_mean_tstat(series)["tstat"] is None


class TestIncrementalSkill:
    def test_detects_a_real_increment(self):
        rng = np.random.default_rng(21)
        baseline = pd.Series(rng.normal(0.01, 0.03, 300))
        enriched = baseline + rng.normal(0.008, 0.01, 300)
        result = incremental_signal_value(enriched, baseline)
        assert result["tstat"] > 2.0
        assert result["enriched_mean"] > result["baseline_mean"]

    def test_no_increment_is_not_significant(self):
        rng = np.random.default_rng(22)
        baseline = pd.Series(rng.normal(0.01, 0.03, 300))
        enriched = baseline.copy()
        result = incremental_signal_value(enriched, baseline)
        assert result["tstat"] is None  # identical arms -> zero variance
        assert result["unavailable_reason"] == "zero variance"

    def test_noisy_but_useless_channel_fails_the_bar(self):
        """A text channel that adds noise and no information must not pass."""
        rng = np.random.default_rng(23)
        baseline = pd.Series(rng.normal(0.01, 0.03, 400))
        enriched = baseline + rng.normal(0.0, 0.02, 400)
        assert abs(incremental_signal_value(enriched, baseline)["tstat"]) < 2.0

    def test_aligns_on_shared_index_only(self):
        left = pd.Series([0.05] * 30, index=range(30))
        right = pd.Series([0.01] * 30, index=range(15, 45))
        result = incremental_signal_value(left, right)
        assert result["n_observations"] == 15

    def test_disjoint_inputs_report_unavailable(self):
        left = pd.Series([0.05] * 10, index=range(10))
        right = pd.Series([0.01] * 10, index=range(100, 110))
        result = incremental_signal_value(left, right)
        assert result["tstat"] is None
        assert result["unavailable_reason"] == "no overlapping observations"


class TestHoldingPeriodLagFloor:
    """P1: overlapping forward returns force a minimum bandwidth."""

    def test_holding_floor_binds_when_larger_than_auto_rule(self):
        assert newey_west_lag(400, holding_periods=1) == 5
        assert newey_west_lag(400, holding_periods=21) == 20

    def test_auto_rule_binds_when_holding_is_short(self):
        assert newey_west_lag(2000, holding_periods=2) == newey_west_lag(2000, 1)

    def test_invalid_holding_period_rejected(self):
        with pytest.raises(ValueError, match="holding_periods must be"):
            newey_west_lag(100, holding_periods=0)

    def test_overlapping_returns_get_a_smaller_tstat(self):
        """A 21-period holding floor must not inflate significance."""
        series = _ar1(500, phi=0.6, mean=0.02, sigma=0.05, seed=31)
        short = newey_west_mean_tstat(series, holding_periods=1)["tstat"]
        overlapping = newey_west_mean_tstat(series, holding_periods=21)["tstat"]
        assert abs(overlapping) < abs(short)

    def test_lag_rule_is_recorded(self):
        auto = newey_west_mean_tstat(_ar1(200, 0.3, 0.01, 0.03, seed=2))
        assert "auto" in auto["lag_rule"]
        manual = newey_west_mean_tstat(_ar1(200, 0.3, 0.01, 0.03, seed=2), lags=9)
        assert manual["lag_rule"] == "explicit override"
        assert manual["lags"] == 9


class TestLagSensitivity:
    def test_reports_a_tstat_per_bandwidth(self):
        series = _ar1(400, phi=0.6, mean=0.02, sigma=0.05, seed=41)
        grid = lag_sensitivity(series, [0, 5, 10, 20])
        assert [row["lags"] for row in grid] == [0, 5, 10, 20]
        assert all(row["tstat"] is not None for row in grid)

    def test_exposes_bandwidth_dependence(self):
        """If a result only survives at lag 0, the reader should see that."""
        series = _ar1(400, phi=0.8, mean=0.015, sigma=0.05, seed=42)
        grid = lag_sensitivity(series, [0, 20])
        assert abs(grid[0]["tstat"]) > abs(grid[1]["tstat"])


class TestNetEconomicValueUnits:
    """P0 of the review: currency and bps cannot be subtracted directly."""

    def test_inference_cost_converted_to_bps_on_capital(self):
        result = net_economic_value_bps(12.0, 4.0, 400.0, 1_000_000.0)
        assert result["inference_cost_bps"] == pytest.approx(4.0)
        assert result["net_economic_value_bps"] == pytest.approx(4.0)

    def test_same_model_flips_sign_at_smaller_capital(self):
        """The finding this enables: viability depends on AUM."""
        big = net_economic_value_bps(12.0, 4.0, 400.0, 5_000_000.0)
        small = net_economic_value_bps(12.0, 4.0, 400.0, 200_000.0)
        assert big["net_economic_value_bps"] > 0
        assert small["net_economic_value_bps"] < 0

    def test_breakeven_capital_is_where_it_crosses_zero(self):
        capital = breakeven_capital(12.0, 4.0, 400.0)
        assert capital == pytest.approx(500_000.0)
        at_breakeven = net_economic_value_bps(12.0, 4.0, 400.0, capital)
        assert at_breakeven["net_economic_value_bps"] == pytest.approx(0.0, abs=1e-9)

    def test_unprofitable_before_inference_never_breaks_even(self):
        assert breakeven_capital(3.0, 4.0, 400.0) is None

    def test_non_positive_capital_is_unavailable_not_infinite(self):
        result = net_economic_value_bps(12.0, 4.0, 400.0, 0.0)
        assert result["net_economic_value_bps"] is None
        assert "positive" in result["unavailable_reason"]


class TestHacImplementationIsCorrect:
    """The numpy HAC must equal the reference implementation exactly."""

    def test_matches_statsmodels_when_available(self):
        sm = pytest.importorskip("statsmodels.api")
        from app.factor_validation.inference import _hac_mean_and_se

        for n, phi in ((50, 0.0), (137, 0.3), (400, 0.7), (1000, -0.4)):
            series = _ar1(n, phi=phi, mean=0.02, sigma=0.05, seed=n)
            lags = newey_west_lag(n)
            _, se = _hac_mean_and_se(series.to_numpy(), lags)
            mine = float(series.mean()) / se
            reference = float(
                sm.OLS(series.to_numpy(), np.ones(n))
                .fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
                .tvalues[0]
            )
            assert mine == pytest.approx(reference, abs=1e-9)

    def test_runs_without_statsmodels_installed(self):
        """The point of the rewrite: no optional dependency in the hot path."""
        import app.factor_validation.inference as module
        import inspect

        source = inspect.getsource(module)
        assert "import statsmodels" not in source

    def test_bartlett_weights_keep_variance_non_negative(self):
        """Strongly negatively autocorrelated series must not yield a NaN se."""
        series = _ar1(300, phi=-0.9, mean=0.01, sigma=0.05, seed=99)
        result = newey_west_mean_tstat(series)
        assert result["se"] is not None
        assert result["se"] > 0
