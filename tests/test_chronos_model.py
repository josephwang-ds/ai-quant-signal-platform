"""The foundation-model adapter, and the three ways it could quietly mislead.

A zero-shot forecaster needs no training fold, which removes the usual place a
leak hides and creates two new ones: the context could run into the window being
forecast, and a cache could hand back another model's numbers under this model's
name. The third risk is subtler -- comparing a challenger fed raw levels against
baselines fed logs, then reporting that it lost.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from filing_triage.chronos_model import (
    CONTEXT_LENGTH,
    LOG_SPACE,
    MODEL_ID,
    MODEL_REVISION,
    ForecastCache,
    _prepare,
    available,
    cached_forecast,
    context_key,
    forecast,
)
from filing_triage.volatility import HORIZON, QUANTILES


class TestTheChallengerGetsTheSameFooting:
    def test_the_model_is_given_logs_like_every_baseline(self):
        """Handing the challenger raw levels while the baselines work in logs
        would be a handicap, and reporting the loss that followed would be
        worse than not running the experiment."""
        assert LOG_SPACE
        prepared = _prepare(np.array([np.e, np.e ** 2], dtype=float))
        assert prepared == pytest.approx([1.0, 2.0])

    def test_a_zero_does_not_become_an_infinity(self):
        """One -inf in a batch silently poisons the whole batch."""
        assert np.isfinite(_prepare(np.array([0.0, 0.2]))).all()

    def test_the_context_is_truncated_from_the_end(self):
        """From the end, because the recent past is what a 20-session forecast
        depends on -- truncating from the front would hand the model history that
        stops before the filing."""
        long = np.linspace(0.1, 0.5, CONTEXT_LENGTH + 200)
        prepared = _prepare(long)
        assert len(prepared) == CONTEXT_LENGTH
        assert prepared[-1] == pytest.approx(np.log(long[-1]), rel=1e-5)


class TestTheCacheKnowsWhatProducedIt:
    def test_the_key_covers_the_series(self):
        assert context_key(np.ones(10)) != context_key(np.ones(10) * 2)

    def test_the_key_covers_the_horizon(self):
        assert context_key(np.ones(10), 20) != context_key(np.ones(10), 40)

    @pytest.mark.parametrize("field,value", [
        ("model", "some/other-model"),
        ("revision", "v0"),
        ("log_space", not LOG_SPACE),
        ("quantiles", [0.5]),
    ])
    def test_a_cache_from_another_configuration_is_discarded(self, tmp_path,
                                                             field, value):
        """Reusing it is how a number stops meaning what its column says while
        nothing fails."""
        index = {"model": MODEL_ID, "revision": MODEL_REVISION,
                 "horizon": HORIZON, "log_space": LOG_SPACE,
                 "quantiles": list(QUANTILES), "keys": {"abc": [1, 2, 3, 4, 5]}}
        index[field] = value
        (tmp_path / "index.json").write_text(json.dumps(index))
        assert ForecastCache(tmp_path).index["keys"] == {}

    def test_a_matching_cache_is_kept(self, tmp_path):
        """The other half: an invalidation rule that discards everything is not
        a cache."""
        cache = ForecastCache(tmp_path)
        cache.add("abc", [0.1, 0.2, 0.3, 0.4, 0.5])
        cache.save()
        assert "abc" in ForecastCache(tmp_path)

    def test_a_round_trip_returns_quantiles_by_level(self, tmp_path):
        cache = ForecastCache(tmp_path)
        cache.add(context_key(np.ones(80)), [0.1, 0.2, 0.3, 0.4, 0.5])
        cache.save()
        got = ForecastCache(tmp_path).get(context_key(np.ones(80)))
        assert list(got) == list(QUANTILES)
        assert got[0.5] == pytest.approx(0.3)

    def test_the_fingerprint_names_the_model_and_the_space(self, tmp_path):
        fingerprint = ForecastCache(tmp_path).fingerprint()
        assert fingerprint["model"] == MODEL_ID
        assert fingerprint["log_space"] is LOG_SPACE
        assert fingerprint["horizon"] == HORIZON


class TestAbsenceIsHandledRatherThanFaked:
    def test_a_missing_forecast_is_nan_not_zero(self, tmp_path):
        """Zero volatility would read as a confident calm rather than as an
        unforecast filing."""
        got = cached_forecast(np.ones(80), ForecastCache(tmp_path))
        assert all(np.isnan(v) for v in got.values())
        assert list(got) == list(QUANTILES)

    def test_a_context_too_short_to_forecast_is_skipped_not_padded(self, tmp_path):
        """Padding would invent history; the filing simply gets no forecast."""
        cache = ForecastCache(tmp_path)
        forecast([np.ones(10)], cache)
        assert cache.index["keys"] == {}

    def test_the_missing_dependency_names_the_extra(self, tmp_path, monkeypatch):
        monkeypatch.setattr("filing_triage.chronos_model.available", lambda: False)
        with pytest.raises(RuntimeError, match=r"\[ts\]"):
            forecast([np.linspace(0.1, 0.4, 200)], ForecastCache(tmp_path))

    def test_nothing_to_do_never_loads_a_model(self, tmp_path, monkeypatch):
        """A rerun over unchanged prices must not touch torch, which is what
        makes the export cheap enough to run often."""
        monkeypatch.setattr("filing_triage.chronos_model.available", lambda: False)
        cache = ForecastCache(tmp_path)
        cache.add(context_key(np.linspace(0.1, 0.4, 200)), [0.1, 0.2, 0.3, 0.4, 0.5])
        forecast([np.linspace(0.1, 0.4, 200)], cache)  # no raise

    def test_availability_is_reported_without_importing_the_stack(self):
        assert isinstance(available(), bool)
