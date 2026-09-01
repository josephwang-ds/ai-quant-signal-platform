"""Probabilities that mean what they say, and the split that makes them honest.

A model score is monotone in the right direction and nothing more. Calibration
is what turns 0.64 into *sixty-four in a hundred*, which is the only form the
reading policy downstream can be stated in.

The trap is where the calibrator learns. Fitted on the model's own training rows
it corrects scores the model has memorised and produces a beautiful reliability
curve that describes nothing. Fitted on the test fold it is simply cheating. So
each fold splits its training block in time: earlier fits the model, later fits
the calibrator, and the test fold sees neither.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage import pipeline
from filing_triage.calibration import (
    CALIBRATION_METHODS,
    _split_training_block,
    calibrated_walk_forward,
    calibration_comparison,
    expected_calibration_error,
    reliability_curve,
    within_fold_monotonicity,
)
from filing_triage.config import PipelineConfig
from filing_triage.self_relative import (
    attention_percentile,
    feature_frame,
    issuer_relative_target,
    self_relative_frame,
)


@pytest.fixture(scope="module")
def setup(world):
    result = pipeline.run(world.events, world.prices, world.membership,
                          PipelineConfig(), compute_importance=False,
                          compute_uncertainty=False)
    relative = self_relative_frame(result.events, result.features, result.labels)
    target = issuer_relative_target(result.events, result.labels).reindex(
        result.features.index)
    features = result.features.join(feature_frame(relative))
    features["self_attention_pct"] = attention_percentile(relative)
    aligned = result.labels.set_index("event_id").reindex(result.features.index)
    indexed = result.events.set_index("event_id")
    return {
        "features": features.select_dtypes(include=[np.number]),
        "target": target["self_target"],
        "relative": relative,
        "event_time": indexed.loc[result.features.index, "acceptance_time"],
        "label_end_time": pd.to_datetime(aligned["label_end_session"]).dt.tz_localize(
            result.events["acceptance_time"].dt.tz),
    }


@pytest.fixture(scope="module")
def result(setup):
    return calibrated_walk_forward(
        setup["features"], setup["target"], setup["event_time"],
        setup["label_end_time"], method="identity")


class TestTheCalibratorNeverSeesTheModelsRows:
    def test_the_split_is_in_time_order_and_disjoint(self):
        train = np.arange(100)
        fit, calib = _split_training_block(train, 0.30)
        assert len(fit) + len(calib) == len(train)
        assert not set(fit) & set(calib)
        assert fit.max() < calib.min(), "the calibrator must come after the model"

    def test_a_tiny_block_still_leaves_both_sides_non_empty(self):
        fit, calib = _split_training_block(np.arange(2), 0.30)
        assert len(fit) >= 1 and len(calib) >= 1


class TestUnknownTargetsAreDroppedNotFilled:
    def test_rows_without_a_target_are_never_scored(self, setup, result):
        unknown = setup["target"].isna()
        assert not set(setup["target"][unknown].index) & set(result.predictions.index)

    def test_something_survives(self, result):
        assert len(result.predictions) > 100


class TestCalibrationPreservesRankingWithinAFold:
    def test_every_fold_is_monotone(self, setup):
        """A calibrator is a monotone map, so within the fold it was fitted for
        it cannot reorder anything. Across folds it may -- five different maps
        stitched together are not one map -- which is why this is per fold and
        why the pooled AUC legitimately moves."""
        for method in CALIBRATION_METHODS:
            scored = calibrated_walk_forward(
                setup["features"], setup["target"], setup["event_time"],
                setup["label_end_time"], method=method)
            if scored.predictions.empty:
                continue
            checks = within_fold_monotonicity(scored)
            assert checks["monotone"].all(), f"{method} reordered inside a fold"


class TestCalibrationMetrics:
    def test_a_perfect_forecaster_has_no_calibration_error(self):
        y = np.array([0, 0, 1, 1])
        assert expected_calibration_error(y, y.astype(float)) == pytest.approx(0.0)

    def test_a_confidently_wrong_forecaster_has_maximal_error(self):
        y = np.array([0, 0, 1, 1])
        p = np.array([1.0, 1.0, 0.0, 0.0])
        assert expected_calibration_error(y, p) == pytest.approx(1.0)

    def test_the_reliability_curve_carries_its_counts(self):
        """A bin holding nine filings can sit far off the diagonal on noise
        alone. A curve drawn without counts invites reading that as bias."""
        rng = np.random.default_rng(0)
        p = rng.uniform(size=500)
        y = (rng.uniform(size=500) < p).astype(int)
        curve = reliability_curve(y, p)
        assert curve["count"].sum() == 500
        assert {"bin_low", "bin_high", "count", "mean_predicted",
                "observed_rate"} <= set(curve.columns)

    def test_the_brier_score_beats_predicting_the_base_rate(self, result):
        """Failing this means the model is worse than a constant, which is a
        bug rather than a modelling outcome."""
        assert result.metrics["brier"] <= result.metrics["brier_base_rate"]

    def test_the_uncalibrated_error_is_reported_too(self, result):
        """Without it there is no way to see that a calibration stage made
        things worse -- which on the real sample it does."""
        assert "ece_uncalibrated" in result.metrics


class TestTheCalibrationMethodIsChosenByEvidence:
    def test_every_method_is_scored_on_the_same_rows(self, setup):
        table = calibration_comparison(
            setup["features"], setup["target"], setup["event_time"],
            setup["label_end_time"])
        assert set(table["method"]) == set(CALIBRATION_METHODS)
        assert table["n_scored"].nunique() == 1

    def test_identity_is_a_first_class_option(self, setup):
        """"We checked and left the scores alone" has to be expressible, or the
        pipeline can only ever conclude that calibration helped."""
        table = calibration_comparison(
            setup["features"], setup["target"], setup["event_time"],
            setup["label_end_time"])
        assert "identity" in set(table["method"])

    def test_an_unknown_method_is_refused(self, setup):
        with pytest.raises(ValueError, match="unknown calibration method"):
            calibrated_walk_forward(
                setup["features"], setup["target"], setup["event_time"],
                setup["label_end_time"], method="platt-ish")
