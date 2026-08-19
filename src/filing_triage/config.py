"""One config object, and four switches that decide whether the answer is real.

Each switch below is a bug that this project deliberately keeps implementable, so
that `experiments/leakage.py` can turn them on one at a time and measure what
each is worth. All four True is the honest pipeline; that is the default, and CI
asserts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class PipelineConfig:
    # -- measurement design ------------------------------------------------ #
    embargo: timedelta = timedelta(0)
    """Delay between the filing becoming public and being allowed to act.
    Sweeping this is how we measure how fast the reaction is over."""

    event_window_sessions: int = 2
    """Sessions the reaction is measured over, starting at the entry session."""

    estimation_sessions: int = 120
    """Length of the pre-event window used to learn the issuer's normal behaviour."""

    estimation_gap_sessions: int = 20
    """Sessions left between the estimation window and the event, so that
    pre-announcement drift does not contaminate the baseline."""

    label_quantile: float = 0.90
    """A filing is 'worth reading' if its reaction lands in this top slice."""

    # -- correctness switches (True = correct) ----------------------------- #
    shift_trailing_features: bool = True
    """Trailing statistics must exclude the event day. A `.rolling(60)` that
    forgets `.shift(1)` puts the event's own volatility into its features --
    which is the answer, spelled slightly differently."""

    pit_entry: bool = True
    """Enter at the first open after the acceptance time, not on the filing date.
    ~80% of 8-Ks land outside market hours; the naive version buys before the
    news exists."""

    pit_universe: bool = True
    """Resolve index membership as of the event date, not as of today."""

    purged_cv: bool = True
    """Purged, embargoed walk-forward instead of shuffled K-fold."""

    @property
    def is_honest(self) -> bool:
        return all([self.shift_trailing_features, self.pit_entry,
                    self.pit_universe, self.purged_cv])

    def describe_switches(self) -> str:
        flags = {
            "trailing features shifted": self.shift_trailing_features,
            "point-in-time entry": self.pit_entry,
            "point-in-time universe": self.pit_universe,
            "purged CV": self.purged_cv,
        }
        return ", ".join(f"{k}={'yes' if v else 'NO'}" for k, v in flags.items())
