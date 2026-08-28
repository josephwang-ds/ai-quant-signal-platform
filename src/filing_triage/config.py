"""One config object, and four switches that decide whether the answer is real.

Each switch below is a bug that this project deliberately keeps implementable, so
that `experiments/leakage.py` can turn them on one at a time and measure what
each is worth. All four True is the honest pipeline; that is the default, and CI
asserts it. `open_anchored_returns` below is a fifth switch but not a fifth
bug -- see its docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class PipelineConfig:
    # -- measurement design ------------------------------------------------ #
    embargo: timedelta = timedelta(0)
    """Delay between EDGAR acceptance and being allowed to act.
    Sweeping this is how we measure how fast the reaction is over."""

    event_window_sessions: int = 2
    """Sessions the reaction is measured over, starting at the entry session."""

    estimation_sessions: int = 120
    """Length of the pre-event window used to learn the issuer's normal behaviour."""

    estimation_gap_sessions: int = 20
    """Sessions left between the estimation window and the event, so that
    pre-announcement drift does not contaminate the baseline."""

    reaction_threshold: float = 2.0
    """A filing is 'worth reading' if its absolute abnormal reaction is at least
    this many issuer-specific residual standard deviations. This cutoff is fixed
    before any fold is observed; a full-sample quantile would let future outcomes
    define the meaning of a test-fold label."""

    # -- correctness switches (True = correct) ----------------------------- #
    shift_trailing_features: bool = True
    """Trailing statistics must exclude the event day. A `.rolling(60)` that
    forgets `.shift(1)` puts the event's own volatility into its features --
    which is the answer, spelled slightly differently."""

    pit_entry: bool = True
    """Enter at the first open after the acceptance time, not on the filing date.
    The naive filing-date version can use an opening print that predates the
    accepted timestamp."""

    pit_universe: bool = True
    """Resolve index membership as of the event date, not as of today."""

    purged_cv: bool = True
    """Purged, embargoed walk-forward instead of shuffled K-fold."""

    resolved_issuer_history: bool = True
    """Count only the issuer's filings whose labels had already resolved.

    The issuer-history features are built from *past labels*, which is the most
    dangerous kind of feature here and the reason this switch exists beside the
    four canonical bugs rather than being assumed.

    A filing's label is not known until its outcome window closes. So at the
    decision time for filing N, the only prior filings of that issuer whose
    materiality is knowable are the ones whose window closed first. The obvious
    implementation -- `expanding()` over every earlier row -- silently includes
    filings still in flight, and for an issuer that files in clusters that is a
    filing being told the answer by its own neighbours. It is the same shape as
    `.rolling()` without `.shift()`, one level up: not the event's own outcome,
    but its immediate siblings'.

    Off, the features expand over every prior filing regardless of resolution,
    which is what the leak looks like and what `experiments` measures.
    """

    # -- estimator family (not a correctness switch) ----------------------- #
    estimator: str = "random_forest"
    """Which model family fits the ranker. Names come from `candidates`.

    Changed from `hist_gbdt` on 2026-08-27, and the reason it changed matters
    more than which one won. It was **not** chosen by reading the out-of-sample
    table and keeping the top row -- that is the selection leak the project
    refuses everywhere else, and it stays a leak when the thing selected is a
    model rather than a threshold. It was chosen by
    `selection.nested_selection_score`, which picks a winner inside each outer
    training block using a purged split of that block alone, so no test fold ever
    informs the choice made for it. That procedure selected this family in all
    five folds, and the score quoted for it is the procedure's, not the winner's.

    The margin is small and the paired difference straddles zero, so the honest
    reading is not that this family is better but that the families are
    indistinguishable and this is what the leak-free procedure returned. Family
    is worth 0.027 in average precision; the validation scheme is worth 0.220.
    """

    # -- measurement basis (not a correctness switch) ---------------------- #
    open_anchored_returns: bool = False
    """Measure the entry session from its OPEN rather than the previous close.

    Off by default, and that default is a deliberate answer to a real question
    rather than an oversight.

    A close-to-close series anchors the entry session's return at the *previous*
    close, which for an after-hours filing was printed before the filing
    existed. So the measured reaction contains the overnight gap in which the
    news was priced -- and `causal(acceptance_time <= entry_open)` passes on
    every row anyway, because the label never touches `entry_open`. That looked
    like a fifth leak, and `experiments.anchoring_study` was written to price it.

    It is not one. The label answers *was this filing material*, and the standard
    market-model event study answers that close-to-close: the overnight gap is
    part of the reaction, not contamination of it. Switching the label to an open
    anchor does not remove hindsight, it changes the question to *how much of the
    reaction was still on the table at the open* -- a harder and different one.
    On the synthetic corpus that collapses the label: three quarters of the move
    is already in the opening print, so the base rate falls from 18% to 2% and
    the association with the ground-truth item all but disappears.

    Both numbers are worth having, which is why the switch stays. What it must
    not do is silently redefine the product's label, so it does not participate
    in `is_honest` and it is not a rung on the leakage ladder."""

    @property
    def is_honest(self) -> bool:
        return all([self.shift_trailing_features, self.pit_entry,
                    self.pit_universe, self.purged_cv,
                    self.resolved_issuer_history])

    def describe_switches(self) -> str:
        flags = {
            "trailing features shifted": self.shift_trailing_features,
            "point-in-time entry": self.pit_entry,
            "point-in-time universe": self.pit_universe,
            "purged CV": self.purged_cv,
            "resolved-only issuer history": self.resolved_issuer_history,
            "open-anchored returns": self.open_anchored_returns,
        }
        switches = ", ".join(f"{k}={'yes' if v else 'NO'}" for k, v in flags.items())
        return f"{switches}, estimator={self.estimator}"
