"""Leakage guards.

Lookahead bias does not announce itself. It shows up as a model that works
suspiciously well, and by then the bug is buried three joins deep. So the rule
here is that leakage is checked *mechanically*, on every run, and a violation is
an exception -- not a code review comment.

Every check answers one question: could this number have been computed by someone
standing at `decision_time` with only the information available to them?

    audit = LeakageAudit()
    audit.causal(events, fact="acceptance_time", decision="decision_time")
    audit.timezone_aware(events)
    audit.universe_pit(events, membership)
    audit.raise_if_failed()

The audit object is also the data behind the report's leakage panel, so the same
checks that gate CI are the ones the reader sees.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import numpy as np
import pandas as pd


class LeakageError(AssertionError):
    """Raised when a dataset lets a model see something it could not have known."""


@dataclass
class CheckResult:
    name: str
    passed: bool
    n_rows: int
    n_violations: int
    detail: str
    sample: pd.DataFrame | None = None

    @property
    def rate(self) -> float:
        return self.n_violations / self.n_rows if self.n_rows else 0.0


@dataclass
class LeakageAudit:
    """Accumulates checks so one run reports every problem, not just the first."""

    results: list[CheckResult] = field(default_factory=list)
    strict: bool = True

    # -- individual checks ------------------------------------------------- #
    def causal(self, frame: pd.DataFrame, *, fact: str, decision: str,
               label: str | None = None, holds: str | None = None) -> CheckResult:
        """No fact may postdate the moment it is used.

        `holds` overrides the pass message. The same check guards two quite
        different claims -- that a feature predates its decision, and that an
        entry price postdates the news -- and a report reads badly when both
        report the generic one.
        """
        bad = frame[frame[fact] > frame[decision]]
        return self._record(CheckResult(
            name=label or f"causal: {fact} <= {decision}",
            passed=bad.empty,
            n_rows=len(frame),
            n_violations=len(bad),
            detail=(
                (holds or "every fact predates the decision that uses it")
                if bad.empty else
                f"{len(bad)} rows use a fact recorded up to "
                f"{(bad[fact] - bad[decision]).max()} after the decision"
            ),
            sample=bad[[fact, decision]].head(5) if not bad.empty else None,
        ))

    def timezone_aware(self, frame: pd.DataFrame) -> CheckResult:
        """A naive timestamp is a timestamp whose meaning depends on who reads it."""
        naive = [
            c for c in frame.columns
            if pd.api.types.is_datetime64_any_dtype(frame[c])
            and getattr(frame[c].dtype, "tz", None) is None
        ]
        return self._record(CheckResult(
            name="timestamps carry a timezone",
            passed=not naive,
            n_rows=len(frame.columns),
            n_violations=len(naive),
            detail=("all datetime columns are tz-aware" if not naive
                    else f"naive datetime columns: {', '.join(naive)}"),
        ))

    def universe_pit(self, events: pd.DataFrame, membership: pd.DataFrame, *,
                     ticker: str = "ticker", when: str = "event_date") -> CheckResult:
        """Survivorship bias: the universe must be as it was, not as it is.

        Screening on today's index constituents quietly deletes every company that
        went bankrupt, got acquired, or fell out of the index -- and those are
        exactly the ones whose disclosures moved most.
        """
        m = membership.set_index(ticker)
        joined = events.join(m[["start_date", "end_date"]], on=ticker, how="left")
        d = pd.to_datetime(joined[when]).dt.tz_localize(None).dt.normalize()
        start = pd.to_datetime(joined["start_date"])
        end = pd.to_datetime(joined["end_date"]).fillna(pd.Timestamp.max.normalize())
        bad = joined[joined["start_date"].isna() | (d < start) | (d > end)]
        return self._record(CheckResult(
            name="universe membership is point-in-time",
            passed=bad.empty,
            n_rows=len(events),
            n_violations=len(bad),
            detail=("every event's issuer was in the index on that date" if bad.empty
                    else f"{len(bad)} events reference an issuer outside the index "
                         "on the event date (survivorship bias)"),
            sample=bad[[ticker, when]].head(5) if not bad.empty else None,
        ))

    def purged_split(self, *, train_end: pd.Series, test_start: pd.Series,
                     embargo: timedelta) -> CheckResult:
        """Purged CV: a training label whose outcome window runs into the test
        period leaks the test period's returns backwards into training."""
        latest_train = train_end.max()
        earliest_test = test_start.min()
        gap = earliest_test - latest_train
        ok = gap >= embargo
        return self._record(CheckResult(
            name="train/test split is purged and embargoed",
            passed=bool(ok),
            n_rows=len(train_end) + len(test_start),
            n_violations=0 if ok else 1,
            detail=(f"gap between last training label and first test event is {gap}, "
                    f"at or beyond the {embargo} embargo") if ok else
                   (f"only {gap} separates the last training label from the first "
                    f"test event; {embargo} required"),
        ))

    def unique_events(self, frame: pd.DataFrame, keys: list[str]) -> CheckResult:
        """Duplicated events double-count and inflate significance."""
        dup = frame.duplicated(subset=keys, keep=False)
        return self._record(CheckResult(
            name=f"events unique on {'+'.join(keys)}",
            passed=not dup.any(),
            n_rows=len(frame),
            n_violations=int(dup.sum()),
            detail=("no duplicate events" if not dup.any()
                    else f"{int(dup.sum())} rows share an event key"),
            sample=frame.loc[dup, keys].head(5) if dup.any() else None,
        ))

    def estimation_window_gap(self, frame: pd.DataFrame, *, est_end: str,
                              event_date: str, min_gap_sessions: int = 1) -> CheckResult:
        """The window used to estimate a stock's normal behaviour must end before
        the event, with a gap -- otherwise the event contaminates its own baseline."""
        gap = (pd.to_datetime(frame[event_date]) - pd.to_datetime(frame[est_end])).dt.days
        bad = frame[gap < min_gap_sessions]
        return self._record(CheckResult(
            name="estimation window ends before the event",
            passed=bad.empty,
            n_rows=len(frame),
            n_violations=len(bad),
            detail=("baselines are estimated on pre-event data only" if bad.empty
                    else f"{len(bad)} events overlap their own estimation window"),
        ))

    def feature_matrix(self, features: pd.DataFrame, *,
                       allow: list[str] | None = None) -> CheckResult:
        """Catches the mundane failure: a column that is literally the answer.

        Anything derived from the outcome window must not reach the model.
        """
        banned = ("car", "abn", "future", "fwd", "forward", "ret_next",
                  "label", "target", "reaction", "outcome")
        allow = set(allow or [])
        hits = [c for c in features.columns
                if c not in allow and any(b in c.lower() for b in banned)]
        return self._record(CheckResult(
            name="no outcome-derived columns in the feature matrix",
            passed=not hits,
            n_rows=len(features.columns),
            n_violations=len(hits),
            detail=("feature matrix is free of outcome-derived columns" if not hits
                    else f"outcome-derived columns present: {', '.join(hits)}"),
        ))

    # -- reporting --------------------------------------------------------- #
    def _record(self, result: CheckResult) -> CheckResult:
        self.results.append(result)
        return result

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def raise_if_failed(self) -> None:
        if self.passed:
            return
        lines = [f"  [{r.name}] {r.detail}" for r in self.failures]
        raise LeakageError(
            f"{len(self.failures)} of {len(self.results)} leakage checks failed:\n"
            + "\n".join(lines)
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"check": r.name, "status": "pass" if r.passed else "FAIL",
             "violations": r.n_violations, "checked": r.n_rows, "detail": r.detail}
            for r in self.results
        ])

    def summary(self) -> str:
        n_pass = sum(r.passed for r in self.results)
        head = f"{n_pass}/{len(self.results)} leakage checks passed"
        return head if self.passed else head + "  <-- BLOCKING"


# --------------------------------------------------------------------------- #
# Purged, embargoed walk-forward CV
# --------------------------------------------------------------------------- #
class PurgedWalkForward:
    """Expanding-window CV that purges and embargoes around each test fold.

    Plain KFold on financial events leaks twice over: it trains on the future, and
    because each label spans a multi-day outcome window, training labels whose
    windows overlap the test period carry the test period's returns with them.

    This drops (purges) any training event whose outcome window reaches into the
    test fold, then holds back a further `embargo` so that serial correlation
    across the boundary cannot carry information either.
    """

    def __init__(self, n_splits: int = 5, embargo: timedelta = timedelta(days=5)):
        self.n_splits = n_splits
        self.embargo = embargo

    def split(self, event_time: pd.Series, label_end_time: pd.Series):
        order = np.argsort(event_time.values)
        t_event = event_time.values[order]
        t_label_end = label_end_time.values[order]
        n = len(order)
        fold_size = n // (self.n_splits + 1)
        if fold_size == 0:
            raise ValueError(f"{n} events cannot be split into {self.n_splits} folds")
        emb = np.timedelta64(self.embargo)

        for k in range(1, self.n_splits + 1):
            test_lo = k * fold_size
            test_hi = n if k == self.n_splits else (k + 1) * fold_size
            test_pos = np.arange(test_lo, test_hi)
            test_start = t_event[test_lo]

            # Purge: a training event may only stay if its entire outcome window
            # closed before the test fold opened, with the embargo on top.
            candidate = np.arange(0, test_lo)
            keep = t_label_end[candidate] + emb <= test_start
            train_pos = candidate[keep]
            if len(train_pos) == 0:
                continue
            yield order[train_pos], order[test_pos]
