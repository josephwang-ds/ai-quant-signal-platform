"""Tests for the guards themselves.

A guard that cannot fail is decoration, so every check here is exercised in both
directions: it passes clean data, and it catches the specific bug it exists for.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from filing_triage.guards import LeakageAudit, LeakageError, PurgedWalkForward


@pytest.fixture
def clean_events():
    times = pd.date_range("2023-01-02", periods=200, freq="B", tz="America/New_York")
    return pd.DataFrame({
        "cik": np.arange(200) % 20,
        "accession": [f"acc-{i}" for i in range(200)],
        "ticker": [f"T{i % 20:02d}" for i in range(200)],
        "acceptance_time": times,
        "decision_time": times + pd.Timedelta("15min"),
        "event_date": times.date,
    })


@pytest.fixture
def membership():
    return pd.DataFrame({
        "ticker": [f"T{i:02d}" for i in range(20)],
        "start_date": [pd.Timestamp("2020-01-01").date()] * 20,
        "end_date": [None] * 20,
    })


class TestCausal:
    def test_passes_when_facts_precede_decisions(self, clean_events):
        audit = LeakageAudit()
        audit.causal(clean_events, fact="acceptance_time", decision="decision_time")
        assert audit.passed

    def test_catches_a_decision_made_before_the_fact(self, clean_events):
        events = clean_events.copy()
        events.loc[events.index[:4], "decision_time"] -= pd.Timedelta("6h")
        audit = LeakageAudit()
        result = audit.causal(events, fact="acceptance_time", decision="decision_time")
        assert not result.passed
        assert result.n_violations == 4
        with pytest.raises(LeakageError, match="causal"):
            audit.raise_if_failed()


class TestTimezone:
    def test_catches_naive_timestamps(self, clean_events):
        events = clean_events.copy()
        events["acceptance_time"] = events["acceptance_time"].dt.tz_localize(None)
        audit = LeakageAudit()
        assert not audit.timezone_aware(events).passed


class TestUniversePIT:
    def test_catches_an_issuer_that_had_left_the_index(self, clean_events, membership):
        left = membership.copy()
        left.loc[left["ticker"] == "T05", "end_date"] = pd.Timestamp("2023-02-01").date()
        audit = LeakageAudit()
        result = audit.universe_pit(clean_events, left)
        assert not result.passed
        assert result.n_violations > 0

    def test_catches_an_issuer_that_had_not_yet_joined(self, clean_events, membership):
        late = membership.copy()
        late.loc[late["ticker"] == "T07", "start_date"] = pd.Timestamp("2023-06-01").date()
        audit = LeakageAudit()
        assert not audit.universe_pit(clean_events, late).passed

    def test_passes_a_stable_index(self, clean_events, membership):
        audit = LeakageAudit()
        assert audit.universe_pit(clean_events, membership).passed


class TestFeatureMatrix:
    def test_catches_an_outcome_column(self):
        features = pd.DataFrame({"novelty": [0.1], "car_2d": [0.05]})
        audit = LeakageAudit()
        result = audit.feature_matrix(features)
        assert not result.passed
        assert "car_2d" in result.detail

    def test_allows_an_explicit_exemption(self):
        features = pd.DataFrame({"novelty": [0.1], "carrier_count": [3]})
        audit = LeakageAudit()
        assert audit.feature_matrix(features, allow=["carrier_count"]).passed


class TestUniqueEvents:
    def test_catches_duplicates(self, clean_events):
        doubled = pd.concat([clean_events, clean_events.head(3)])
        audit = LeakageAudit()
        result = audit.unique_events(doubled, ["cik", "accession"])
        assert not result.passed
        assert result.n_violations == 6      # both copies of each duplicate


class TestPurgedWalkForward:
    @pytest.fixture
    def times(self):
        event = pd.Series(pd.date_range("2022-01-03", periods=1000, freq="B", tz="UTC"))
        return event, event + pd.Timedelta("2D")

    def test_training_always_precedes_testing(self, times):
        event, label_end = times
        for train, test in PurgedWalkForward(5, timedelta(days=5)).split(event, label_end):
            assert event.iloc[train].max() < event.iloc[test].min()

    def test_label_windows_never_reach_into_the_test_fold(self, times):
        event, label_end = times
        embargo = timedelta(days=5)
        for train, test in PurgedWalkForward(5, embargo).split(event, label_end):
            gap = event.iloc[test].min() - label_end.iloc[train].max()
            assert gap >= embargo

    def test_purging_actually_removes_something(self, times):
        """With a long outcome window, the purge must bite -- otherwise the split
        is just an ordinary walk-forward wearing a different name."""
        event, _ = times
        long_labels = event + pd.Timedelta("30D")
        short = list(PurgedWalkForward(5, timedelta(0)).split(event, event))
        long = list(PurgedWalkForward(5, timedelta(0)).split(event, long_labels))
        assert sum(len(t) for t, _ in long) < sum(len(t) for t, _ in short)

    def test_folds_partition_the_tail(self, times):
        event, label_end = times
        seen = np.concatenate([test for _, test in
                               PurgedWalkForward(5, timedelta(days=5)).split(event, label_end)])
        assert len(seen) == len(np.unique(seen))     # no event tested twice

    def test_rejects_a_sample_too_small_to_split(self):
        tiny = pd.Series(pd.date_range("2022-01-03", periods=3, freq="B", tz="UTC"))
        with pytest.raises(ValueError, match="cannot be split"):
            list(PurgedWalkForward(5, timedelta(days=5)).split(tiny, tiny))


class TestAuditReporting:
    def test_summary_flags_failure(self, clean_events):
        events = clean_events.copy()
        events.loc[events.index[0], "decision_time"] -= pd.Timedelta("1h")
        audit = LeakageAudit()
        audit.causal(events, fact="acceptance_time", decision="decision_time")
        assert "BLOCKING" in audit.summary()

    def test_frame_has_one_row_per_check(self, clean_events, membership):
        audit = LeakageAudit()
        audit.causal(clean_events, fact="acceptance_time", decision="decision_time")
        audit.timezone_aware(clean_events)
        audit.universe_pit(clean_events, membership)
        assert len(audit.to_frame()) == 3
        assert set(audit.to_frame()["status"]) == {"pass"}
