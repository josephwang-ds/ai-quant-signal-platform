"""Point-in-time index membership.

The interesting case is the one a naive join gets wrong: an issuer with more than
one membership interval. Companies get dropped from an index and added back years
later, and the S&P 500 has a steady trickle of them, so this is not a corner case
that only shows up in a fixture -- it is a crash waiting on the first real pull.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from filing_triage.ingest.universe import (
    load_membership, members_asof, membership_mask, restrict_to_membership,
)


@pytest.fixture
def rejoiner() -> pd.DataFrame:
    """XYZ was dropped in mid-2021 and re-added in 2023. ABC never left."""
    return pd.DataFrame([
        {"ticker": "XYZ", "start_date": date(2015, 1, 1), "end_date": date(2021, 6, 30)},
        {"ticker": "XYZ", "start_date": date(2023, 3, 1), "end_date": None},
        {"ticker": "ABC", "start_date": date(2015, 1, 1), "end_date": None},
    ])


@pytest.fixture
def events() -> pd.DataFrame:
    return pd.DataFrame({
        "ticker": ["XYZ", "XYZ", "XYZ", "ABC", "NOPE"],
        "event_date": [date(2020, 5, 1),    # first spell
                       date(2022, 5, 1),    # the gap
                       date(2024, 5, 1),    # second spell
                       date(2024, 5, 1),    # never left
                       date(2024, 5, 1)],   # not in the index at all
    })


class TestMultipleIntervals:
    def test_mask_length_matches_the_events(self, events, rejoiner):
        """A join on ticker returns one row per interval, and the mask it produces
        no longer lines up with the frame it filters."""
        mask = membership_mask(events, rejoiner)
        assert len(mask) == len(events)

    def test_event_in_the_gap_is_dropped(self, events, rejoiner):
        assert list(membership_mask(events, rejoiner)) == [True, False, True, True, False]

    def test_restrict_keeps_exactly_those(self, events, rejoiner):
        kept = restrict_to_membership(events, rejoiner)
        assert len(kept) == 3
        assert list(kept["event_date"]) == [date(2020, 5, 1), date(2024, 5, 1),
                                            date(2024, 5, 1)]

    def test_unknown_ticker_is_excluded_not_crashed_on(self, events, rejoiner):
        assert not membership_mask(events, rejoiner)[-1]


class TestBoundaries:
    def test_interval_ends_are_inclusive(self, rejoiner):
        edges = pd.DataFrame({"ticker": ["XYZ", "XYZ"],
                              "event_date": [date(2015, 1, 1), date(2021, 6, 30)]})
        assert list(membership_mask(edges, rejoiner)) == [True, True]

    def test_day_outside_each_edge_is_excluded(self, rejoiner):
        edges = pd.DataFrame({"ticker": ["XYZ", "XYZ"],
                              "event_date": [date(2014, 12, 31), date(2021, 7, 1)]})
        assert list(membership_mask(edges, rejoiner)) == [False, False]

    def test_open_ended_membership_extends_forward(self, rejoiner):
        far = pd.DataFrame({"ticker": ["ABC"], "event_date": [date(2099, 1, 1)]})
        assert membership_mask(far, rejoiner)[0]


class TestStringDates:
    """Membership read straight off a CSV carries strings, not dates."""

    def test_string_dates_are_coerced(self, events):
        as_strings = pd.DataFrame([
            {"ticker": "ABC", "start_date": "2015-01-01", "end_date": ""},
        ])
        one = pd.DataFrame({"ticker": ["ABC"], "event_date": [date(2024, 5, 1)]})
        assert membership_mask(one, as_strings)[0]

    def test_load_membership_round_trips(self, tmp_path, rejoiner):
        path = tmp_path / "m.csv"
        rejoiner.assign(cik=[1, 1, 2], name="x").to_csv(path, index=False)
        loaded = load_membership(path)
        assert loaded["start_date"].map(lambda v: isinstance(v, date)).all()
        assert pd.isna(loaded.loc[loaded["ticker"] == "ABC", "end_date"].iloc[0])


class TestMembersAsof:
    def test_counts_the_index_as_it_stood(self, rejoiner):
        assert set(members_asof(rejoiner, date(2020, 1, 1))["ticker"]) == {"XYZ", "ABC"}
        assert set(members_asof(rejoiner, date(2022, 1, 1))["ticker"]) == {"ABC"}
        assert set(members_asof(rejoiner, date(2024, 1, 1))["ticker"]) == {"XYZ", "ABC"}
