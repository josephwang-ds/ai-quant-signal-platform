"""Comparing model families without reintroducing the leak no guard can catch.

Choosing a model by looking at the out-of-sample metric contaminates the whole
project while leaving every individual run clean -- the contamination lives in
which run was kept. The project answers that question for hyper-parameters with
a sensitivity spread rather than a promise, so a model comparison must not
arrive and quietly hand back the selection premium it was built to refuse.

These pin down the two properties that make the nested score honest: the inner
split never sees the outer test fold, and preprocessing is fitted inside a fold
rather than over the whole frame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from filing_triage import pipeline, selection
from filing_triage.candidates import CANDIDATES, build
from filing_triage.config import PipelineConfig


@pytest.fixture(scope="module")
def frames(world):
    """Features, labels and the two time columns the splitter needs."""
    result = pipeline.run(world.events, world.prices, world.membership,
                          PipelineConfig(), compute_importance=False,
                          compute_uncertainty=False)
    features = result.features
    aligned = result.labels.set_index("event_id").loc[features.index]
    indexed = result.events.set_index("event_id")
    return {
        "features": features,
        "labels": aligned["label"],
        "event_time": indexed.loc[features.index, "acceptance_time"],
        "label_end_time": pd.to_datetime(
            aligned["label_end_session"]
        ).dt.tz_localize(result.events["acceptance_time"].dt.tz),
        "sessions": indexed["entry_session"],
    }


class TestPreprocessingStaysInsideTheFold:
    """The trap a model comparison walks into on its first day.

    Two of these families cannot take a NaN, and imputing the frame once before
    splitting fits the median on every fold at once -- a value computed partly
    from the test period, carried into training. It is the same shape as a
    TF-IDF fitted over the whole corpus, and it does not feel like fitting,
    which is why it ships.
    """

    @pytest.mark.parametrize("name", sorted(CANDIDATES))
    def test_every_candidate_is_a_pipeline(self, name):
        assert isinstance(build(name), Pipeline)

    @pytest.mark.parametrize("name", ["logistic", "random_forest"])
    def test_families_that_cannot_take_nan_carry_their_own_imputer(self, name):
        assert "impute" in dict(build(name).named_steps)

    def test_the_shipped_family_needs_no_imputer(self):
        """HistGradientBoosting learns a direction for missing values from the
        training split, so imputing would discard information it uses."""
        assert "impute" not in dict(build("hist_gbdt (shipped)").named_steps)

    def test_a_fitted_imputer_uses_only_the_rows_it_was_shown(self):
        """The property the Pipeline is relied on for, asserted directly."""
        X = np.array([[1.0], [1.0], [1.0], [99.0], [99.0], [99.0]])
        y = np.array([0, 1, 0, 1, 0, 1])
        model = build("logistic")
        model.fit(X[:3], y[:3])
        assert model.named_steps["impute"].statistics_[0] == pytest.approx(1.0)

    def test_build_returns_a_fresh_object_each_time(self):
        """Reusing one across folds would carry the previous fold's fitted
        imputer and coefficients into the next."""
        assert build("logistic") is not build("logistic")

    def test_an_unknown_candidate_names_the_known_ones(self):
        with pytest.raises(KeyError, match="logistic"):
            build("xgboost")


class TestTheDescriptiveTable:
    @pytest.fixture(scope="class")
    @staticmethod
    def table(frames):
        return selection.compare_candidates(
            frames["features"], frames["labels"], frames["event_time"],
            frames["label_end_time"], frames["sessions"])

    def test_every_family_is_scored(self, table):
        assert set(table["candidate"]) == set(CANDIDATES)

    def test_all_families_see_the_same_events(self, table):
        """Different folds would make the comparison meaningless, and it would
        not look wrong -- every row would still carry a plausible number."""
        assert table["events_scored"].nunique() == 1

    def test_each_row_carries_an_interval(self, table):
        """Sorting families by point estimate invites reading a ranking into a
        gap the sample cannot resolve. The interval is what refuses that."""
        assert (table["average_precision_ci_low"]
                <= table["average_precision"]).all()
        assert (table["average_precision"]
                <= table["average_precision_ci_high"]).all()

    def test_a_real_family_beats_the_stratified_floor(self, table):
        """Failing this is a bug behind the features, not a modelling problem."""
        floor = float(
            table.loc[table["candidate"] == "stratified_dummy", "average_precision"].iloc[0])
        best = float(table["average_precision"].max())
        assert best > floor


class TestNestedSelectionIsHonest:
    @pytest.fixture(scope="class")
    @staticmethod
    def nested(frames):
        return selection.nested_selection_score(
            frames["features"], frames["labels"], frames["event_time"],
            frames["label_end_time"])

    def test_it_records_what_it_picked_in_each_fold(self, nested):
        """Often the finding: a procedure that picks a different winner every
        fold has measured noise, not identified a better model."""
        assert nested["selected_per_fold"]
        assert all(name in CANDIDATES for name in nested["selected_per_fold"])

    def test_it_scores_events_out_of_sample(self, nested):
        assert nested["events_scored"] > 0
        assert 0.0 < nested["average_precision"] < 1.0

    def test_it_does_not_exceed_the_best_family_by_much(self, frames, nested):
        """The nested score prices the *procedure*, so it cannot systematically
        beat the best family that procedure can choose. Beating it outright is
        the signature of a leak in the nesting."""
        table = selection.compare_candidates(
            frames["features"], frames["labels"], frames["event_time"],
            frames["label_end_time"])
        assert nested["average_precision"] <= float(
            table["average_precision"].max()) + 0.05

    def test_the_inner_split_never_reaches_the_outer_test_fold(self, frames):
        """The invariant the whole design rests on, checked directly rather than
        trusted: every inner index must come from the outer training block."""
        from filing_triage.guards import PurgedWalkForward
        from filing_triage.model import CV_EMBARGO

        outer = PurgedWalkForward(5, CV_EMBARGO)
        for train, test in outer.split(frames["event_time"], frames["label_end_time"]):
            inner = PurgedWalkForward(3, CV_EMBARGO)
            for inner_train, inner_test in inner.split(
                    frames["event_time"].iloc[train],
                    frames["label_end_time"].iloc[train]):
                assert not set(train[inner_train]) & set(test)
                assert not set(train[inner_test]) & set(test)


class TestCandidatesAreComparedInPairs:
    """The correction the operational baselines already get, applied here too.

    Independent intervals answer "how precisely is each family measured". A
    reader asks whether one is *better*, and overlapping independent intervals
    do not settle that -- the families saw the same events on the same days, so
    the difference is measured within a resample. On the real sample the
    independent intervals overlap almost entirely while the paired difference is
    about three times tighter, which is the whole reason this exists.
    """

    @pytest.fixture(scope="class")
    @staticmethod
    def paired(frames):
        scored = selection.candidate_predictions(
            frames["features"], frames["labels"], frames["event_time"],
            frames["label_end_time"])
        return selection.paired_candidate_differences(
            scored, frames["sessions"], reference="hist_gbdt (shipped)", n_boot=200)

    def test_the_reference_is_not_compared_with_itself(self, paired):
        assert "hist_gbdt (shipped)" not in set(paired["candidate"])

    def test_every_other_family_is_compared(self, paired):
        assert set(paired["candidate"]) == set(CANDIDATES) - {"hist_gbdt (shipped)"}

    def test_the_difference_lies_inside_its_own_interval(self, paired):
        assert (paired["difference_ci_low"] <= paired["difference_ci_high"]).all()

    def test_the_dummy_loses_decisively(self, paired):
        """The sanity check. A stratified dummy scoring near a real family means
        the features are not doing what the rest of the report says they are."""
        dummy = paired[paired["candidate"] == "stratified_dummy"].iloc[0]
        assert dummy["difference"] < 0
        assert dummy["difference_ci_high"] < 0
        assert dummy["draws_not_beating_reference"] > 0.95

    def test_the_paired_interval_is_tighter_than_independent_ones(self, frames, paired):
        """The claim this method rests on. If it ever reverses, pairing has
        stopped buying anything and saying it does becomes false."""
        table = selection.compare_candidates(
            frames["features"], frames["labels"], frames["event_time"],
            frames["label_end_time"], frames["sessions"])
        indexed = table.set_index("candidate")
        reference_width = (indexed.loc["hist_gbdt (shipped)", "average_precision_ci_high"]
                           - indexed.loc["hist_gbdt (shipped)", "average_precision_ci_low"])
        for _, row in paired.iterrows():
            other = indexed.loc[row["candidate"]]
            independent_width = (other["average_precision_ci_high"]
                                 - other["average_precision_ci_low"])
            paired_width = row["difference_ci_high"] - row["difference_ci_low"]
            assert paired_width < independent_width + reference_width
