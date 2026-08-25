"""The clock is load-bearing: if it is wrong, every number downstream is wrong."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from filing_triage.pit import (
    CALENDAR,
    ET,
    TradingClock,
    _easter,
    _holidays,
    naive_entry_session_from_filing_date,
)


class TestCalendar:
    def test_known_holidays(self):
        assert date(2024, 1, 1) in _holidays(2024)       # New Year's Day
        assert date(2024, 3, 29) in _holidays(2024)      # Good Friday
        assert date(2024, 6, 19) in _holidays(2024)      # Juneteenth
        assert date(2024, 11, 28) in _holidays(2024)     # Thanksgiving
        assert date(2024, 12, 25) in _holidays(2024)     # Christmas

    def test_juneteenth_only_from_2022(self):
        assert date(2021, 6, 18) not in _holidays(2021)
        assert date(2022, 6, 20) in _holidays(2022)      # 19th was a Sunday

    def test_saturday_new_year_is_not_observed_on_friday(self):
        """The one holiday that breaks the observation rule: NYSE stays open on
        the preceding Friday, because that Friday belongs to the prior year."""
        assert date(2022, 1, 1).weekday() == 5
        assert date(2021, 12, 31) not in _holidays(2021)
        assert CALENDAR.is_session(date(2021, 12, 31))

    def test_sunday_holiday_observed_on_monday(self):
        assert date(2021, 7, 4).weekday() == 6
        assert date(2021, 7, 5) in _holidays(2021)

    def test_saturday_holiday_observed_on_friday(self):
        """Christmas 2021 fell on a Saturday; the NYSE closed Friday the 24th."""
        assert date(2021, 12, 25).weekday() == 5
        assert date(2021, 12, 24) in _holidays(2021)
        assert not CALENDAR.is_session(date(2021, 12, 24))

    def test_easter(self):
        assert _easter(2024) == date(2024, 3, 31)
        assert _easter(2025) == date(2025, 4, 20)
        assert _easter(2026) == date(2026, 4, 5)

    def test_weekends_are_not_sessions(self):
        assert not CALENDAR.is_session(date(2024, 7, 6))     # Saturday
        assert not CALENDAR.is_session(date(2024, 7, 7))     # Sunday
        assert CALENDAR.is_session(date(2024, 7, 8))         # Monday

    def test_early_close(self):
        """Day after Thanksgiving closes at 13:00."""
        assert CALENDAR.close_time(date(2024, 11, 29)).hour == 13
        assert CALENDAR.close_time(date(2024, 11, 26)).hour == 16

    def test_shift_is_symmetric(self):
        start = date(2024, 3, 15)
        assert CALENDAR.shift(CALENDAR.shift(start, 20), -20) == start

    def test_shift_skips_holidays(self):
        # 2024-11-27 (Wed) +1 session skips Thanksgiving to the 29th.
        assert CALENDAR.shift(date(2024, 11, 27), 1) == date(2024, 11, 29)


class TestClock:
    clock = TradingClock()

    def test_after_hours_filing_is_tradable_next_session(self):
        accepted = datetime(2024, 10, 31, 18, 3, tzinfo=ET)
        assert self.clock.entry_session(accepted) == date(2024, 11, 1)
        assert self.clock.session_state(accepted) == "post"

    def test_premarket_filing_is_tradable_same_session(self):
        accepted = datetime(2024, 10, 31, 7, 30, tzinfo=ET)
        assert self.clock.entry_session(accepted) == date(2024, 10, 31)
        assert self.clock.session_state(accepted) == "pre"

    def test_intraday_filing_waits_for_the_next_open(self):
        """We hold daily bars. The only honest fill after the open has passed is
        the next one."""
        accepted = datetime(2024, 10, 31, 11, 0, tzinfo=ET)
        assert self.clock.session_state(accepted) == "open"
        assert self.clock.entry_session(accepted) == date(2024, 11, 1)

    def test_friday_evening_filing_waits_for_monday(self):
        accepted = datetime(2024, 11, 1, 20, 0, tzinfo=ET)     # Friday
        assert self.clock.entry_session(accepted) == date(2024, 11, 4)

    def test_filing_before_a_long_weekend(self):
        # Friday 2024-05-24 evening; Memorial Day is Monday the 27th.
        accepted = datetime(2024, 5, 24, 17, 0, tzinfo=ET)
        assert self.clock.entry_session(accepted) == date(2024, 5, 28)

    def test_embargo_pushes_entry_out(self):
        accepted = datetime(2024, 10, 31, 8, 0, tzinfo=ET)
        assert TradingClock().entry_session(accepted) == date(2024, 10, 31)
        delayed = TradingClock(embargo=timedelta(hours=3))
        assert delayed.entry_session(accepted) == date(2024, 11, 1)

    def test_entry_open_is_never_before_the_filing(self):
        """The invariant the whole project rests on."""
        for hour in range(24):
            accepted = datetime(2024, 10, 31, hour, 15, tzinfo=ET)
            entry = self.clock.entry_session(accepted)
            assert CALENDAR.open_at(entry) >= accepted

    def test_naive_datetime_is_rejected(self):
        with pytest.raises(ValueError, match="timezone"):
            self.clock.entry_session(datetime(2024, 10, 31, 18, 3))


class TestNaiveEntryIsActuallyWrong:
    """These assert the bug, so that the leakage experiment measures something real."""

    def test_naive_entry_precedes_an_after_hours_filing(self):
        accepted = datetime(2024, 10, 31, 18, 3, tzinfo=ET)
        naive = naive_entry_session_from_filing_date(accepted.date())
        assert CALENDAR.open_at(naive) < accepted
        hindsight = (accepted - CALENDAR.open_at(naive)).total_seconds() / 3600
        assert hindsight > 8

    def test_correct_entry_never_precedes_the_filing(self):
        accepted = datetime(2024, 10, 31, 18, 3, tzinfo=ET)
        correct = TradingClock().entry_session(accepted)
        assert CALENDAR.open_at(correct) > accepted
