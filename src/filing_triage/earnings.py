"""When an issuer is next expected to report, inferred from its own filings.

Two consumers read this: the features, which need it point-in-time, and the
calendar page, which needs it forward-looking. One implementation, because the
day they disagree is the day the page stops describing the model's inputs.

**Nothing here reads a published earnings calendar, and that is deliberate.** A
vendor calendar is the better source for a *display* -- it carries announced
dates rather than estimates. It is the wrong source for a *feature*, because the
calendar you download today lists dates as they are known today, not as they were
known then, and it does not record when each date was announced. Using it in a
backtest would let a 2022 filing know a date that was published weeks later, and
no guard in this project could catch it: there is no column to check.

So the estimate is built from the issuer's own history, which is knowable by
construction.

**The predictor is last year's corresponding quarter plus 365 days**, not the
median gap since the last report. Issuers report on close to the same calendar
week each year, and measuring both on 3,257 out-of-sample predictions says so:
a median absolute error of 1 day against 4, and 60% within three days against
48%. Quarter-to-quarter gaps drift with the calendar; the annual anchor does not.

It remains an estimate. About a quarter of predictions miss by more than a week,
so the page states a window and the confidence behind it rather than printing a
date as though it were announced.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Item 2.02 is "Results of Operations and Financial Condition" -- the earnings
# release. Matched on the whole code so 2.02 is not found inside 12.02.
EARNINGS_ITEM = r"(?:^|,)\s*2\.02(?:,|$)"
YEAR_DAYS = 365
QUARTERS_PER_YEAR = 4
MIN_HISTORY = 2


def is_earnings_filing(items: pd.Series) -> pd.Series:
    return items.fillna("").astype(str).str.contains(EARNINGS_ITEM, regex=True)


def earnings_dates(events: pd.DataFrame) -> pd.DataFrame:
    """One row per earnings filing: ticker and the session it was accepted on."""
    frame = events[is_earnings_filing(events["items"])].copy()
    if frame.empty:
        return pd.DataFrame(columns=["ticker", "date"])
    accepted = pd.to_datetime(frame["acceptance_time"])
    if isinstance(accepted.dtype, pd.DatetimeTZDtype):
        accepted = accepted.dt.tz_convert("America/New_York").dt.tz_localize(None)
    frame["date"] = accepted.dt.normalize()
    return frame[["ticker", "date"]].sort_values(["ticker", "date"])


def _predict(history: np.ndarray) -> np.datetime64 | None:
    """The next expected date from a sorted array of prior earnings dates.

    Annual anchor first, quarterly cadence as the fallback for an issuer that has
    not yet filed a full year -- which is the only case where the worse predictor
    is the available one.
    """
    if len(history) >= QUARTERS_PER_YEAR:
        return history[-QUARTERS_PER_YEAR] + np.timedelta64(YEAR_DAYS, "D")
    if len(history) >= MIN_HISTORY:
        gaps = np.diff(history).astype("timedelta64[D]").astype(int)
        return history[-1] + np.timedelta64(int(np.median(gaps)), "D")
    return None


def expected_next_report(events: pd.DataFrame,
                         as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """The next expected earnings filing per issuer, for the calendar page.

    `days_of_history` is reported beside every estimate because it decides how
    much the estimate is worth: an issuer with three prior reports is being
    predicted by the weaker of the two methods, and saying so is cheaper than
    having a reader discover it from a miss.
    """
    columns = ["ticker", "last_report", "expected", "days_until",
               "prior_reports", "method"]
    dates = earnings_dates(events)
    if dates.empty:
        return pd.DataFrame(columns=columns)
    as_of = pd.Timestamp(as_of or pd.Timestamp.today().normalize()).normalize()

    rows = []
    for ticker, group in dates.groupby("ticker", sort=True):
        history = group["date"].to_numpy("datetime64[D]")
        history = history[history <= np.datetime64(as_of.date(), "D")]
        predicted = _predict(history)
        if predicted is None:
            continue
        # Roll forward whole quarters when the estimate has already passed --
        # which happens when a report is late, or when the panel simply ends
        # before today. Better than showing a date in the past and calling it
        # "next".
        while predicted < np.datetime64(as_of.date(), "D"):
            predicted = predicted + np.timedelta64(YEAR_DAYS // QUARTERS_PER_YEAR, "D")
        rows.append({
            "ticker": ticker,
            "last_report": pd.Timestamp(history[-1]),
            "expected": pd.Timestamp(predicted),
            "days_until": int((predicted - np.datetime64(as_of.date(), "D")).astype(int)),
            "prior_reports": len(history),
            "method": ("annual anchor" if len(history) >= QUARTERS_PER_YEAR
                       else "quarterly cadence"),
        })
    if not rows:
        # Every issuer had too little history. An empty frame still has to carry
        # its columns: the caller sorts and filters on them, and an untyped empty
        # frame fails there instead of here, with a KeyError that says nothing.
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).sort_values(["expected", "ticker"]).reset_index(drop=True)


def earnings_rhythm_features(events: pd.DataFrame) -> pd.DataFrame:
    """Where each filing sits in its issuer's reporting cycle, point-in-time.

    For every filing, both columns are computed from that issuer's earnings
    filings *strictly before* it. A filing never informs its own features, and
    the expectation is the one that would have been made standing at that filing
    rather than the one hindsight supports.

    `days_to_expected_earnings` can be negative: the expected date has passed and
    the report has not arrived. That is a real state and worth keeping distinct
    from "not due yet", so it is not clipped.
    """
    frame = events[["event_id", "ticker", "acceptance_time"]].copy()
    accepted = pd.to_datetime(frame["acceptance_time"])
    if isinstance(accepted.dtype, pd.DatetimeTZDtype):
        accepted = accepted.dt.tz_convert("America/New_York").dt.tz_localize(None)
    frame["when"] = accepted.dt.normalize()

    reports = earnings_dates(events)
    by_ticker = {t: g["date"].to_numpy("datetime64[D]")
                 for t, g in reports.groupby("ticker", sort=False)}

    since = np.full(len(frame), np.nan)
    until = np.full(len(frame), np.nan)
    when = frame["when"].to_numpy("datetime64[D]")

    for position, (ticker, moment) in enumerate(zip(frame["ticker"], when, strict=True)):
        history = by_ticker.get(ticker)
        if history is None:
            continue
        prior = history[history < moment]
        if not len(prior):
            continue
        since[position] = float((moment - prior[-1]).astype(int))
        predicted = _predict(prior)
        if predicted is not None:
            until[position] = float((predicted - moment).astype(int))

    return pd.DataFrame({
        "days_since_last_earnings": since,
        "days_to_expected_earnings": until,
    }, index=events.index)
