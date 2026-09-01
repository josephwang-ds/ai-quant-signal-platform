"""The reading policy, and the four ways it must refuse to overclaim.

`Read now` is a claim on someone's attention, not on their money. The label
underneath predicts reaction *magnitude*, so no direction can be recovered from
it even in principle, and every state name and every reason string is checked
here against that boundary.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage import recommend
from filing_triage.recommend import (
    INSUFFICIENT,
    MONITOR,
    READ_NOW,
    ROUTINE,
    STATES,
    WITHHELD,
    Policy,
)


def _signals(novelty=0.95, volume=0.10, length=0.10, index=("e0",)):
    return pd.DataFrame(
        {"self_novelty_pct": [novelty] * len(index),
         "self_rel_volume_pct": [volume] * len(index),
         "self_doc_length_pct": [length] * len(index)},
        index=list(index))


class TestTheStatesRespectTheBoundary:
    def test_no_state_names_a_trade(self):
        forbidden = ("buy", "sell", "hold", "long", "short", "target", "price")
        for state in STATES:
            assert not any(word in state for word in forbidden)

    def test_no_reason_string_implies_direction(self):
        """Every phrase the card can print, checked once. A reason that says
        "expect a rise" would turn a magnitude model into a direction call."""
        phrases = list(recommend.SUPPORT_WORDS.values()) + list(
            recommend.SUPPORT_WORDS_TOP.values())
        forbidden = ("rise", "fall", "up", "down", "gain", "loss", "buy", "sell",
                     "outperform", "return")
        for phrase in phrases:
            words = phrase.replace("-", " ").lower().split()
            assert not set(words) & set(forbidden), phrase


class TestReadNowNeedsTwoThings:
    def test_probability_alone_is_only_monitor(self):
        """A high probability with nothing a reader can check is demoted, not
        promoted. An unexplainable `Read now` is the one this policy exists to
        avoid."""
        out = recommend.recommend(
            pd.Series([0.99], index=["e0"]),
            _signals(novelty=0.10),
            policy=Policy(read_now=0.60, monitor=0.40))
        assert out.loc["e0", "state"] == MONITOR

    def test_a_supporting_signal_alone_is_not_enough(self):
        out = recommend.recommend(
            pd.Series([0.05], index=["e0"]), _signals(novelty=0.99),
            policy=Policy(read_now=0.60, monitor=0.40))
        assert out.loc["e0", "state"] == ROUTINE

    def test_both_together_fire(self):
        out = recommend.recommend(
            pd.Series([0.85], index=["e0"]), _signals(novelty=0.99),
            policy=Policy(read_now=0.60, monitor=0.40))
        assert out.loc["e0", "state"] == READ_NOW
        assert out.loc["e0", "reasons"]

    def test_every_read_now_carries_a_reason(self):
        rng = np.random.default_rng(3)
        index = [f"e{i}" for i in range(200)]
        signals = pd.DataFrame(
            {"self_novelty_pct": rng.uniform(size=200),
             "self_rel_volume_pct": rng.uniform(size=200),
             "self_doc_length_pct": rng.uniform(size=200)}, index=index)
        out = recommend.recommend(pd.Series(rng.uniform(size=200), index=index), signals)
        fired = out[out["state"] == READ_NOW]
        assert fired["reasons"].map(len).gt(0).all()


class TestAbstentionAndVeto:
    def test_shallow_history_abstains_rather_than_guessing(self):
        out = recommend.recommend(
            pd.Series([0.99], index=["e0"]), _signals(novelty=0.99),
            confidence=pd.Series([INSUFFICIENT], index=["e0"]))
        assert out.loc["e0", "state"] == INSUFFICIENT

    def test_a_veto_outranks_every_other_state(self):
        """A recommendation resting on evidence that failed validation is worse
        than none: the card around it still looks trustworthy."""
        out = recommend.recommend(
            pd.Series([0.99], index=["e0"]), _signals(novelty=0.99),
            withheld=pd.Series([True], index=["e0"]))
        assert out.loc["e0", "state"] == WITHHELD

    def test_a_missing_probability_abstains(self):
        out = recommend.recommend(pd.Series([np.nan], index=["e0"]), _signals())
        assert out.loc["e0", "state"] == INSUFFICIENT


class TestThresholdSelection:
    def test_thresholds_are_chosen_without_the_last_fold(self):
        """Selecting on the period the policy is then reported on is the
        selection leak this project refuses everywhere else."""
        rng = np.random.default_rng(11)
        n = 900
        index = [f"e{i}" for i in range(n)]
        p = pd.Series(rng.uniform(size=n), index=index)
        folds = pd.Series(np.repeat(np.arange(3), n // 3), index=index)
        # The final fold is pure noise; a leaking selector would be dragged by it.
        y = pd.Series(np.where(folds == 2, rng.integers(0, 2, n),
                               (p > 0.6).astype(int)), index=index, dtype=float)
        signals = pd.DataFrame(
            {"self_novelty_pct": np.ones(n), "self_rel_volume_pct": np.ones(n),
             "self_doc_length_pct": np.ones(n)}, index=index)
        policy = recommend.select_thresholds(p, y, signals, folds)
        assert 0.15 <= policy.read_now <= 0.95

    def test_it_prefers_the_smallest_threshold_that_works(self):
        """A threshold at 0.99 is perfectly precise and recommends nothing. A
        policy that never fires has no product value."""
        n = 600
        index = [f"e{i}" for i in range(n)]
        p = pd.Series(np.linspace(0.0, 1.0, n), index=index)
        y = pd.Series((p > 0.30).astype(float).to_numpy(), index=index)
        folds = pd.Series(np.repeat([0, 1], n // 2), index=index)
        signals = pd.DataFrame(
            {"self_novelty_pct": np.ones(n), "self_rel_volume_pct": np.ones(n),
             "self_doc_length_pct": np.ones(n)}, index=index)
        policy = recommend.select_thresholds(p, y, signals, folds,
                                             target_precision=0.50)
        assert policy.read_now <= 0.60


class TestEvaluation:
    def test_every_state_appears_even_when_empty(self):
        """A missing row reads as a state that cannot happen; a zero says it
        did not happen this time."""
        out = recommend.recommend(pd.Series([0.1], index=["e0"]), _signals())
        table = recommend.evaluate(out, pd.Series([0.0], index=["e0"]))
        assert list(table["state"]) == list(STATES)

    def test_recall_is_measured_against_all_positives(self):
        """Not against each state's own slice, which would let an abstaining
        policy report perfect numbers on the three rows it still answered."""
        index = ["a", "b", "c", "d"]
        out = recommend.recommend(
            pd.Series([0.9, 0.9, 0.1, 0.1], index=index),
            _signals(novelty=0.99, index=index),
            policy=Policy(read_now=0.6, monitor=0.4))
        table = recommend.evaluate(
            out, pd.Series([1.0, 0.0, 1.0, 1.0], index=index)).set_index("state")
        assert table.loc[READ_NOW, "recall"] == pytest.approx(1 / 3)
