"""Point-in-time clock: the single authority on *when* a fact became knowable.

An SEC filing carries three different timestamps, and confusing them is the most
common way to manufacture fake signal:

    period_of_report    the fiscal period the filing describes.
                        Months before the public learns anything. Never knowable.
    filing_date         the calendar date EDGAR stamped on it. Date only, no time.
                        A filing stamped "Monday" may have been accepted at 16:05
                        Monday -- after the close. Treating it as knowable at
                        Monday's open buys you seven hours of hindsight.
    acceptance_time     the moment EDGAR accepted the submission, to the second.
                        This is the knowledge time. Everything keys off this.

From a knowledge time this module derives, conservatively:

    decision_time = acceptance_time + embargo
    entry_session = the first trading session whose OPEN is at or after decision_time

The "open" convention matters. We work with daily bars, so the earliest price we
can honestly transact at is an opening print that had not yet happened when the
information arrived. A filing accepted at 16:05 ET Monday is tradable at
Tuesday's open, never at Monday's.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
EARLY_CLOSE = time(13, 0)


# --------------------------------------------------------------------------- #
# NYSE calendar
# --------------------------------------------------------------------------- #
def _easter(year: int) -> date:
    """Gregorian Easter (Meeus/Jones/Butcher). Good Friday is two days earlier."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    lam = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * lam) // 433
    month, day = divmod(h + lam - 7 * m + 90, 25)
    day = (h + lam - 7 * m + 33 * month + 19) % 32
    return date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """n-th `weekday` (Mon=0) of a month; n=-1 means the last one."""
    if n > 0:
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + timedelta(days=offset + 7 * (n - 1))
    last_day = (date(year, month, 28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def _observed(d: date) -> date | None:
    """NYSE observation rule: Sat -> preceding Fri, Sun -> following Mon."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


@lru_cache(maxsize=64)
def _holidays(year: int) -> frozenset[date]:
    days: set[date] = set()

    # New Year's Day. Unlike every other holiday, a Saturday New Year's is NOT
    # observed on the preceding Friday -- that Friday belongs to the prior year
    # and the NYSE stays open.
    ny = date(year, 1, 1)
    if ny.weekday() == 6:
        days.add(ny + timedelta(days=1))
    elif ny.weekday() != 5:
        days.add(ny)

    days.add(_nth_weekday(year, 1, 0, 3))                     # MLK Day
    days.add(_nth_weekday(year, 2, 0, 3))                     # Washington's Birthday
    days.add(_easter(year) - timedelta(days=2))               # Good Friday
    days.add(_nth_weekday(year, 5, 0, -1))                    # Memorial Day
    if year >= 2022:                                          # Juneteenth
        days.add(_observed(date(year, 6, 19)))
    days.add(_observed(date(year, 7, 4)))                     # Independence Day
    days.add(_nth_weekday(year, 9, 0, 1))                     # Labor Day
    days.add(_nth_weekday(year, 11, 3, 4))                    # Thanksgiving
    days.add(_observed(date(year, 12, 25)))                   # Christmas

    # Ad-hoc closures that no rule generates.
    days.update({
        date(2012, 10, 29), date(2012, 10, 30),   # Hurricane Sandy
        date(2018, 12, 5),                        # G.H.W. Bush national day of mourning
        date(2025, 1, 9),                         # Carter national day of mourning
    } & {d for d in _year_span(year)})
    return frozenset(d for d in days if d.year == year)


def _year_span(year: int) -> set[date]:
    start = date(year, 1, 1)
    return {start + timedelta(days=i) for i in range((date(year + 1, 1, 1) - start).days)}


@lru_cache(maxsize=64)
def _early_closes(year: int) -> frozenset[date]:
    """1:00 pm ET sessions. Only the recurring ones -- they are what matter for
    classifying a filing as 'arrived while the market was open'."""
    days: set[date] = set()
    hol = _holidays(year)

    july3 = date(year, 7, 3)
    if july3.weekday() < 5 and july3 not in hol and date(year, 7, 4) in hol:
        days.add(july3)

    days.add(_nth_weekday(year, 11, 3, 4) + timedelta(days=1))   # day after Thanksgiving

    dec24 = date(year, 12, 24)
    if dec24.weekday() < 5 and dec24 not in hol:
        days.add(dec24)

    return frozenset(d for d in days if d not in hol)


class MarketCalendar:
    """NYSE sessions. Rule-generated, so it works for any year without a data file."""

    def is_session(self, d: date) -> bool:
        return d.weekday() < 5 and d not in _holidays(d.year)

    def close_time(self, d: date) -> time:
        return EARLY_CLOSE if d in _early_closes(d.year) else REGULAR_CLOSE

    def open_at(self, d: date) -> datetime:
        return datetime.combine(d, REGULAR_OPEN, tzinfo=ET)

    def close_at(self, d: date) -> datetime:
        return datetime.combine(d, self.close_time(d), tzinfo=ET)

    def next_session(self, d: date, *, inclusive: bool = False) -> date:
        cur = d if inclusive else d + timedelta(days=1)
        for _ in range(15):
            if self.is_session(cur):
                return cur
            cur += timedelta(days=1)
        raise RuntimeError(f"no trading session within 15 days of {d}")

    def shift(self, d: date, n: int) -> date:
        """Move `n` sessions from session `d` (n may be negative)."""
        if n == 0:
            return d
        step = timedelta(days=1 if n > 0 else -1)
        cur, remaining = d, abs(n)
        while remaining:
            cur += step
            if self.is_session(cur):
                remaining -= 1
        return cur

    def sessions_between(self, start: date, end: date) -> list[date]:
        """Inclusive on both ends."""
        out, cur = [], start
        while cur <= end:
            if self.is_session(cur):
                out.append(cur)
            cur += timedelta(days=1)
        return out


CALENDAR = MarketCalendar()


# --------------------------------------------------------------------------- #
# The clock
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TradingClock:
    """Maps a knowledge time to the earliest session we may honestly act in.

    `embargo` is the deliberate delay between learning something and being allowed
    to act on it. Sweeping it (0 min, 15 min, 1 day...) is how we measure how fast
    the information decays -- and how much of an apparent effect is really just
    the reaction we already missed.
    """

    embargo: timedelta = timedelta(0)
    calendar: MarketCalendar = CALENDAR

    def decision_time(self, knowledge_time: datetime) -> datetime:
        return _as_et(knowledge_time) + self.embargo

    def entry_session(self, knowledge_time: datetime) -> date:
        """First session whose OPEN is at or after the decision time."""
        dt = self.decision_time(knowledge_time)
        day = self.calendar.next_session(dt.date(), inclusive=True)
        if self.calendar.open_at(day) < dt:
            day = self.calendar.next_session(day)
        return day

    def session_state(self, knowledge_time: datetime) -> str:
        """Where in the trading day the filing landed: pre / open / post / closed.

        A real feature -- filings are overwhelmingly released outside market hours,
        and the ones that are not behave differently.
        """
        dt = _as_et(knowledge_time)
        d = dt.date()
        if not self.calendar.is_session(d):
            return "closed"
        if dt < self.calendar.open_at(d):
            return "pre"
        if dt < self.calendar.close_at(d):
            return "open"
        return "post"


def _as_et(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError(
            "naive datetime reached the PIT clock. Every timestamp must carry a "
            "timezone -- ambiguity here is exactly how lookahead bias gets in."
        )
    return dt.astimezone(ET)


# --------------------------------------------------------------------------- #
# The naive alternatives -- kept so we can measure what they cost
# --------------------------------------------------------------------------- #
def naive_entry_session_from_filing_date(filing_date: date) -> date:
    """BUG, ON PURPOSE. Treats the filing *date* as tradable at its own open.

    Roughly 80% of 8-Ks are accepted outside market hours. For those, this enters
    the position hours before the information existed. `experiments/leakage.py`
    measures what that hindsight is worth.
    """
    return CALENDAR.next_session(filing_date, inclusive=True)


def naive_entry_session_from_period(period_of_report: date) -> date:
    """BUG, ON PURPOSE. Uses the fiscal period end -- typically weeks to months
    before anyone outside the company knew anything."""
    return CALENDAR.next_session(period_of_report, inclusive=True)
