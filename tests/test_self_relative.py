"""Issuer-relative history, and the two cutoffs that keep it causal.

The cross-sectional ranker asks which of today's filings deserve a read. This
layer asks whether a filing is unusual *for its own issuer*, which needs a
reference distribution built from that issuer's past -- and a reference
distribution is exactly where the future gets in.

Two rules, and the second is the one that is easy to miss. A knowledge-time
quantity may look at every filing accepted earlier. An outcome-derived quantity
may only look at filings whose windows had already closed, because a reaction is
not knowable until it has finished happening.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.self_relative import (
    FEATURE_COLUMNS,
    OUTCOME_COLUMNS,
    HistoryPolicy,
    assert_no_outcome_features,
    attention_percentile,
    causal_percentile,
    causal_robust_z,
    feature_frame,
    issuer_relative_target,
    self_relative_frame,
)


@pytest.fixture(scope="module")
def scored(world):
    return pipeline.run(world.events, world.prices, world.membership,
                        PipelineConfig(), compute_importance=False,
                        compute_uncertainty=False)


@pytest.fixture(scope="module")
def relative(scored):
    return self_relative_frame(scored.events, scored.features, scored.labels)


class TestPercentilesLookOnlyBackwards:
    def test_the_first_value_has_no_percentile(self):
        """Nothing precedes it, so there is no distribution to sit in. NaN, not
        0.5, which would assert it was perfectly ordinary."""
        out = causal_percentile(np.array([3.0, 1.0, 2.0]))
        assert np.isnan(out[0])

    def test_each_value_is_ranked_against_earlier_ones_only(self):
        out = causal_percentile(np.array([1.0, 2.0, 3.0]))
        assert out[1] == pytest.approx(1.0)   # beats the one before it
        assert out[2] == pytest.approx(1.0)   # beats both

    def test_a_later_value_cannot_change_an_earlier_percentile(self):
        """The property the whole module rests on, checked by truncation: if
        appending a filing changed an earlier one's percentile, that earlier
        filing was reading the future."""
        values = np.array([1.0, 5.0, 2.0, 9.0, 4.0])
        full = causal_percentile(values)
        for cut in range(2, len(values)):
            assert np.allclose(causal_percentile(values[:cut]), full[:cut],
                               equal_nan=True)

    def test_ties_land_in_the_middle(self):
        """A filing identical to its own history belongs at the centre of it,
        not at either edge."""
        out = causal_percentile(np.array([2.0, 2.0]))
        assert out[1] == pytest.approx(0.5)

    def test_the_usable_window_shortens_the_lookback(self):
        """What the resolved-only rule does: the third value may look at one
        earlier value rather than two."""
        values = np.array([10.0, 0.0, 5.0])
        assert causal_percentile(values, usable=np.array([0, 1, 1]))[2] == pytest.approx(0.0)
        assert causal_percentile(values, usable=np.array([0, 1, 2]))[2] == pytest.approx(0.5)


class TestRobustZ:
    def test_a_constant_history_yields_no_z(self):
        """MAD is zero, so a z-score is undefined rather than infinite. Saying
        so beats inventing a spread the data does not have."""
        assert np.isnan(causal_robust_z(np.array([1.0, 1.0, 1.0, 4.0]))[3])

    def test_an_outlier_in_history_does_not_redefine_normal(self):
        """The reason for median/MAD: one extreme filing must not move the scale
        that is supposed to identify extreme filings."""
        calm = np.array([1.0, 1.1, 0.9, 1.0, 5.0])
        wild = np.array([1.0, 1.1, 0.9, 40.0, 5.0])
        z_calm = causal_robust_z(calm)[4]
        z_wild = causal_robust_z(wild)[4]
        assert abs(z_calm - z_wild) < abs(z_calm) * 0.75


class TestTheTwoCutoffsDiffer:
    def test_outcome_depth_never_exceeds_knowledge_depth(self, relative):
        assert (relative["self_resolved_depth"]
                <= relative["self_history_depth"]).all()

    def test_the_stricter_rule_actually_bites(self, relative):
        """If the two depths never differed, the distinction would be theatre.
        On the real sample it changes 8.7% of rows."""
        assert (relative["self_resolved_depth"]
                < relative["self_history_depth"]).any()


class TestOutcomeColumnsCannotReachAModel:
    def test_the_two_column_sets_do_not_overlap(self):
        assert not set(FEATURE_COLUMNS) & set(OUTCOME_COLUMNS)

    def test_the_guard_names_what_leaked(self, relative):
        with pytest.raises(ValueError, match="self_reaction_pct"):
            assert_no_outcome_features(relative.columns)

    def test_the_safe_subset_passes_the_guard(self, relative):
        assert_no_outcome_features(feature_frame(relative).columns)

    def test_the_safe_subset_is_not_empty(self, relative):
        assert len(feature_frame(relative).columns) >= 4


class TestMinimumHistoryPolicy:
    @pytest.mark.parametrize("depth,expected", [
        (0, "insufficient_history"), (4, "insufficient_history"),
        (5, "low"), (9, "low"), (10, "medium"), (19, "medium"), (20, "standard"),
    ])
    def test_the_bands_are_what_the_plan_specified(self, depth, expected):
        assert HistoryPolicy().confidence(depth) == expected

    def test_shallow_history_is_labelled_not_hidden(self, relative):
        shallow = relative["self_history_depth"] < HistoryPolicy().minimum
        if not shallow.any():
            pytest.skip("this world has no shallow issuers")
        assert (relative.loc[shallow, "self_confidence"]
                == "insufficient_history").all()


class TestTheIssuerRelativeTarget:
    @pytest.fixture(scope="class")
    @staticmethod
    def target(scored):
        return issuer_relative_target(scored.events, scored.labels)

    def test_it_is_binary_or_unknown(self, target):
        known = target["self_target"].dropna()
        assert set(known.unique()) <= {0.0, 1.0}

    def test_unknown_history_is_nan_not_zero(self, target):
        """Zero would assert the filing was ordinary, and a model trained on
        that assertion learns to call every unknown issuer routine."""
        shallow = target["self_target_depth"] < HistoryPolicy().minimum
        if not shallow.any():
            pytest.skip("this world has no shallow issuers")
        assert target.loc[shallow, "self_target"].isna().all()

    def test_the_positive_rate_is_near_the_complement_of_the_quantile(self, target):
        """An 80th-percentile threshold should fire about a fifth of the time.
        Far from that means the threshold is not tracking the distribution."""
        rate = float(target["self_target"].mean())
        assert 0.10 < rate < 0.35

    def test_the_threshold_never_sees_the_filing_it_judges(self, scored):
        """Recomputed independently: a filing's threshold must be derivable from
        strictly earlier resolved filings of the same issuer."""
        target = issuer_relative_target(scored.events, scored.labels)
        frame = (scored.events.set_index("event_id")[["ticker", "entry_session"]]
                 .join(scored.labels.set_index("event_id")[["reaction", "label_end_session"]])
                 .join(target[["self_target", "self_threshold"]]))
        checked = 0
        for _, group in frame.groupby("ticker"):
            group = group.sort_values("entry_session")
            entry = pd.to_datetime(group["entry_session"]).to_numpy("datetime64[D]")
            end = pd.to_datetime(group["label_end_session"]).to_numpy("datetime64[D]")
            reaction = group["reaction"].to_numpy(dtype=float)
            for i, threshold in enumerate(group["self_threshold"].to_numpy()):
                if not np.isfinite(threshold):
                    continue
                eligible = reaction[:i][end[:i] < entry[i]]
                eligible = eligible[np.isfinite(eligible)]
                assert threshold <= np.max(eligible), (
                    "threshold exceeds every value it could legally have used"
                )
                checked += 1
        assert checked > 0, "no thresholds were verifiable"


class TestAttentionPercentile:
    def test_it_stays_inside_the_unit_interval(self, relative):
        combined = attention_percentile(relative).dropna()
        assert ((combined >= 0) & (combined <= 1)).all()

    def test_all_missing_inputs_give_no_answer(self):
        """Zero would read as 'least unusual filing this issuer ever made',
        which is a claim. Absence is not a claim."""
        frame = pd.DataFrame({"self_novelty_pct": [np.nan],
                              "self_rel_volume_pct": [np.nan],
                              "self_doc_length_pct": [np.nan]})
        assert attention_percentile(frame).isna().all()
