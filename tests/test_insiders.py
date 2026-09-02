"""Classifying insider trades, and keeping the classification honest.

The routine/opportunistic split is the whole reason this data source is
interesting, and it is built from an insider's trading history -- which makes it
the obvious place for the future to leak into the past. A label computed from
someone's complete record knows in 2022 what they did in 2025.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage.insiders import (
    OPPORTUNISTIC,
    ROUTINE,
    UNKNOWN,
    causal_routine,
    classification_agreement,
    disclosure_gap,
    gap_profile,
    to_events,
)


def _trades(rows) -> pd.DataFrame:
    """One frame of open-market trades from (owner, date, code, shares, price) rows."""
    frame = pd.DataFrame(rows, columns=["owner_cik", "transaction_date",
                                        "transaction_code", "shares", "price"])
    frame["transaction_date"] = pd.to_datetime(frame["transaction_date"]).dt.date
    frame["acquired"] = np.where(frame["transaction_code"] == "P", "A", "D")
    frame["accession"] = [f"a{i}" for i in range(len(frame))]
    frame["ticker"] = "AAPL"
    frame["plan_10b5_1"] = False
    frame["is_officer"] = True
    frame["is_director"] = False
    frame["is_ten_percent_owner"] = False
    frame["acceptance_time"] = pd.to_datetime(
        frame["transaction_date"]).dt.tz_localize("America/New_York") + pd.Timedelta(days=2)
    return frame


# Someone who buys every March for four years running.
SCHEDULED = [("1", f"{year}-03-10", "P", 100, 10.0) for year in (2020, 2021, 2022, 2023)]


class TestTheScheduleLabelLooksOnlyBackwards:
    def test_four_years_of_the_same_month_is_routine_by_the_fourth(self):
        labels = causal_routine(_trades(SCHEDULED))
        assert list(labels) == [UNKNOWN, UNKNOWN, UNKNOWN, ROUTINE]

    def test_a_broken_run_is_opportunistic_not_routine(self):
        """Three prior years are required, and all three must have the month."""
        rows = [("1", "2020-03-10", "P", 100, 10.0),
                ("1", "2021-07-10", "P", 100, 10.0),   # wrong month
                ("1", "2022-03-10", "P", 100, 10.0),
                ("1", "2023-03-10", "P", 100, 10.0)]
        assert causal_routine(_trades(rows)).iloc[-1] == OPPORTUNISTIC

    def test_too_little_history_is_unknown_not_opportunistic(self):
        """"We have no evidence this person trades on a schedule" and "we have
        three years showing they do not" are different claims."""
        rows = [("1", "2022-03-10", "P", 100, 10.0), ("1", "2023-03-10", "P", 100, 10.0)]
        assert set(causal_routine(_trades(rows))) == {UNKNOWN}

    def test_a_later_trade_cannot_change_an_earlier_label(self):
        """The property the whole classification rests on."""
        short = causal_routine(_trades(SCHEDULED))
        extended = causal_routine(_trades([*SCHEDULED, ("1", "2024-03-10", "P", 5, 9.0)]))
        assert list(extended)[:len(short)] == list(short)

    def test_one_insiders_history_does_not_label_another(self):
        rows = [*SCHEDULED, ("2", "2023-03-10", "P", 100, 10.0)]
        labels = causal_routine(_trades(rows))
        assert labels.iloc[-1] == UNKNOWN
        assert labels.iloc[-2] == ROUTINE

    def test_an_empty_frame_returns_an_empty_label(self):
        assert causal_routine(_trades([])).empty


class TestTheDisclosureWindow:
    def test_the_gap_is_measured_from_the_trade_to_the_acceptance(self):
        frame = _trades([("1", "2024-03-01", "P", 100, 10.0)])
        assert disclosure_gap(frame).iloc[0] == pytest.approx(2.0)

    def test_a_same_day_filing_has_no_window(self):
        frame = _trades([("1", "2024-03-01", "P", 100, 10.0)])
        frame["acceptance_time"] = pd.Timestamp("2024-03-01 18:00",
                                                tz="America/New_York")
        assert disclosure_gap(frame).iloc[0] == pytest.approx(0.0)

    def test_the_profile_reports_a_distribution_not_a_mean(self):
        """Most filings arrive on the deadline; the tail is where a study
        anchored at the transaction date reads the most future."""
        events = pd.DataFrame({"disclosure_gap_days": [0, 1, 2, 2, 2, 9]})
        profile = gap_profile(events)
        assert set(profile["statistic"]) >= {"filings", "mean", "p50", "p99"}
        assert profile.loc[profile["statistic"] == "p100", "calendar_days"].iloc[0] == 9

    def test_an_empty_frame_profiles_to_nothing(self):
        assert gap_profile(pd.DataFrame()).empty


class TestOneEventPerFiling:
    def test_compensation_rows_produce_no_event(self):
        """A filing reporting only a vest and its tax withholding decided
        nothing, so there is nothing to react to."""
        frame = _trades([("1", "2024-03-01", "M", 100, 10.0),
                         ("1", "2024-03-01", "F", 40, 10.0)])
        assert to_events(frame).empty

    def test_a_filing_with_several_trades_is_one_row(self):
        frame = _trades([("1", "2024-03-01", "S", 100, 10.0),
                         ("1", "2024-03-02", "S", 50, 12.0)])
        frame["accession"] = "same"
        events = to_events(frame)
        assert len(events) == 1
        assert events.iloc[0]["trades"] == 2

    def test_net_and_gross_value_differ_when_a_filing_does_both(self):
        """A large buy and a large sell on the same day is not the same
        disclosure as nothing happening."""
        frame = _trades([("1", "2024-03-01", "P", 100, 10.0),
                         ("1", "2024-03-01", "S", 100, 10.0)])
        frame["accession"] = "same"
        row = to_events(frame).iloc[0]
        assert row["net_value"] == pytest.approx(0.0)
        assert row["gross_value"] == pytest.approx(2000.0)
        assert row["direction"] == "flat"

    def test_direction_follows_the_net(self):
        buy = to_events(_trades([("1", "2024-03-01", "P", 100, 10.0)]))
        sell = to_events(_trades([("1", "2024-03-01", "S", 100, 10.0)]))
        assert buy.iloc[0]["direction"] == "buy"
        assert sell.iloc[0]["direction"] == "sell"

    def test_one_opportunistic_trade_makes_the_filing_opportunistic(self):
        """An unscheduled decision inside a filing is what makes it
        informative; averaging it in with the scheduled ones would hide it."""
        rows = [*SCHEDULED, ("1", "2023-03-10", "S", 100, 10.0)]
        frame = _trades(rows)
        frame.loc[frame.index[-1], "transaction_date"] = pd.Timestamp("2023-08-01").date()
        frame["accession"] = ["a", "b", "c", "same", "same"]
        events = to_events(frame)
        assert events.set_index("event_id").loc["same", "behaviour"] == OPPORTUNISTIC

    def test_the_knowledge_time_survives_onto_the_event(self):
        events = to_events(_trades([("1", "2024-03-01", "P", 100, 10.0)]))
        assert pd.notna(events.iloc[0]["acceptance_time"])
        assert events.iloc[0]["disclosure_gap_days"] == pytest.approx(2.0)

    def test_co_filers_are_counted(self):
        frame = _trades([("1", "2024-03-01", "P", 100, 10.0),
                         ("2", "2024-03-01", "P", 100, 10.0)])
        frame["accession"] = "same"
        assert to_events(frame).iloc[0]["owners"] == 2


class TestTheInferredLabelIsScoredAgainstTheDisclosedOne:
    def test_agreement_is_reported_per_behaviour_with_its_count(self):
        """Cohen, Malloy and Pomorski had to infer what filers now disclose.
        Scoring one against the other is free, and it is a check on a
        well-known method against ground truth it never had."""
        frame = _trades(SCHEDULED)
        frame["behaviour"] = causal_routine(frame)
        frame["plan_10b5_1"] = [False, False, False, True]
        table = classification_agreement(frame)
        routine = table[table["behaviour"] == ROUTINE].iloc[0]
        assert routine["trades"] == 1
        assert routine["disclosed_under_a_plan"] == pytest.approx(1.0)

    def test_no_behaviour_column_yields_nothing_rather_than_raising(self):
        assert classification_agreement(_trades(SCHEDULED)).empty
