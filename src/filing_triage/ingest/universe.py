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

import numpy as np
import pandas as pd

COLUMNS = ["ticker", "cik", "name", "start_date", "end_date"]


def load_membership(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"membership file {path} is missing columns: {sorted(missing)}")
    frame["start_date"] = pd.to_datetime(frame["start_date"]).dt.date
    frame["end_date"] = pd.to_datetime(frame["end_date"], errors="coerce").dt.date
    # Nullable: an issuer that has left the index often resolves to no CIK, and
    # the interval is still worth recording even though its filings cannot be
    # fetched. See scripts/build_universe.py.
    frame["cik"] = pd.to_numeric(frame["cik"], errors="coerce").astype("Int64")
    return frame[COLUMNS]


def normalise_intervals(membership: pd.DataFrame) -> pd.DataFrame:
    """Coerce the interval columns to dates, whatever the caller handed us.

    A membership frame read straight off a CSV carries its dates as strings, and
    comparing those to a date raises a TypeError three frames deep that names
    dtypes rather than the mistake. `load_membership` does this conversion, but
    the frame does not always arrive through it, so the functions that depend on
    the types enforce them.
    """
    out = membership.copy()
    for column in ("start_date", "end_date"):
        if column in out.columns and not out[column].map(
                lambda v: isinstance(v, date) or pd.isna(v)).all():
            out[column] = pd.to_datetime(out[column], errors="coerce").dt.date
    return out


def membership_mask(events: pd.DataFrame, membership: pd.DataFrame, *,
                    ticker: str = "ticker", when: str = "event_date") -> np.ndarray:
    """Per-event: was this issuer in the index on that date?

    One issuer may hold several intervals -- companies get dropped from an index
    and added back years later, and the S&P 500 has a steady trickle of them. So
    this cannot be a join on ticker: that multiplies every event of a re-added
    issuer by its number of intervals, and the resulting mask no longer lines up
    with the frame it is meant to filter. Match against all intervals, then
    collapse with `any`.
    """
    left = pd.DataFrame({
        "_row": np.arange(len(events)),
        ticker: events[ticker].to_numpy(),
        "_when": pd.to_datetime(events[when].to_numpy()),
    })
    intervals = normalise_intervals(membership)[[ticker, "start_date", "end_date"]]
    merged = left.merge(intervals, on=ticker, how="left")

    start = pd.to_datetime(merged["start_date"])
    end = pd.to_datetime(merged["end_date"]).fillna(pd.Timestamp.max)
    inside = start.notna() & (merged["_when"] >= start) & (merged["_when"] <= end)

    return (inside.groupby(merged["_row"]).any()
            .reindex(range(len(events)), fill_value=False).to_numpy())


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
    return events[membership_mask(events, membership, ticker=ticker, when=when)].copy()
