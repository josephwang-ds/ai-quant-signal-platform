"""Timestamp discipline for text-derived signals.

The failure mode of nearly all text-alpha research is treating a document as
usable at a bar it could not have been acted on. This module makes the
relevant instants explicit and separates the three that are routinely and
incorrectly collapsed into one:

    event_time                  when the underlying thing happened
    publish_time                when the document became public
    ingest_time                 when this pipeline actually received it
    information_available_time  when it could first inform anything
                                = max(publish_time + buffer, ingest_time)
    execution_time              the session open at which a resulting position
                                could first be taken

``information_available_time`` and ``execution_time`` are *derived* and cannot
be supplied by a caller. A document is readable by a feature computed at
instant ``T`` when ``information_available_time <= T``; whether the resulting
position is executable is a separate question answered by ``execution_time``.
Collapsing the two is how look-ahead enters text research.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Protocol, runtime_checkable
from zoneinfo import ZoneInfo

MARKET_TZ = ZoneInfo("America/New_York")

#: US equity regular session open.
SESSION_OPEN = time(9, 30)

#: Acceptance is not dissemination. EDGAR propagation, vendor relay and human
#: reading all take time. Conservative by default; any override is recorded.
DEFAULT_DISSEMINATION_BUFFER = timedelta(minutes=30)


class IngestSource(str, Enum):
    """Where ``ingest_time`` came from.

    A backfilled corpus cannot have observed its own history. Reconstructing
    "when would my collector have seen this?" is legitimate and necessary, but
    it is an assumption, and an assumption presented as a measurement is the
    thing this platform exists not to do.
    """

    #: A collector was running and recorded receipt as it happened.
    OBSERVED = "observed"

    #: Reconstructed after the fact from publish time plus an assumed polling
    #: interval. Defensible for EDGAR, whose index is public and continuously
    #: updated — but it must be declared.
    SIMULATED = "simulated"


class LookaheadError(AssertionError):
    """Raised when a record would be read before it was knowable."""


class IngestIntegrityError(AssertionError):
    """Raised when a record claims observation it could not have made."""


class CalendarCoverageError(ValueError):
    """Raised when a date falls outside the calendar's verified range.

    Fail closed. A calendar silently extrapolating past its maintained range
    is how holiday drift produces phantom returns.
    """


class UnapprovedCalendarError(ValueError):
    """Raised when a test-grade calendar is used on a research path."""


@runtime_checkable
class SessionCalendar(Protocol):
    """Minimal trading-calendar surface this module depends on."""

    name: str
    approved_for_research: bool

    def covers(self, day: date) -> bool: ...
    def is_session(self, day: date) -> bool: ...


@dataclass(frozen=True)
class WeekdayCalendar:
    """Weekday-only calendar. **Unit tests only.**

    Knows nothing about US market holidays, so it will happily place a
    decision on Thanksgiving. ``approved_for_research`` defaults to ``False``
    and research entry points reject it.
    """

    name: str = "weekday-test-only"
    holidays: frozenset[date] = frozenset()
    approved_for_research: bool = False

    def covers(self, day: date) -> bool:  # noqa: ARG002
        return True

    def is_session(self, day: date) -> bool:
        return day.weekday() < 5 and day not in self.holidays


@dataclass(frozen=True)
class StaticHolidayCalendar:
    """Exchange calendar backed by an explicit, bounded holiday set.

    Coverage is bounded on purpose: outside ``[start, end]`` it raises rather
    than guessing. Supply ``holidays`` from a maintained source and set
    ``approved_for_research=True`` only once you have verified it.
    """

    name: str
    holidays: frozenset[date]
    start: date
    end: date
    approved_for_research: bool = True

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end

    def is_session(self, day: date) -> bool:
        if not self.covers(day):
            raise CalendarCoverageError(
                f"{self.name}: {day.isoformat()} is outside verified coverage "
                f"{self.start.isoformat()}..{self.end.isoformat()}"
            )
        return day.weekday() < 5 and day not in self.holidays


def require_research_calendar(calendar: SessionCalendar) -> None:
    """Gate for research paths. Fail closed on test-grade calendars."""
    if not getattr(calendar, "approved_for_research", False):
        raise UnapprovedCalendarError(
            f"calendar {getattr(calendar, 'name', calendar)!r} is not approved "
            "for research use; inject a maintained exchange calendar"
        )


def _as_market_time(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("naive datetime rejected; supply an aware datetime")
    return moment.astimezone(MARKET_TZ)


def next_session_open(
    moment: datetime,
    calendar: SessionCalendar,
    *,
    max_lookahead_days: int = 10,
) -> datetime:
    """First regular-session open at or after ``moment``."""
    local = _as_market_time(moment)
    for offset in range(max_lookahead_days + 1):
        day = (local + timedelta(days=offset)).date()
        if not calendar.is_session(day):
            continue
        candidate = datetime.combine(day, SESSION_OPEN, tzinfo=MARKET_TZ)
        if candidate >= local:
            return candidate
    raise ValueError(
        f"no session open found within {max_lookahead_days} days of {moment!r}"
    )


def derive_information_available_time(
    publish_time: datetime,
    ingest_time: datetime,
    *,
    dissemination_buffer: timedelta = DEFAULT_DISSEMINATION_BUFFER,
) -> datetime:
    """Earliest instant the document could have informed anything.

    Takes the later of dissemination and actual receipt: a filing this
    pipeline had not yet received was not available to this pipeline, however
    public it was.
    """
    if dissemination_buffer < timedelta(0):
        raise ValueError("dissemination_buffer must be non-negative")
    return max(
        _as_market_time(publish_time) + dissemination_buffer,
        _as_market_time(ingest_time),
    )


@dataclass(frozen=True)
class TextRecord:
    """A text document with its full timestamp provenance.

    ``information_available_time`` and ``execution_time`` are derived and are
    not constructor arguments; use :meth:`resolve` to populate them.
    """

    doc_id: str
    symbol: str
    publish_time: datetime
    ingest_time: datetime
    #: Deliberately has no default. Every record must declare whether its
    #: receipt time was measured or reconstructed; forgetting to choose is not
    #: an available option.
    ingest_time_source: IngestSource
    event_time: datetime | None = None
    source: str = "unknown"

    _information_available_time: datetime | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _execution_time: datetime | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _dissemination_buffer: timedelta | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _calendar_name: str | None = field(
        default=None, init=False, repr=False, compare=False
    )

    @property
    def information_available_time(self) -> datetime | None:
        return self._information_available_time

    @property
    def execution_time(self) -> datetime | None:
        return self._execution_time

    @property
    def calendar_name(self) -> str | None:
        return self._calendar_name

    @property
    def resolved(self) -> bool:
        return self._information_available_time is not None

    def resolve(
        self,
        calendar: SessionCalendar,
        *,
        dissemination_buffer: timedelta = DEFAULT_DISSEMINATION_BUFFER,
        research: bool = True,
    ) -> "TextRecord":
        """Derive availability and execution instants. Returns a new record."""
        if research:
            require_research_calendar(calendar)

        available = derive_information_available_time(
            self.publish_time,
            self.ingest_time,
            dissemination_buffer=dissemination_buffer,
        )
        execution = next_session_open(available, calendar)

        clone = TextRecord(
            doc_id=self.doc_id,
            symbol=self.symbol,
            publish_time=self.publish_time,
            ingest_time=self.ingest_time,
            ingest_time_source=self.ingest_time_source,
            event_time=self.event_time,
            source=self.source,
        )
        object.__setattr__(clone, "_information_available_time", available)
        object.__setattr__(clone, "_execution_time", execution)
        object.__setattr__(clone, "_dissemination_buffer", dissemination_buffer)
        object.__setattr__(clone, "_calendar_name", getattr(calendar, "name", None))
        return clone

    @property
    def publish_to_execution_gap(self) -> timedelta:
        """Reported metric, not an implementation detail.

        Concentrated near the buffer means documents arrive in session hours;
        a long right tail means weekend and after-hours filings dominate. The
        two cases mean different things for what the signal can be.
        """
        if self._execution_time is None:
            raise ValueError(f"{self.doc_id}: not resolved; call resolve() first")
        return self._execution_time - _as_market_time(self.publish_time)

    @property
    def ingest_binding(self) -> bool:
        """True when late receipt, not dissemination, set availability.

        A high rate means the corpus was assembled after the fact and the
        availability claim rests on backfill assumptions.
        """
        if self._information_available_time is None or self._dissemination_buffer is None:
            raise ValueError(f"{self.doc_id}: not resolved; call resolve() first")
        return self._information_available_time > (
            _as_market_time(self.publish_time) + self._dissemination_buffer
        )


def assert_no_lookahead(
    records: Iterable[TextRecord],
    signal_computation_time: datetime,
) -> None:
    """Guard: no record may be read before it was available.

    Call at the top of every feature builder. A record whose availability
    instant equals the computation instant is admissible — the information
    exists at that moment. Execution timing is a separate constraint, carried
    by :attr:`TextRecord.execution_time`.
    """
    cutoff = _as_market_time(signal_computation_time)
    for record in records:
        available = record.information_available_time
        if available is None:
            raise LookaheadError(
                f"{record.doc_id}: unresolved; call resolve() before feature "
                "construction"
            )
        if available > cutoff:
            raise LookaheadError(
                f"{record.doc_id}: available {available.isoformat()} is after "
                f"signal computation instant {cutoff.isoformat()}"
            )


def assert_ingest_integrity(
    records: Iterable[TextRecord],
    research_period_end: datetime,
) -> None:
    """Guard: a record may only claim OBSERVED if it could have been observed.

    A collector running during the study period produces receipt times inside
    that period. A record stamped OBSERVED with a receipt time after the study
    ended was necessarily backfilled, and the label is false — which is worse
    than being SIMULATED, because it invites the reader to trust it more.
    """
    cutoff = _as_market_time(research_period_end)
    for record in records:
        if record.ingest_time_source is not IngestSource.OBSERVED:
            continue
        ingest = _as_market_time(record.ingest_time)
        if ingest > cutoff:
            raise IngestIntegrityError(
                f"{record.doc_id}: claims OBSERVED ingest at "
                f"{ingest.isoformat()}, after the research period ended "
                f"{cutoff.isoformat()}; this record was backfilled and must be "
                "declared SIMULATED"
            )


def simulated_ingest_time(
    publish_time: datetime,
    *,
    polling_interval: timedelta,
) -> datetime:
    """Counterfactual receipt time for a backfilled document.

    Models a collector polling every ``polling_interval``: worst case it sees
    the document a full interval after publication. Conservative on purpose —
    assuming instant capture flatters the signal.

    The interval must be pre-registered alongside the hypothesis, because it
    is a free parameter that moves results.
    """
    if polling_interval < timedelta(0):
        raise ValueError("polling_interval must be non-negative")
    return _as_market_time(publish_time) + polling_interval


def usable_at(
    records: Sequence[TextRecord],
    signal_computation_time: datetime,
) -> list[TextRecord]:
    """Subset of ``records`` legitimately readable at the given instant."""
    cutoff = _as_market_time(signal_computation_time)
    return [
        record
        for record in records
        if record.information_available_time is not None
        and record.information_available_time <= cutoff
    ]


def gap_summary(records: Sequence[TextRecord]) -> dict[str, float | int | None]:
    """Publish-to-execution gap distribution, in hours, plus ingest binding.

    Belongs in every evidence package that uses a text channel.
    """
    resolved = [record for record in records if record.resolved]
    if not resolved:
        return {
            "n_records": 0,
            "median_gap_hours": None,
            "p95_gap_hours": None,
            "max_gap_hours": None,
            "ingest_bound_share": None,
            "simulated_ingest_share": None,
        }

    gaps = sorted(
        record.publish_to_execution_gap.total_seconds() / 3600.0 for record in resolved
    )
    n = len(gaps)

    def _quantile(q: float) -> float:
        if n == 1:
            return gaps[0]
        position = q * (n - 1)
        lower = int(position)
        upper = min(lower + 1, n - 1)
        weight = position - lower
        return gaps[lower] * (1 - weight) + gaps[upper] * weight

    return {
        "n_records": n,
        "median_gap_hours": _quantile(0.5),
        "p95_gap_hours": _quantile(0.95),
        "max_gap_hours": gaps[-1],
        "ingest_bound_share": sum(r.ingest_binding for r in resolved) / n,
        "simulated_ingest_share": sum(
            r.ingest_time_source is IngestSource.SIMULATED for r in resolved
        )
        / n,
    }
