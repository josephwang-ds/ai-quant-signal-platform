"""The volatility forecast, and the one line that decides whether it means anything.

A forecast evaluation is unusually easy to get wrong in a way that looks like
success: let one session of the target window into the context and the model
becomes clairvoyant, with nothing in the metrics to say so. These pin down the
boundary, the scoring rules, and the property that makes each baseline the
opponent it is supposed to be.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage.volatility import (
    ANNUALISE,
    BASELINES,
    HORIZON,
    QUANTILES,
    VolatilityPanel,
    baseline_forecast,
    build_forecast_frame,
    compare,
    coverage,
    coverage_by_regime,
    pinball_loss,
    realized_volatility,
    score_forecasts,
    volatility_regime,
)

SESSIONS = pd.bdate_range("2020-01-01", periods=1400)


def _panel(ticker="AAPL", seed=0, spike_from=None, spike=0.25):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.01, len(SESSIONS))
    if spike_from is not None:
        returns[spike_from:] = rng.normal(0, spike, len(returns) - spike_from)
    frame = pd.DataFrame({"ticker": ticker, "date": SESSIONS, "ret": returns})
    return VolatilityPanel.build(frame), returns


class TestTheContextStopsBeforeTheTarget:
    """The whole experiment rests on this. A context that ran one session too far
    would not fail anything -- it would look like a very good forecaster."""

    def test_a_violent_target_window_leaves_the_context_untouched(self):
        anchor = 1000
        calm, _ = _panel(seed=1)
        stormy, _ = _panel(seed=1, spike_from=anchor)
        assert np.allclose(calm.trailing_series("AAPL", anchor - 1),
                           stormy.trailing_series("AAPL", anchor - 1))

    def test_the_storm_does_reach_the_target(self):
        """The other half: if the target were also unaffected, the test above
        would pass for the wrong reason."""
        anchor = 1000
        calm, _ = _panel(seed=1)
        stormy, _ = _panel(seed=1, spike_from=anchor)
        assert (stormy.forward_volatility("AAPL", anchor)
                > 5 * calm.forward_volatility("AAPL", anchor))

    def test_the_context_ends_one_session_before_entry(self):
        """Not at entry: the entry session is the first session being forecast,
        and a reader acting on the card has not seen its close."""
        panel, returns = _panel()
        anchor = 900
        context = panel.trailing_series("AAPL", anchor - 1)
        expected = realized_volatility(returns[anchor - HORIZON:anchor])
        assert context[-1] == pytest.approx(expected)

    def test_a_target_running_past_the_data_is_missing_not_short(self):
        """A truncated window would look artificially calm and score well."""
        panel, _ = _panel()
        assert np.isnan(panel.forward_volatility("AAPL", len(SESSIONS) - 5))


class TestTheScoringRules:
    def test_pinball_is_minimised_at_the_true_quantile(self):
        rng = np.random.default_rng(3)
        actual = rng.lognormal(-1.3, 0.4, 20_000)
        for q in (0.1, 0.5, 0.9):
            truth = float(np.quantile(actual, q))
            best = pinball_loss(actual, np.full_like(actual, truth), q)
            for offset in (-0.05, 0.05):
                worse = pinball_loss(actual, np.full_like(actual, truth + offset), q)
                assert worse > best

    def test_pinball_penalises_the_two_directions_differently(self):
        """Which is what makes it a quantile score rather than a dressed-up
        absolute error."""
        actual = np.array([1.0])
        under = pinball_loss(actual, np.array([0.5]), 0.9)
        over = pinball_loss(actual, np.array([1.5]), 0.9)
        assert under > over

    def test_coverage_counts_the_band_it_claims(self):
        actual = np.array([1.0, 2.0, 3.0, 4.0])
        assert coverage(actual, np.full(4, 1.5), np.full(4, 3.5)) == pytest.approx(0.5)

    def test_missing_rows_are_excluded_rather_than_counted_as_misses(self):
        actual = np.array([1.0, np.nan])
        assert coverage(actual, np.zeros(2), np.full(2, 2.0)) == pytest.approx(1.0)

    def test_width_is_reported_beside_coverage(self):
        """An interval from zero to infinity has perfect coverage. Reporting the
        two together is what stops that from reading as success."""
        frame = pd.DataFrame({"actual": [0.3] * 10, "q10": [0.0] * 10,
                              "q25": [0.0] * 10, "q50": [0.3] * 10,
                              "q75": [9.0] * 10, "q90": [9.0] * 10})
        scored = score_forecasts(frame)
        assert scored["coverage_80"] == pytest.approx(1.0)
        assert scored["width_80"] == pytest.approx(9.0)

    def test_a_frame_missing_a_quantile_raises(self):
        with pytest.raises(KeyError, match="q90"):
            score_forecasts(pd.DataFrame({"actual": [0.3], "q10": [0.1],
                                          "q25": [0.2], "q50": [0.3],
                                          "q75": [0.4]}))


class TestEachBaselineIsTheOpponentItClaims:
    @pytest.fixture(scope="class")
    def history(self):
        panel, _ = _panel(seed=5)
        return panel.trailing_series("AAPL", 1200)

    @pytest.mark.parametrize("name", BASELINES)
    def test_quantiles_come_out_ordered_and_positive(self, name, history):
        """Volatility is bounded below by zero, which a Gaussian interval on the
        raw scale would not respect."""
        forecast = baseline_forecast(name, history)
        values = [forecast[q] for q in QUANTILES]
        assert all(v > 0 for v in values)
        assert values == sorted(values)

    def test_climatology_barely_notices_the_present(self, history):
        """It quotes the issuer's own distribution, in which today is one
        observation out of a thousand rather than the answer. A version that
        tracked the last value would be a worse random walk, not a second
        opinion -- so tripling today may move it by rounding, not by a third."""
        moved = history.copy()
        moved[-1] *= 3
        base = baseline_forecast("climatology", history)[0.5]
        assert abs(baseline_forecast("climatology", moved)[0.5] - base) < 0.01 * base

    def test_the_random_walk_does(self, history):
        moved = history.copy()
        moved[-1] *= 3
        assert (baseline_forecast("random_walk", moved)[0.5]
                > 2 * baseline_forecast("random_walk", history)[0.5])

    def test_har_declines_rather_than_extrapolating_from_nothing(self):
        panel, _ = _panel()
        short = panel.trailing_series("AAPL", 300)[:120]
        assert np.isnan(baseline_forecast("har", short)[0.5])

    def test_the_band_is_asymmetric_in_volatility_units(self, history):
        """Because it is symmetric in logs, which is the shape realized
        volatility has."""
        forecast = baseline_forecast("random_walk", history)
        below = forecast[0.5] - forecast[0.1]
        above = forecast[0.9] - forecast[0.5]
        assert above > below

    def test_an_unknown_baseline_is_an_error_not_a_silent_nan(self):
        with pytest.raises(ValueError, match="unknown baseline"):
            baseline_forecast("lstm", np.ones(400))


class TestTheComparisonIsFair:
    @pytest.fixture(scope="class")
    def built(self):
        rng = np.random.default_rng(11)
        frames = []
        for ticker in ("AAA", "BBB"):
            frames.append(pd.DataFrame({
                "ticker": ticker, "date": SESSIONS,
                "ret": rng.normal(0, 0.012, len(SESSIONS))}))
        returns = pd.concat(frames, ignore_index=True)
        # Distinct (ticker, session) pairs on purpose: two issuers over twenty
        # sessions, each pair once, so a context shared by two rows would be a
        # real defect rather than an artefact of the fixture.
        events = pd.DataFrame({
            "event_id": [f"e{i}" for i in range(40)],
            "ticker": ["AAA"] * 20 + ["BBB"] * 20,
            "entry_session": list(SESSIONS[1100:1120]) * 2})
        return build_forecast_frame(events, returns)

    def test_every_event_gets_its_own_context(self, built):
        frame, contexts = built
        assert set(contexts) == set(frame.index)
        assert len({c.tobytes() for c in contexts.values()}) == len(contexts)

    def test_a_forecaster_cannot_win_by_declining_the_hard_rows(self, built):
        """`compare` scores every forecaster on the rows all of them answered."""
        frame, _ = built
        full = pd.DataFrame(
            {f"q{int(q * 100)}": 0.2 for q in QUANTILES}, index=frame.index)
        full["actual"] = frame["actual"]
        picky = full.copy()
        picky.loc[picky.index[:30], "q50"] = np.nan
        table = compare(frame, {"full": full, "picky": picky})
        assert table["filings"].nunique() == 1

    def test_regimes_partition_the_sample(self, built):
        frame, _ = built
        regimes = volatility_regime(frame)
        assert len(regimes) == len(frame)
        assert set(regimes) <= {"calm", "ordinary", "turbulent", "all"}

    def test_regime_coverage_is_reported_per_band(self, built):
        frame, _ = built
        table = pd.DataFrame(
            {f"q{int(q * 100)}": 0.1 + q for q in QUANTILES}, index=frame.index)
        table["actual"] = frame["actual"]
        rows = coverage_by_regime(table, volatility_regime(frame))
        assert set(rows.columns) >= {"regime", "coverage_50", "coverage_80",
                                     "width_80", "pinball_mean"}
        assert rows["filings"].sum() <= len(frame)


class TestRealizedVolatility:
    def test_it_is_annualised(self):
        daily = np.full(60, 0.01)
        daily[::2] = -0.01
        assert realized_volatility(daily) == pytest.approx(0.01 * ANNUALISE, rel=0.02)

    def test_a_window_of_one_has_no_volatility(self):
        assert np.isnan(realized_volatility(np.array([0.01])))

    def test_missing_bars_are_skipped_not_treated_as_zero_returns(self):
        """A NaN read as a flat session would understate volatility, which is
        the direction that makes a risk card dangerous."""
        with_gap = np.array([0.02, np.nan, -0.02, 0.02, -0.02])
        without = np.array([0.02, -0.02, 0.02, -0.02])
        assert realized_volatility(with_gap) == pytest.approx(
            realized_volatility(without))
