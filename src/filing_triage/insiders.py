"""Which insider trades are decisions, and when the market could know about them.

Two questions, and the project's usual discipline applied to both.

**Which trades are decisions.** Most insider selling is a calendar: shares vest,
a pre-adopted plan sells a fixed number every quarter, tax is withheld. Cohen,
Malloy and Pomorski (2012) separated insiders into *routine* ones -- who trade in
the same calendar month year after year -- and *opportunistic* ones, and found the
predictability sits entirely with the second group. `causal_routine` implements
that classification, with one change their paper did not need: it is computed
point-in-time, from each insider's earlier trades only, because a label built
from an insider's whole history would know in 2022 what they did in 2025.

That classification is *inferred*. Since 2023 the filer must also *disclose*
whether a trade ran under a Rule 10b5-1 plan, which is the same idea stated
outright. Both are carried, so the inferred label can be scored against the
disclosed one on filings that have both -- a check on a well-known method against
ground truth that did not exist when it was published.

**When the market could know.** A Form 4 has two timestamps and the gap between
them is a filing-length window in which the insider has traded and nobody else
can see it. `disclosure_gap` measures that window, and the reason it matters is
the same reason the 8-K leakage ladder exists: anchoring the study at the
transaction date is easy, natural, and hindsight.

**Abstention, again.** Classifying an insider as routine needs three prior years
of their trading. An insider without that history gets `unknown` rather than a
guess, for the same reason an issuer with four prior filings gets
`insufficient_history` in the disclosure model: filling the gap with a default
answers a different question in the same slot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# How many prior years an insider must have traded in the same calendar month
# before they count as trading on a schedule. Three is Cohen, Malloy and
# Pomorski's threshold and is kept rather than tuned: a threshold chosen to make
# a result come out is not a threshold.
ROUTINE_YEARS = 3

ROUTINE = "routine"
OPPORTUNISTIC = "opportunistic"
UNKNOWN = "unknown"

# One row per filing, which is the unit the market reacts to. A filing reporting
# four sales is one disclosure, not four.
EVENT_COLUMNS = (
    "event_id", "ticker", "acceptance_time", "first_transaction_date",
    "last_transaction_date", "disclosure_gap_days", "trades", "net_value",
    "gross_value", "direction", "any_plan_10b5_1", "all_plan_10b5_1",
    "owners", "any_officer", "any_director", "any_ten_percent_owner",
    "behaviour",
)


def causal_routine(transactions: pd.DataFrame, *, years: int = ROUTINE_YEARS
                   ) -> pd.Series:
    """Label each trade routine, opportunistic, or unknown, from earlier trades only.

    An insider is trading on a schedule if, in each of the `years` calendar years
    before this one, they also traded in this calendar month. Every trade that
    check looks at is strictly earlier, so the label is available at the moment
    the trade is disclosed.

    `unknown` is returned rather than `opportunistic` when the insider's record
    does not go back far enough. The distinction matters: "we have no evidence
    this person trades on a schedule" and "we have three years showing they do
    not" are different claims, and only the second is a finding.
    """
    if transactions.empty:
        return pd.Series(dtype="object", index=transactions.index)

    frame = transactions[["owner_cik", "transaction_date"]].copy()
    dates = pd.to_datetime(frame["transaction_date"], errors="coerce")
    frame["year"] = dates.dt.year
    frame["month"] = dates.dt.month

    labels = pd.Series(UNKNOWN, index=transactions.index, dtype="object")
    for owner, group in frame.groupby("owner_cik", sort=False):
        if not owner or group["year"].isna().all():
            continue
        # The set of (year, month) pairs this insider has ever traded in. Only
        # pairs from strictly earlier years are ever consulted below, so no
        # future trade can reach a past label.
        traded = set(zip(group["year"], group["month"], strict=True))
        first_year = int(group["year"].min())
        for index, row in group.iterrows():
            if pd.isna(row["year"]):
                continue
            year, month = int(row["year"]), int(row["month"])
            if year - first_year < years:
                continue          # not enough of their history has happened yet
            prior = [(year - back, month) for back in range(1, years + 1)]
            labels.at[index] = (ROUTINE if all(p in traded for p in prior)
                                else OPPORTUNISTIC)
    return labels


def disclosure_gap(transactions: pd.DataFrame) -> pd.Series:
    """Calendar days between the trade and the moment anyone else could know.

    The SEC allows two business days. The distribution of this column is the
    measurement: it is the length of the window in which a study anchored at the
    transaction date is reading the future.
    """
    accepted = pd.to_datetime(transactions["acceptance_time"], utc=True)
    accepted = accepted.dt.tz_convert("America/New_York").dt.tz_localize(None)
    traded = pd.to_datetime(transactions["transaction_date"], errors="coerce")
    return (accepted.dt.normalize() - traded).dt.days


def to_events(transactions: pd.DataFrame, *, years: int = ROUTINE_YEARS
              ) -> pd.DataFrame:
    """One row per filing: what was disclosed, by whom, and how stale it already was.

    Only open-market purchases and sales reach this function's arithmetic. A
    filing whose every row is compensation machinery produces no event, because
    nothing was decided in it.

    `net_value` is signed -- purchases positive -- and `gross_value` is not, so a
    filing reporting a large buy and a large sell on the same day is visibly
    different from one reporting nothing.
    """
    from filing_triage.ingest.ownership import open_market, signed_value

    trades = open_market(transactions).copy()
    if trades.empty:
        return pd.DataFrame(columns=list(EVENT_COLUMNS))

    trades["value"] = signed_value(trades)
    trades["behaviour"] = causal_routine(trades, years=years)
    trades["gap"] = disclosure_gap(trades)
    traded_on = pd.to_datetime(trades["transaction_date"], errors="coerce")

    rows = []
    for accession, group in trades.groupby("accession", sort=False):
        net = float(group["value"].sum(skipna=True))
        dates = traded_on.loc[group.index]
        rows.append({
            "event_id": accession,
            "ticker": group["ticker"].iloc[0],
            "acceptance_time": group["acceptance_time"].iloc[0],
            "first_transaction_date": dates.min(),
            "last_transaction_date": dates.max(),
            # From the earliest trade in the filing: the whole window during
            # which some part of this disclosure was already true and unseen.
            "disclosure_gap_days": float(group["gap"].max()),
            "trades": len(group),
            "net_value": net,
            "gross_value": float(group["value"].abs().sum(skipna=True)),
            "direction": "buy" if net > 0 else ("sell" if net < 0 else "flat"),
            "any_plan_10b5_1": bool(group["plan_10b5_1"].any()),
            "all_plan_10b5_1": bool(group["plan_10b5_1"].all()),
            "owners": group["owner_cik"].nunique(),
            "any_officer": bool(group["is_officer"].any()),
            "any_director": bool(group["is_director"].any()),
            "any_ten_percent_owner": bool(group["is_ten_percent_owner"].any()),
            # A filing is opportunistic if any of its trades is: one unscheduled
            # decision inside a filing is what makes the filing informative, and
            # averaging it away with the scheduled ones would hide it.
            "behaviour": (OPPORTUNISTIC if (group["behaviour"] == OPPORTUNISTIC).any()
                          else (ROUTINE if (group["behaviour"] == ROUTINE).any()
                                else UNKNOWN)),
        })
    return pd.DataFrame(rows, columns=list(EVENT_COLUMNS))


def classification_agreement(transactions: pd.DataFrame) -> pd.DataFrame:
    """Does the inferred schedule label recover the disclosed 10b5-1 flag?

    Cohen, Malloy and Pomorski had to infer which insiders traded on a schedule;
    since 2023 the filer states it. Scoring the inference against the statement
    is a check on a well-known method against ground truth that did not exist
    when it was published -- and it is free, because both columns are already
    here.

    Restricted to trades carrying a disclosed flag, and the count is reported
    beside the rates so a reader can see how much of the sample supports it.
    """
    trades = transactions.dropna(subset=["plan_10b5_1"])
    if trades.empty or "behaviour" not in trades.columns:
        return pd.DataFrame()
    rows = []
    for behaviour in (ROUTINE, OPPORTUNISTIC, UNKNOWN):
        group = trades[trades["behaviour"] == behaviour]
        if group.empty:
            continue
        rows.append({
            "behaviour": behaviour,
            "trades": len(group),
            "share_of_sample": len(group) / len(trades),
            "disclosed_under_a_plan": float(group["plan_10b5_1"].mean()),
        })
    return pd.DataFrame(rows)


def gap_profile(events: pd.DataFrame) -> pd.DataFrame:
    """The disclosure window, as a distribution rather than an average.

    A mean would hide the shape: most filings arrive on the deadline, and the
    tail is where a transaction-date-anchored study reads the most future.
    """
    if events.empty:
        return pd.DataFrame()
    gap = events["disclosure_gap_days"].dropna()
    if gap.empty:
        return pd.DataFrame()
    quantiles = [0.5, 0.75, 0.9, 0.99, 1.0]
    return pd.DataFrame({
        "statistic": ["filings", "mean"] + [f"p{int(q * 100)}" for q in quantiles],
        "calendar_days": ([float(len(gap)), float(gap.mean())]
                          + [float(np.quantile(gap, q)) for q in quantiles]),
    })
