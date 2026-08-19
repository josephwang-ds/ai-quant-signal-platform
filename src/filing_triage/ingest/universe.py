"""Point-in-time index membership.

The universe is a survivorship trap. Screening on today's S&P 500 deletes every
company that was dropped after a collapse, an acquisition, or a delisting -- and
those issuers are precisely the ones whose 8-Ks moved the most. A model trained
on the survivors learns that disclosures rarely matter.

Membership is therefore stored as intervals, not a list:

    ticker, cik, name, start_date, end_date      (end_date empty = still a member)

and every lookup is an as-of query. `guards.universe_pit` enforces it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

COLUMNS = ["ticker", "cik", "name", "start_date", "end_date"]


def load_membership(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"membership file {path} is missing columns: {sorted(missing)}")
    frame["start_date"] = pd.to_datetime(frame["start_date"]).dt.date
    frame["end_date"] = pd.to_datetime(frame["end_date"], errors="coerce").dt.date
    frame["cik"] = frame["cik"].astype("int64")
    return frame[COLUMNS]


def members_asof(membership: pd.DataFrame, when: date) -> pd.DataFrame:
    """Constituents as the index actually stood on `when`."""
    started = membership["start_date"] <= when
    not_ended = membership["end_date"].isna() | (membership["end_date"] >= when)
    return membership[started & not_ended]


def restrict_to_membership(events: pd.DataFrame, membership: pd.DataFrame, *,
                           ticker: str = "ticker", when: str = "event_date") -> pd.DataFrame:
    """Drop events from issuers that were not in the index at the time.

    Returns only the rows that survive, so the caller can compare counts and see
    how much of the sample survivorship bias would have quietly handed them.
    """
    m = membership.set_index(ticker)[["start_date", "end_date"]]
    joined = events.join(m, on=ticker, how="left")
    when_col = pd.to_datetime(joined[when]).dt.date
    ok = (
        joined["start_date"].notna()
        & (when_col >= joined["start_date"])
        & (joined["end_date"].isna() | (when_col <= joined["end_date"]))
    )
    return events[ok.values].copy()
