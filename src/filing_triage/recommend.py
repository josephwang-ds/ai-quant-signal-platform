"""Turning a calibrated probability into a reading priority.

The recommendation is about *attention*, never about money. `Read now` means a
person should open the document today; it does not mean buy, sell, hold, or that
the price will move in any direction. The label the model predicts is the
*magnitude* of a reaction, so a direction cannot be recovered from it even in
principle, and the states below are named so that no reading of them suggests
otherwise.

**Two conditions, not one.** A probability alone is a thin basis for telling
someone to drop what they are doing. The policy requires a calibrated
probability *and* at least one issuer-relative signal that a person could check
for themselves -- an unusually novel document, unusual pre-filing volume. That
second condition is what makes the card explainable: every `Read now` can name a
reason that traces to a number on the page, and a recommendation nobody can
interrogate is one nobody should follow.

**Abstention is a state, not a failure.** An issuer with four prior filings has
no defensible baseline, and the honest output is to say so and show the raw
evidence. Filling the gap with a cross-sectional percentile would answer a
different question in the same visual slot, which is worse than answering none.

**Thresholds are fitted on the past and reported on the future.** Choosing them
by looking at the period they are then evaluated on is the selection leak this
project refuses everywhere else; `select_thresholds` sees training folds only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

READ_NOW = "read_now"
MONITOR = "monitor"
ROUTINE = "routine"
INSUFFICIENT = "insufficient_history"
WITHHELD = "withheld"

STATES = (READ_NOW, MONITOR, ROUTINE, INSUFFICIENT, WITHHELD)

# Placeholders from the plan. `select_thresholds` replaces them with values
# chosen on training folds; these are what a fresh install gets before any
# selection has run.
DEFAULT_READ_NOW = 0.60
DEFAULT_MONITOR = 0.40
DEFAULT_SUPPORT_PERCENTILE = 0.80

# Signals a `Read now` may cite. All are knowledge-time: a reader could have
# checked every one of them before the market opened.
SUPPORT_COLUMNS = ("self_novelty_pct", "self_rel_volume_pct", "self_doc_length_pct")

SUPPORT_WORDS = {
    "self_novelty_pct": "more unusual language than {pct} of this issuer's earlier filings",
    "self_rel_volume_pct": "pre-filing volume above {pct} of its own history",
    "self_doc_length_pct": "longer than {pct} of its own filings",
}

# A percentile of 1.0 is "above everything", and rendering it as "more unusual
# than 100% of earlier filings" reads as a rounding artefact rather than the
# strongest statement the data supports. The top case gets its own sentence.
SUPPORT_WORDS_TOP = {
    "self_novelty_pct": "the most unusual language in this issuer's filing history",
    "self_rel_volume_pct": "the heaviest pre-filing volume in its own history",
    "self_doc_length_pct": "the longest filing this issuer has made",
}


@dataclass(frozen=True)
class Policy:
    """The rule, stated as data so it can be varied and reported."""

    read_now: float = DEFAULT_READ_NOW
    monitor: float = DEFAULT_MONITOR
    support: float = DEFAULT_SUPPORT_PERCENTILE

    def describe(self) -> str:
        return (f"read_now p>={self.read_now:.2f} with a supporting signal "
                f">={self.support:.0%}; monitor p>={self.monitor:.2f}")


def _supporting(row: pd.Series, policy: Policy) -> list[str]:
    reasons = []
    for column in SUPPORT_COLUMNS:
        value = row.get(column)
        if value is None or not np.isfinite(value) or value < policy.support:
            continue
        if value >= 1.0:
            reasons.append(SUPPORT_WORDS_TOP[column])
        else:
            reasons.append(SUPPORT_WORDS[column].format(pct=f"{value:.0%}"))
    return reasons


def recommend(probabilities: pd.Series, signals: pd.DataFrame,
              confidence: pd.Series | None = None,
              policy: Policy | None = None,
              withheld: pd.Series | None = None) -> pd.DataFrame:
    """One state and its reasons per filing.

    `withheld` lets an upstream validator veto a row -- a stale snapshot, a
    failed evidence check -- without this module needing to know what the check
    was. A veto beats every other state, including `Read now`: a recommendation
    resting on evidence that failed validation is worse than none, because the
    card around it still looks trustworthy.
    """
    policy = policy or Policy()
    index = probabilities.index
    states, reasons, supports = [], [], []

    for event_id in index:
        p = probabilities.get(event_id)
        blocked = bool(withheld.get(event_id, False)) if withheld is not None else False
        depth_state = (confidence.get(event_id) if confidence is not None else None)
        row = signals.loc[event_id] if event_id in signals.index else pd.Series(dtype=float)
        found = _supporting(row, policy)

        if blocked:
            state, why = WITHHELD, ["evidence or freshness checks did not pass"]
        elif depth_state == INSUFFICIENT or p is None or not np.isfinite(p):
            state = INSUFFICIENT
            why = ["too few earlier filings from this issuer to say what is normal"]
        elif p >= policy.read_now and found:
            state, why = READ_NOW, found
        elif p >= policy.monitor or (p >= policy.read_now and not found):
            # A high probability with nothing a reader can check is deliberately
            # demoted rather than promoted. The model may be right; the card
            # could not explain why, and an unexplainable `Read now` is the one
            # this policy exists to avoid.
            state = MONITOR
            why = found or ["elevated model probability without a confirming signal"]
        else:
            state, why = ROUTINE, ["consistent with this issuer's usual disclosures"]

        states.append(state)
        reasons.append(why)
        supports.append(len(found))

    return pd.DataFrame(
        {"state": states, "reasons": reasons, "supporting_signals": supports,
         "probability": probabilities.reindex(index)},
        index=index,
    )


def select_thresholds(probabilities: pd.Series, labels: pd.Series,
                      signals: pd.DataFrame, folds: pd.Series,
                      training_folds: tuple[int, ...] | None = None,
                      grid: tuple[float, ...] | None = None,
                      target_precision: float = 0.40) -> Policy:
    """Choose thresholds on training folds only, for a stated precision.

    The objective is the smallest threshold reaching `target_precision` on the
    training folds, not the one maximising precision: a threshold at 0.99 is
    perfectly precise and recommends nothing, and a policy that never fires has
    no product value however good its confusion matrix looks.

    Selecting on the same period the policy is then reported on would be the
    selection leak this project refuses for models and hyper-parameters. The
    caller passes fold ids; the last fold is held out unless told otherwise.
    """
    grid = grid or tuple(np.round(np.arange(0.20, 0.95, 0.05), 2))
    if training_folds is None:
        available = sorted(folds.dropna().unique())
        training_folds = tuple(available[:-1]) if len(available) > 1 else tuple(available)

    mask = folds.isin(training_folds) & labels.notna() & probabilities.notna()
    p = probabilities[mask]
    y = labels[mask]
    supported = signals.reindex(p.index)[list(SUPPORT_COLUMNS)].max(axis=1)

    best = None
    for threshold in grid:
        fires = (p >= threshold) & (supported >= DEFAULT_SUPPORT_PERCENTILE)
        if fires.sum() < 20:
            continue
        precision = float(y[fires].mean())
        if precision >= target_precision:
            best = float(threshold)
            break
    read_now = best if best is not None else DEFAULT_READ_NOW
    return Policy(read_now=read_now, monitor=min(DEFAULT_MONITOR, read_now))


def evaluate(recommendations: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    """Precision, recall and volume per state.

    Recall is against every positive in the scored population, so the states
    sum to the whole rather than each being scored on its own slice -- which
    would let an abstaining policy report perfect numbers on the three rows it
    still answered.
    """
    joined = recommendations.join(labels.rename("label"))
    positives = float(joined["label"].sum())
    rows = []
    for state in STATES:
        group = joined[joined["state"] == state]
        if group.empty:
            rows.append({"state": state, "count": 0, "share": 0.0,
                         "precision": np.nan, "recall": np.nan})
            continue
        known = group["label"].notna()
        rows.append({
            "state": state,
            "count": len(group),
            "share": len(group) / len(joined),
            "precision": float(group.loc[known, "label"].mean()) if known.any() else np.nan,
            "recall": (float(group["label"].sum()) / positives) if positives else np.nan,
        })
    return pd.DataFrame(rows)
