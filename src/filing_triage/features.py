"""Features, every one of which a reader could have computed at `decision_time`.

Four families:

  what kind of news   8-K item codes, assigned by the registrant and available
                      the instant the filing lands
  when it landed      pre-market, during the session, after the close, or on a
                      non-trading day -- release timing is a deliberate choice
                      by the issuer and it is informative
  how unusual it is   cosine distance between this document and the issuer's own
                      previous filings. A boilerplate quarterly notice scores
                      near zero; genuinely new language scores high
  the issuer's state  trailing volatility, relative volume, turnover and filing
                      cadence, all strictly through the session before entry

On the novelty score: it uses a HashingVectorizer, not TF-IDF, and that is a
leakage decision rather than a performance one. TF-IDF has to be fitted, and a
vectorizer fitted on the whole corpus carries document frequencies computed from
filings that had not been written yet. Hashing is stateless -- the same document
maps to the same vector regardless of what else is in the sample -- so the
feature is identical whether computed today or in 2019.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer

from filing_triage.config import PipelineConfig
from filing_triage.ingest.edgar import ITEM_LABELS

NOVELTY_LOOKBACK = 8      # how many of the issuer's own prior filings to compare against
HASH_FEATURES = 2 ** 16

_VECTORIZER = HashingVectorizer(
    n_features=HASH_FEATURES,
    alternate_sign=False,
    norm="l2",
    stop_words="english",
    ngram_range=(1, 2),
)

SESSION_STATES = ("pre", "open", "post", "closed")


def build_features(events: pd.DataFrame, returns: pd.DataFrame,
                   config: PipelineConfig,
                   labels: pd.DataFrame | None = None,
                   profile: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per event, indexed by `event_id`.

    `labels` is optional and is used for one family only: the issuer's own track
    record, which is built from prior labels that had already resolved. Passing
    the frame in is what makes that possible and is also the moment this becomes
    dangerous, so the rule lives in `_issuer_history_features` with its reasoning
    attached. Nothing else here may touch it.
    """
    frame = events.sort_values(["ticker", "acceptance_time"]).reset_index(drop=True)

    parts = [
        frame[["event_id"]],
        _item_features(frame),
        _timing_features(frame),
        _novelty_features(frame),
        _issuer_state_features(frame, returns, config),
        _issuer_history_features(frame, labels, config),
        _issuer_profile_features(frame, profile),
    ]
    out = pd.concat(parts, axis=1)
    return out.set_index("event_id")


# --------------------------------------------------------------------------- #
def _item_features(frame: pd.DataFrame) -> pd.DataFrame:
    """One column per 8-K item code, plus how many were cited."""
    items = frame["items"].fillna("").astype(str)
    parsed = items.apply(lambda s: {p.strip() for p in s.split(",") if p.strip()})

    cols = {f"item_{code.replace('.', '_')}": parsed.apply(lambda s, c=code: int(c in s))
            for code in ITEM_LABELS}
    cols["n_items"] = parsed.apply(len)
    return pd.DataFrame(cols, index=frame.index)


def _timing_features(frame: pd.DataFrame) -> pd.DataFrame:
    """When the issuer chose to release it."""
    acceptance = frame["acceptance_time"]
    out = pd.DataFrame(index=frame.index)
    for state in SESSION_STATES:
        out[f"released_{state}"] = (frame["session_state"] == state).astype(int)
    out["weekday"] = acceptance.dt.weekday
    out["hour_et"] = acceptance.dt.hour + acceptance.dt.minute / 60.0

    prev = frame.groupby("ticker", sort=False)["acceptance_time"].shift(1)
    out["days_since_prev_filing"] = (
        (acceptance - prev).dt.total_seconds() / 86400.0
    ).fillna(365.0).clip(upper=365.0)

    # Filing cadence over the trailing year, counted from prior filings only.
    out["filings_trailing_year"] = (
        frame.groupby("ticker", sort=False)["acceptance_time"]
        .transform(lambda s: _rolling_count_365(s))
    )
    return out


def _rolling_count_365(times: pd.Series) -> pd.Series:
    """How many of this issuer's filings fell in the 365 days before each one.

    Counts strictly prior filings: the filing itself is never in its own window.
    """
    # Via numpy datetime64[s] rather than dividing an int64: pandas resolution is
    # not fixed (2.x nanoseconds, 3.x microseconds), so a hard-coded divisor is a
    # unit bug waiting for a version bump.
    if isinstance(times.dtype, pd.DatetimeTZDtype):
        times = times.dt.tz_convert("UTC").dt.tz_localize(None)
    seconds = times.to_numpy().astype("datetime64[s]").astype("int64")
    here = np.searchsorted(seconds, seconds, side="left")
    year_ago = np.searchsorted(seconds, seconds - 365 * 86400, side="left")
    return pd.Series(here - year_ago, index=times.index)


def _novelty_features(frame: pd.DataFrame) -> pd.DataFrame:
    """How different this document is from the issuer's own recent filings."""
    text = frame.get("text")
    if text is None:
        return pd.DataFrame({"novelty": 0.5, "log_doc_chars": 0.0,
                             "doc_chars_vs_median": 0.0}, index=frame.index)

    text = text.fillna("")
    novelty = pd.Series(np.nan, index=frame.index, dtype=float)

    for _, group in frame.groupby("ticker", sort=False):
        docs = text.loc[group.index]
        matrix = _VECTORIZER.transform(docs.tolist())
        for position, idx in enumerate(group.index):
            if position == 0:
                continue      # first filing has nothing of its own to compare to
            lo = max(0, position - NOVELTY_LOOKBACK)
            prior = matrix[lo:position]
            # Rows are l2-normalised, so the dot product is cosine similarity.
            similarity = (prior @ matrix[position].T).toarray().ravel()
            novelty.loc[idx] = 1.0 - float(similarity.max()) if similarity.size else np.nan

    chars = text.str.len().astype(float)
    median = (chars.groupby(frame["ticker"])
              .transform(lambda s: s.shift(1).expanding().median()))

    return pd.DataFrame({
        # A first-ever filing is neither novel nor familiar. Use a fixed neutral
        # value rather than a full-sample median whose value includes future docs;
        # `first_filing` lets the model learn that the value was unavailable.
        "novelty": novelty.fillna(0.5),
        "first_filing": novelty.isna().astype(int),
        "log_doc_chars": np.log1p(chars),
        "doc_chars_vs_median": (chars / median).replace([np.inf, -np.inf], np.nan).fillna(1.0),
    }, index=frame.index)


def _issuer_state_features(frame: pd.DataFrame, returns: pd.DataFrame,
                           config: PipelineConfig) -> pd.DataFrame:
    """Trailing market state, joined as of the entry session.

    The `shift` below is the whole ballgame. With it, every statistic ends on the
    session before entry. Without it, the event's own session is inside its own
    features -- and a filing that moved the stock 8% arrives pre-labelled with an
    8% day in its volatility window.
    """
    panel = returns.sort_values(["ticker", "date"]).copy()
    grouped = panel.groupby("ticker", sort=False)

    def roll(series: pd.Series, window: int, fn: str) -> pd.Series:
        base = series.shift(1) if config.shift_trailing_features else series
        return getattr(base.rolling(window, min_periods=max(5, window // 4)), fn)()

    # Short windows on purpose. A 60-session window barely notices one extra day,
    # so forgetting to shift it is harmless and proves nothing; a 5-session window
    # is dominated by it. `rel_volume` is the sharpest case -- unshifted, on the
    # entry session, it is the reaction's own volume spike divided by its baseline,
    # which is the label wearing a moustache. It is also a completely ordinary
    # feature to want, which is why this bug is so easy to ship.
    panel["vol_20"] = grouped["ret"].transform(lambda s: roll(s, 20, "std"))
    panel["abs_ret_5"] = grouped["ret"].transform(lambda s: roll(s.abs(), 5, "mean"))
    dollar_volume = panel["close"] * panel["volume"]
    panel["log_dollar_volume"] = np.log1p(
        dollar_volume.groupby(panel["ticker"], sort=False).transform(
            lambda series: roll(series, 20, "mean")
        )
    )

    # Grouped shift, not a bare one: a plain .shift(1) would carry the last row
    # of each ticker into the first row of the next.
    volume = (grouped["volume"].shift(1) if config.shift_trailing_features
              else panel["volume"])
    panel["rel_volume"] = volume / panel["volume_median_60"]

    keys = ["ticker", "date", "vol_20", "abs_ret_5", "log_dollar_volume", "rel_volume"]
    joined = frame[["ticker", "entry_session"]].merge(
        panel[keys], left_on=["ticker", "entry_session"], right_on=["ticker", "date"],
        how="left")

    out = joined[["vol_20", "abs_ret_5", "log_dollar_volume", "rel_volume"]].copy()
    out.index = frame.index
    # HistGradientBoosting handles NaN natively. Preserving missingness avoids a
    # full-sample median whose value would carry future market observations into
    # an earlier test fold.
    return out


def _issuer_profile_features(frame: pd.DataFrame,
                             profile: pd.DataFrame | None) -> pd.DataFrame:
    """Static issuer attributes, and the two that were dropped for cause.

    `filer_category` is gone because on this universe it has **zero variance**:
    all 194 issuers are large accelerated filers. That is the convenience sample
    confessing again -- hand-picked large caps are all in one size bucket -- and
    a constant column is a feature that cannot inform anything while still
    costing a line of explanation.

    `sic_division` is kept at *one* digit, not two. Two digits give 40 groups
    over 193 issuers, about five companies each, and a categorical that thin is
    much closer to an issuer identifier than to an industry: the same issuers
    appear in training and test folds, so a level holding five companies lets a
    tree memorise which ones they are and recover their base rate directly.
    One digit gives around ten groups and asks the intended question.

    `days_to_fiscal_year_end` is the attribute worth having. It is genuinely
    point-in-time -- a fiscal calendar is published in advance and changes almost
    never -- and it says where in the reporting cycle a filing sits, which is
    exactly the kind of thing that separates a routine quarterly release from an
    unscheduled one.
    """
    # No profile table at all is a different fact from an issuer whose attributes
    # EDGAR does not report, and the two must not share an encoding. NaN means
    # "missing for this issuer" and the model may learn from it; a run with no
    # profile source -- the synthetic path -- has nothing to learn, so it gets a
    # constant sentinel. An all-NaN column would also make the imputer warn once
    # per fold about a statistic it cannot compute.
    if profile is None or profile.empty:
        return pd.DataFrame({"sic_group": -1, "days_to_fiscal_year_end": -1.0},
                            index=frame.index)

    joined = frame[["cik", "acceptance_time"]].merge(
        profile[["cik", "sic_division", "fiscal_year_end"]], on="cik", how="left")
    joined.index = frame.index

    group = (joined["sic_division"].fillna(-1).astype(int) // 10).astype(int)

    # MMDD, and the leading zero is load-bearing: a September year-end is "0926"
    # and survives a CSV round trip as the integer 926, which slices to month 92.
    # Re-pad rather than trusting whatever dtype the frame arrived with.
    stamp = (joined["fiscal_year_end"].fillna("").astype(str)
             .str.replace(r"\.0$", "", regex=True).str.zfill(4))
    month = pd.to_numeric(stamp.str[:2], errors="coerce")
    day = pd.to_numeric(stamp.str[2:], errors="coerce")
    accepted = joined["acceptance_time"].dt.tz_localize(None)
    # Day of the fiscal year the filing lands on, as a signed distance to the
    # next year-end. Wrapped rather than clipped so an issuer filing just after
    # its year-end is near the far edge, not at an arbitrary boundary value.
    year_end_doy = (month - 1) * 30.4 + day
    filing_doy = accepted.dt.dayofyear
    distance = (year_end_doy - filing_doy) % 365.0

    return pd.DataFrame({
        "sic_group": group,
        # An issuer EDGAR has no fiscal calendar for keeps NaN: that is genuinely
        # unknown, and the estimator is entitled to treat it as such.
        "days_to_fiscal_year_end": distance.astype(float),
    }, index=frame.index)


def _issuer_history_features(frame: pd.DataFrame, labels: pd.DataFrame,
                             config: PipelineConfig) -> pd.DataFrame:
    """The issuer's own track record, counting only filings already resolved.

    Built from *past labels*, which makes it the most dangerous family of
    features in this project. A filing's label is not knowable until its outcome
    window closes, so at filing N's decision time the only usable history is the
    prior filings of that issuer whose windows closed first.

    `expanding()` over every earlier row is the obvious implementation and it is
    wrong: for an issuer that files in clusters, a filing would be told the
    answer by siblings whose reactions had not finished happening. That is
    `.rolling()` without `.shift()` moved one level up -- not the event's own
    outcome, but the outcomes beside it.

    The cutoff is `label_end_session < entry_session`. Conservative on purpose:
    a label is fully observed at the close of its last window session, and the
    entry it would inform is the *open* of a later one, so the strict inequality
    leaves a whole session of slack rather than reasoning about intraday timing
    the daily panel cannot support.

    Two features, not three, and the third was removed by its own measurement.
    A median of prior reaction magnitudes ranked 38th of 41 on out-of-sample
    permutation importance with a negative mean -- redundant with the rate, which
    ranks 6th. Keeping a feature that measures as noise costs a column of
    explanation for nothing.

    The count stays despite also measuring near zero, and the reason is the
    project's own: a rate over two observations is not a rate, and quoting one
    without its denominator is the same error as quoting a point estimate
    without its interval. Filling an unknown rate with the sample mean instead
    would carry the whole corpus into every issuer that had no history yet.
    """
    columns = ["issuer_prior_resolved", "issuer_prior_material_rate"]
    if labels is None or "label_end_session" not in labels.columns:
        return pd.DataFrame(
            {"issuer_prior_resolved": 0, "issuer_prior_material_rate": np.nan},
            index=frame.index)

    joined = frame[["event_id", "ticker", "entry_session"]].merge(
        labels[["event_id", "label", "label_end_session"]],
        on="event_id", how="left")
    joined.index = frame.index

    resolved = np.zeros(len(joined), dtype=int)
    rate = np.full(len(joined), np.nan)

    entry = pd.to_datetime(joined["entry_session"]).to_numpy("datetime64[D]")
    end = pd.to_datetime(joined["label_end_session"]).to_numpy("datetime64[D]")
    label = joined["label"].to_numpy(dtype=float)

    for _, positions in joined.groupby("ticker", sort=False).indices.items():
        order = positions[np.argsort(entry[positions], kind="mergesort")]
        ends = end[order]
        # Windows close in the order the filings entered, so one pass of
        # searchsorted gives every row its count of already-resolved priors.
        cutoff = (np.searchsorted(ends, entry[order], side="left")
                  if config.resolved_issuer_history
                  else np.arange(len(order)))
        for position, (row, n) in enumerate(zip(order, cutoff, strict=True)):
            usable = order[:min(n, position)]
            resolved[row] = len(usable)
            if len(usable):
                rate[row] = float(np.nanmean(label[usable]))

    return pd.DataFrame(dict(zip(columns, (resolved, rate), strict=True)),
                        index=frame.index)


def feature_columns(features: pd.DataFrame) -> list[str]:
    return [c for c in features.columns if features[c].dtype != object]
