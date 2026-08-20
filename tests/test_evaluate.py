"""Ranking metrics, and the conditions under which they mean nothing.

The daily queue metric is the one that can quietly stop measuring the model. When
a session carries no more filings than the queue length, the top k is every
filing, the ranking cannot change the answer, and the figure becomes a property
of the calendar. These tests pin that it is excluded rather than averaged in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage.evaluate import (
    evaluate, lift_at_k, mean_daily_precision_at_k, ndcg_at_k, precision_at_k,
    queue_sizes, recall_at_k,
)


def _frame(sessions: list[int], labels: list[int], scores: list[float]):
    predictions = pd.DataFrame({"label": labels, "score": scores})
    return predictions, pd.Series(sessions, index=predictions.index)


class TestPooledMetrics:
    @pytest.fixture
    def sample(self):
        rng = np.random.default_rng(3)
        labels = (rng.random(1000) < 0.1).astype(int)
        return labels, labels + rng.random(1000) * 0.01

    def test_perfect_ranking(self, sample):
        labels, scores = sample
        assert precision_at_k(labels, scores, 10) == 1.0
        assert ndcg_at_k(labels, scores, 10) == 1.0

    def test_random_ranking_lands_near_the_base_rate(self, sample):
        labels, _ = sample
        rng = np.random.default_rng(4)
        assert lift_at_k(labels, rng.random(1000), 100) == pytest.approx(1.0, abs=0.6)

    def test_recall_at_k_never_exceeds_one(self, sample):
        labels, scores = sample
        assert recall_at_k(labels, scores, 10_000) == 1.0


class TestDailyQueueMetric:
    def test_thin_sessions_are_excluded(self):
        """Three filings cannot fill a queue of five, so that day tests nothing."""
        predictions, sessions = _frame(
            sessions=[0, 0, 0], labels=[0, 1, 0], scores=[0.1, 0.9, 0.2])
        precision, counted, available = mean_daily_precision_at_k(
            predictions, sessions, k=5)
        assert counted == 0
        assert available == 1
        assert np.isnan(precision)

    def test_a_single_material_filing_does_not_score_one(self):
        """The worst case for the unrestricted metric: one filing, it mattered,
        precision 1.0 -- and the model had no say in it."""
        predictions, sessions = _frame([0], [1], [0.5])
        precision, counted, _ = mean_daily_precision_at_k(predictions, sessions, k=5)
        assert counted == 0
        assert np.isnan(precision)

    def test_crowded_sessions_are_counted(self):
        predictions, sessions = _frame(
            sessions=[0] * 10, labels=[1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            scores=[0.9, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        precision, counted, available = mean_daily_precision_at_k(
            predictions, sessions, k=5)
        assert (counted, available) == (1, 1)
        assert precision == pytest.approx(0.4)      # 2 of the top 5

    def test_ranking_changes_the_result_on_crowded_sessions(self):
        """The property the exclusion exists to preserve."""
        labels = [1, 1, 0, 0, 0, 0, 0, 0]
        good = [0.9, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        bad = [0.1, 0.1, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        first, *_ = mean_daily_precision_at_k(*_frame([0] * 8, labels, good), k=5)
        second, *_ = mean_daily_precision_at_k(*_frame([0] * 8, labels, bad), k=5)
        assert first > second

    def test_usability_flag_is_false_for_a_thin_universe(self):
        """A universe of forty issuers files about twice a session; the queue
        metric cannot be computed from that and must not be reported."""
        rng = np.random.default_rng(5)
        rows = []
        for session in range(300):
            for _ in range(int(rng.integers(1, 4))):
                rows.append({"session": session,
                             "label": int(rng.random() < 0.1),
                             "score": rng.random()})
        frame = pd.DataFrame(rows)
        metrics = evaluate(frame[["label", "score"]], sessions=frame["session"])
        assert metrics["daily_usable_at_5"] is False
        assert metrics["filings_per_session_median"] <= 3


class TestQueueSizes:
    def test_reports_the_shape_of_the_daily_queue(self):
        predictions, sessions = _frame([0, 0, 0, 1, 2, 2], [0] * 6, [0.5] * 6)
        sizes = queue_sizes(predictions, sessions)
        assert sizes["sessions"] == 3
        assert sizes["filings_per_session_max"] == 3
