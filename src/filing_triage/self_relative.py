"""Where a filing sits in its own issuer's history, using only what preceded it.

The cross-sectional ranker asks which of today's filings deserve a read. This
asks a different question that a reader of one company actually has: *is this
unusual for this company?* A biotech that moves 6% on routine news and a utility
that moves 0.4% on the same are not comparable on any absolute scale, and a
percentile against the issuer's own past is the scale that makes them so.

**Two cutoffs, not one, and the difference is the whole correctness argument.**

The obvious rule -- and the one the expansion plan states -- is that a reference
distribution may only contain filings accepted before this one. That is right for
everything computable at the moment a document lands: how novel the text is, what
hour it arrived, how rare the event type is.

It is not enough for anything derived from an *outcome*. A filing's reaction is
not knowable until its event window closes, so a reaction percentile built from
"filings accepted earlier" quietly includes filings still in flight. For an
issuer that files in clusters, that is a filing being ranked against reactions
that had not finished happening. The rule here is therefore

    knowledge-time features   prior.acceptance_time < acceptance_time
    outcome-derived features  prior.label_end_session < entry_session

and the second is strictly stronger. It is the same distinction that separates
`.rolling()` from `.rolling().shift()`, one level up.

**Percentiles are reported with the count behind them.** A percentile over four
observations is not a percentile, and the minimum-history policy exists so the
page can say `insufficient_history` rather than print a confident-looking number
computed from almost nothing.

**Robust statistics throughout.** Reaction magnitudes are heavy-tailed: one twelve-sigma
filing in an issuer's history moves a mean far more than it should move a
judgement about what is normal for that issuer. Median and MAD do not move.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Below this a percentile is arithmetic rather than evidence, and the page says so.
MIN_HISTORY = 5
LOW_CONFIDENCE_MAX = 9
MEDIUM_CONFIDENCE_MAX = 19

# MAD of a normal sample is 0.6745 sigma; the scale factor makes a robust z
# comparable to an ordinary one, so a threshold picked on one reads the same
# on the other.
MAD_TO_SIGMA = 1.4826

INSUFFICIENT = "insufficient_history"

# Columns safe to hand a model: every one is computable at the moment the
# document lands.
FEATURE_COLUMNS = (
    "self_novelty_pct", "self_doc_length_pct", "self_rel_volume_pct",
    "self_trailing_vol_pct",
    "self_novelty_z", "self_doc_length_z", "self_rel_volume_z",
    "self_trailing_vol_z",
    "self_history_depth", "self_resolved_depth",
)

# Columns describing what happened *after* the filing. They exist for the
# self-history chart, which plots earlier filings' observed reactions, and for
# analysis. They must never reach a feature matrix.
#
# This separation was not obvious enough to skip. The first version of the
# calibrated model was handed `self_reaction_pct` alongside a target defined as
# "this filing's reaction exceeded the issuer's 80th percentile" -- which is the
# same quantity thresholded, so the model scored PR-AUC 0.993 and ROC AUC 0.998.
# The reference distribution had the correct causal cutoff; the value being
# compared against it was the filing's own future. A cutoff on the wrong side of
# the comparison is still a leak.
OUTCOME_COLUMNS = ("self_reaction_pct", "self_reaction_z")
CONFIDENCE_STATES = ("insufficient_history", "low", "medium", "standard")


@dataclass(frozen=True)
class HistoryPolicy:
    """How much of an issuer's past is required before a percentile is shown.

    The thresholds are declared here rather than scattered through the callers so
    a sensitivity study has one thing to vary. They are a starting proposal, not
    a finding: `experiments.history_depth_sensitivity` measures whether the
    ranking actually behaves differently on either side of them.
    """

    minimum: int = MIN_HISTORY
    low_max: int = LOW_CONFIDENCE_MAX
    medium_max: int = MEDIUM_CONFIDENCE_MAX

    def confidence(self, depth: int) -> str:
        if depth < self.minimum:
            return INSUFFICIENT
        if depth <= self.low_max:
            return "low"
        if depth <= self.medium_max:
            return "medium"
        return "standard"


def causal_percentile(ordered: np.ndarray,
                      usable: np.ndarray | None = None) -> np.ndarray:
    """For each value, the share of the *earlier* values it exceeds.

    Takes and returns one issuer's values already sorted by time, and works
    purely in that space -- the caller maps back. An earlier version took the
    sort order and wrote through it, which silently indexed a group-sized array
    with whole-frame positions and only failed once a group did not start at
    row zero.

    `usable`, when given, is how many earlier values each row may look back at:
    fewer than all of them when the quantity is outcome-derived and some
    outcomes had not resolved yet.

    Ties count as half, the standard mid-rank convention, so a filing identical
    to its own history lands in the middle of it rather than at either edge.
    """
    out = np.full(len(ordered), np.nan)
    for position in range(len(ordered)):
        window = position if usable is None else int(usable[position])
        current = ordered[position]
        if window < 1 or not np.isfinite(current):
            continue
        prior = ordered[:window]
        prior = prior[np.isfinite(prior)]
        if not prior.size:
            continue
        below = float((prior < current).sum())
        equal = float((prior == current).sum())
        out[position] = (below + 0.5 * equal) / prior.size
    return out


def causal_robust_z(ordered: np.ndarray,
                    usable: np.ndarray | None = None) -> np.ndarray:
    """Median/MAD z-score against the issuer's earlier values.

    Robust rather than mean/sd because a single extreme reaction in an issuer's
    history would otherwise redefine what counts as normal for it -- which is
    exactly backwards, since the extreme filing is the one the scale is supposed
    to identify.
    """
    out = np.full(len(ordered), np.nan)
    for position in range(len(ordered)):
        window = position if usable is None else int(usable[position])
        current = ordered[position]
        if window < 1 or not np.isfinite(current):
            continue
        prior = ordered[:window]
        prior = prior[np.isfinite(prior)]
        if prior.size < 2:
            continue
        median = float(np.median(prior))
        mad = float(np.median(np.abs(prior - median)))
        if mad <= 0:
            # A degenerate history -- every prior value identical. A z-score is
            # undefined rather than infinite, and saying so beats inventing a
            # spread the data does not have.
            continue
        out[position] = (current - median) / (mad * MAD_TO_SIGMA)
    return out


def _resolved_counts(entry: np.ndarray, label_end: np.ndarray,
                     order: np.ndarray) -> np.ndarray:
    """How many earlier filings had their outcome window closed, per row.

    Windows close in the order filings entered, so one `searchsorted` gives every
    row its count. The comparison is strict: a label is fully observed at the
    close of its last window session, and the entry it would inform is the open
    of a later one, which leaves a whole session of slack rather than reasoning
    about intraday timing a daily panel cannot support.
    """
    ends = label_end[order]
    starts = entry[order]
    resolved = np.searchsorted(ends, starts, side="left")
    # Never look forward: a row may only count filings that are also earlier in
    # the ordering, whatever the window arithmetic says.
    return np.minimum(resolved, np.arange(len(order)))


def self_relative_frame(events: pd.DataFrame, features: pd.DataFrame,
                        labels: pd.DataFrame | None = None,
                        policy: HistoryPolicy | None = None) -> pd.DataFrame:
    """Issuer-relative percentiles, z-scores and the history behind each.

    Returns one row per event in `features`, indexed the same way, so it can be
    joined or concatenated without realigning.

    Knowledge-time columns are computed against every earlier filing of the
    issuer. The reaction column is computed only against filings whose outcome
    had resolved, and carries its own smaller depth so a reader can see that the
    two are not the same denominator.
    """
    policy = policy or HistoryPolicy()
    frame = events.set_index("event_id").reindex(features.index)
    joined = pd.DataFrame(index=features.index)
    joined["ticker"] = frame["ticker"].to_numpy()

    accepted = pd.to_datetime(frame["acceptance_time"])
    if isinstance(accepted.dtype, pd.DatetimeTZDtype):
        accepted = accepted.dt.tz_convert("UTC").dt.tz_localize(None)
    joined["accepted"] = accepted.to_numpy("datetime64[s]")

    # Knowledge-time inputs: everything a reader had when the document landed.
    sources = {
        "novelty": features.get("novelty"),
        "doc_length": features.get("log_doc_chars"),
        "rel_volume": features.get("rel_volume"),
        "trailing_vol": features.get("vol_20"),
    }
    for name, series in sources.items():
        joined[name] = (series.to_numpy(dtype=float) if series is not None
                        else np.full(len(features), np.nan))

    has_labels = labels is not None and "reaction" in getattr(labels, "columns", [])
    if has_labels:
        aligned = labels.set_index("event_id").reindex(features.index)
        joined["reaction"] = aligned["reaction"].to_numpy(dtype=float)
        joined["entry"] = pd.to_datetime(
            frame["entry_session"]).to_numpy("datetime64[D]")
        joined["label_end"] = pd.to_datetime(
            aligned["label_end_session"]).to_numpy("datetime64[D]")

    depth = np.zeros(len(joined), dtype=int)
    resolved_depth = np.zeros(len(joined), dtype=int)
    percentiles: dict[str, np.ndarray] = {
        f"self_{name}_pct": np.full(len(joined), np.nan) for name in sources
    }
    zscores = {f"self_{name}_z": np.full(len(joined), np.nan) for name in sources}
    reaction_pct = np.full(len(joined), np.nan)
    reaction_z = np.full(len(joined), np.nan)

    positions = joined.reset_index(drop=True)
    for _, index in positions.groupby("ticker", sort=False).indices.items():
        order = index[np.argsort(positions["accepted"].to_numpy()[index],
                                 kind="mergesort")]
        depth[order] = np.arange(len(order))

        for name in sources:
            ordered = positions[name].to_numpy(dtype=float)[order]
            percentiles[f"self_{name}_pct"][order] = causal_percentile(ordered)
            zscores[f"self_{name}_z"][order] = causal_robust_z(ordered)

        if has_labels:
            usable = _resolved_counts(positions["entry"].to_numpy("datetime64[D]"),
                                      positions["label_end"].to_numpy("datetime64[D]"),
                                      order)
            resolved_depth[order] = usable
            ordered = positions["reaction"].to_numpy(dtype=float)[order]
            reaction_pct[order] = causal_percentile(ordered, usable)
            reaction_z[order] = causal_robust_z(ordered, usable)

    out = pd.DataFrame(
        {**percentiles, **zscores,
         "self_reaction_pct": reaction_pct,
         "self_reaction_z": reaction_z,
         "self_history_depth": depth,
         "self_resolved_depth": resolved_depth},
        index=features.index,
    )
    out["self_confidence"] = [policy.confidence(int(d)) for d in depth]
    return out


def feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Only the columns a model may see, selected by name rather than by care.

    `self_relative_frame` returns knowledge-time and outcome-derived columns in
    one frame because a caller usually wants both -- the page plots the second
    and the model consumes the first. Handing the whole frame to an estimator is
    then one forgotten `drop` away, so the safe subset is a function rather than
    a convention.
    """
    return frame[[c for c in FEATURE_COLUMNS if c in frame.columns]]


def assert_no_outcome_features(columns) -> None:
    """Raise if anything outcome-derived reached a feature matrix.

    A guard rather than a comment, and it belongs at the point features are
    assembled: this leak does not fail, it produces a beautiful number. The one
    that got through scored 0.998 ROC AUC and looked like a triumph.
    """
    leaked = sorted(set(OUTCOME_COLUMNS) & set(columns))
    if leaked:
        raise ValueError(
            f"outcome-derived columns in the feature matrix: {leaked}. These are "
            "computed from the filing's own reaction, which is the thing being "
            "predicted."
        )


def attention_percentile(frame: pd.DataFrame,
                         columns: tuple[str, ...] = (
                             "self_novelty_pct", "self_rel_volume_pct",
                             "self_doc_length_pct")) -> pd.Series:
    """One combined number, and the reason it is a mean of percentiles.

    Averaging percentiles rather than raw values is what keeps the combination
    meaningful: the inputs are on different scales and have different tails, and
    a weighted sum of a log length and a volume ratio is arithmetic without a
    unit. Percentiles are already comparable by construction.

    Rows where every input is missing return NaN rather than zero. Zero would
    read as "least unusual filing this issuer has ever made", which is a claim,
    and absence is not a claim.
    """
    available = [c for c in columns if c in frame.columns]
    if not available:
        return pd.Series(np.nan, index=frame.index)
    return frame[available].mean(axis=1, skipna=True)


# The plan's first-release target: did this filing react more than four fifths of
# the issuer's own earlier filings? A quantile rather than a fixed sigma cutoff,
# because "unusual for this company" is the question and companies differ.
TARGET_QUANTILE = 0.80


def issuer_relative_target(events: pd.DataFrame, labels: pd.DataFrame,
                           quantile: float = TARGET_QUANTILE,
                           policy: HistoryPolicy | None = None) -> pd.DataFrame:
    """Whether a filing beat its issuer's own earlier reaction distribution.

    ``y = 1`` when ``|CAR|`` exceeds the ``quantile`` of that issuer's previously
    *resolved* reactions. Two properties make this different from the
    cross-sectional label, and both are the point:

    The threshold is per issuer, so a utility's 1.5-sigma day and a biotech's
    6-sigma day can both count as unusual for their own history. And the
    threshold moves: an issuer whose disclosures grow quieter raises its own bar,
    which is what "unusual *now*" has to mean.

    **The threshold never sees the filing it judges.** It is computed from
    strictly earlier filings whose outcome windows had already closed -- the same
    resolved-only rule the percentiles use, for the same reason. A filing
    contributing to the quantile that classifies it would be grading its own
    exam, and on this sample that would touch 8.7% of rows.

    Rows without enough resolved history get ``y = NaN`` rather than 0. Zero
    would assert the filing was ordinary, which is not what "we cannot tell"
    means, and a model trained on that assertion learns to call unknowns routine.
    """
    policy = policy or HistoryPolicy()
    frame = events.set_index("event_id")
    aligned = labels.set_index("event_id").reindex(frame.index)

    accepted = pd.to_datetime(frame["acceptance_time"])
    if isinstance(accepted.dtype, pd.DatetimeTZDtype):
        accepted = accepted.dt.tz_convert("UTC").dt.tz_localize(None)

    work = pd.DataFrame({
        "ticker": frame["ticker"].to_numpy(),
        "accepted": accepted.to_numpy("datetime64[s]"),
        "entry": pd.to_datetime(frame["entry_session"]).to_numpy("datetime64[D]"),
        "label_end": pd.to_datetime(
            aligned["label_end_session"]).to_numpy("datetime64[D]"),
        "reaction": aligned["reaction"].to_numpy(dtype=float),
    }, index=frame.index)

    target = np.full(len(work), np.nan)
    threshold = np.full(len(work), np.nan)
    depth = np.zeros(len(work), dtype=int)

    positions = work.reset_index(drop=True)
    for _, index in positions.groupby("ticker", sort=False).indices.items():
        order = index[np.argsort(positions["accepted"].to_numpy()[index],
                                 kind="mergesort")]
        usable = _resolved_counts(positions["entry"].to_numpy("datetime64[D]"),
                                  positions["label_end"].to_numpy("datetime64[D]"),
                                  order)
        ordered = positions["reaction"].to_numpy(dtype=float)[order]
        depth[order] = usable
        for position, row in enumerate(order):
            window = int(usable[position])
            if window < policy.minimum or not np.isfinite(ordered[position]):
                continue
            prior = ordered[:window]
            prior = prior[np.isfinite(prior)]
            if prior.size < policy.minimum:
                continue
            cut = float(np.quantile(prior, quantile))
            threshold[row] = cut
            target[row] = float(ordered[position] > cut)

    return pd.DataFrame({
        "self_target": target,
        "self_threshold": threshold,
        "self_target_depth": depth,
        "self_target_confidence": [policy.confidence(int(d)) for d in depth],
    }, index=frame.index)
