"""End-to-end regressions.

These are the tests that matter. The unit tests say each part behaves; these say
the assembled pipeline does not leak, and that it would notice if it started to.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.pit import CALENDAR


@pytest.fixture(scope="module")
def honest(world):
    return pipeline.run(world.events, world.prices, world.membership,
                        PipelineConfig(), compute_importance=False)


class TestHonestPipeline:
    def test_every_guard_passes(self, honest):
        assert honest.audit.passed, honest.audit.summary()

    def test_default_config_is_the_honest_one(self):
        """The correct pipeline must be what you get for free. A safe default that
        has to be opted into is not a safe default."""
        assert PipelineConfig().is_honest

    def test_no_entry_precedes_its_filing(self, honest):
        """The invariant. Every entry open must postdate the acceptance time."""
        assert honest.integrity["impossible_entries"] == 0

        events = honest.events
        opens = events["entry_session"].map(
            lambda d: CALENDAR.open_at(d).astimezone(events["acceptance_time"].dt.tz))
        assert (opens > events["acceptance_time"]).all()

    def test_features_carry_no_outcome_columns(self, honest):
        banned = ("car", "reaction", "label", "abnormal", "volume_surprise")
        assert not [c for c in honest.features.columns
                    if any(b in c.lower() for b in banned)]

    def test_predictions_are_out_of_sample(self, honest):
        """Every scored event was held out by the fold that scored it."""
        assert (honest.predictions["fold"] >= 0).all()
        assert len(honest.predictions) <= len(honest.features)

    def test_ranks_better_than_chance(self, honest):
        assert honest.metrics["roc_auc"] > 0.55

    def test_does_not_rank_suspiciously_well(self, honest):
        """A tripwire, not a target. On features knowable before the event, an AUC
        near 0.95 does not mean the model got good -- it means something leaked."""
        assert honest.metrics["roc_auc"] < 0.90

    def test_label_rate_matches_the_configured_quantile(self, honest):
        assert honest.metrics["base_rate"] == pytest.approx(0.10, abs=0.03)


class TestLeaksAreDetected:
    """Each bug is switched on and must be caught -- by a guard where a guard
    exists, and by an inflated metric where the damage is statistical."""

    def test_naive_entry_is_caught_by_the_guard(self, world):
        result = pipeline.run(world.events, world.prices, world.membership,
                              replace(PipelineConfig(), pit_entry=False),
                              compute_importance=False)
        assert not result.audit.passed
        assert result.integrity["impossible_entries"] > 0
        assert result.integrity["impossible_share"] > 0.5      # most 8-Ks are after hours

    def test_stale_universe_is_caught_by_the_guard(self, world):
        result = pipeline.run(world.events, world.prices, world.membership,
                              replace(PipelineConfig(), pit_universe=False),
                              compute_importance=False)
        failures = [f.name for f in result.audit.failures]
        assert any("universe" in name for name in failures)

    def test_unshifted_features_inflate_the_metric(self, world):
        """The quiet one. No guard catches it, because a trailing window that
        includes the event day is structurally indistinguishable from one that
        does not -- only the score gives it away."""
        honest = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False)
        leaky = pipeline.run(world.events, world.prices, world.membership,
                             replace(PipelineConfig(), shift_trailing_features=False),
                             compute_importance=False)
        # Average precision, not AUC. The leak concentrates on the positives, so
        # AUC barely stirs (~0.04) while average precision inflates by more than
        # half -- which is the metric anyone would actually quote for a queue.
        assert leaky.metrics["average_precision"] > honest.metrics["average_precision"] * 1.3
        assert leaky.metrics["roc_auc"] > honest.metrics["roc_auc"]

    def test_shuffled_cv_inflates_the_metric(self, world):
        honest = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False)
        leaky = pipeline.run(world.events, world.prices, world.membership,
                             replace(PipelineConfig(), purged_cv=False),
                             compute_importance=False)
        assert leaky.metrics["roc_auc"] >= honest.metrics["roc_auc"]


class TestEmbargo:
    def test_embargo_delays_entry(self, world):
        prompt = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False)
        delayed = pipeline.run(world.events, world.prices, world.membership,
                               replace(PipelineConfig(), embargo=timedelta(days=2)),
                               compute_importance=False)
        # Align on event_id: the two runs keep different events, because a longer
        # embargo pushes some entries past the end of the price panel.
        a = prompt.events.set_index("event_id")["entry_session"]
        b = delayed.events.set_index("event_id")["entry_session"]
        common = a.index.intersection(b.index)
        assert len(common) > 0
        assert (b.loc[common] >= a.loc[common]).all()

    def test_embargo_keeps_the_pipeline_honest(self, world):
        result = pipeline.run(world.events, world.prices, world.membership,
                              replace(PipelineConfig(), embargo=timedelta(hours=6)),
                              compute_importance=False)
        assert result.audit.passed
