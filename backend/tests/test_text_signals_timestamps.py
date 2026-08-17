"""Timestamp discipline tests.

The central claim these protect: a document cannot be read before it was both
public *and* received, and the instant it becomes readable is separate from
the instant a resulting position becomes executable. If any of these fail,
every downstream result is fiction.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.text_signals.timestamps import (
    DEFAULT_DISSEMINATION_BUFFER,
    CalendarCoverageError,
    LookaheadError,
    StaticHolidayCalendar,
    TextRecord,
    IngestIntegrityError,
    IngestSource,
    UnapprovedCalendarError,
    WeekdayCalendar,
    assert_ingest_integrity,
    assert_no_lookahead,
    derive_information_available_time,
    simulated_ingest_time,
    gap_summary,
    next_session_open,
    require_research_calendar,
    usable_at,
)

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

TEST_CAL = WeekdayCalendar()
RESEARCH_CAL = StaticHolidayCalendar(
    name="us-equity-2026-test",
    holidays=frozenset({date(2026, 8, 18)}),
    start=date(2026, 1, 1),
    end=date(2026, 12, 31),
)


def _record(
    doc_id: str,
    publish: datetime,
    *,
    ingest_delay: timedelta = timedelta(minutes=1),
    symbol: str = "AAPL",
) -> TextRecord:
    return TextRecord(
        doc_id=doc_id,
        symbol=symbol,
        publish_time=publish,
        ingest_time=publish + ingest_delay,
        ingest_time_source=IngestSource.OBSERVED,
        source="edgar",
    ).resolve(TEST_CAL, research=False)


class TestNextSessionOpen:
    def test_before_open_on_a_session_day_uses_that_day(self):
        moment = datetime(2026, 8, 17, 7, 0, tzinfo=ET)  # Monday pre-market
        assert next_session_open(moment, TEST_CAL) == datetime(
            2026, 8, 17, 9, 30, tzinfo=ET
        )

    def test_after_open_rolls_to_next_session(self):
        moment = datetime(2026, 8, 17, 14, 0, tzinfo=ET)
        assert next_session_open(moment, TEST_CAL) == datetime(
            2026, 8, 18, 9, 30, tzinfo=ET
        )

    def test_friday_evening_rolls_to_monday(self):
        moment = datetime(2026, 8, 21, 18, 30, tzinfo=ET)
        assert next_session_open(moment, TEST_CAL) == datetime(
            2026, 8, 24, 9, 30, tzinfo=ET
        )

    def test_holiday_is_skipped(self):
        moment = datetime(2026, 8, 17, 14, 0, tzinfo=ET)
        assert next_session_open(moment, RESEARCH_CAL) == datetime(
            2026, 8, 19, 9, 30, tzinfo=ET
        )

    def test_naive_datetime_is_rejected(self):
        with pytest.raises(ValueError, match="naive datetime"):
            next_session_open(datetime(2026, 8, 17, 7, 0), TEST_CAL)

    def test_non_market_timezone_is_normalised(self):
        moment = datetime(2026, 8, 17, 13, 0, tzinfo=UTC)  # 09:00 ET
        assert next_session_open(moment, TEST_CAL) == datetime(
            2026, 8, 17, 9, 30, tzinfo=ET
        )


class TestCalendarSafety:
    """P0: a weekday-only calendar must not be usable for research."""

    def test_weekday_calendar_is_rejected_on_research_paths(self):
        with pytest.raises(UnapprovedCalendarError, match="not approved"):
            require_research_calendar(TEST_CAL)

    def test_resolve_defaults_to_research_mode_and_fails_closed(self):
        raw = TextRecord(
            doc_id="x",
            symbol="AAPL",
            publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        )
        with pytest.raises(UnapprovedCalendarError):
            raw.resolve(TEST_CAL)

    def test_maintained_calendar_is_accepted(self):
        require_research_calendar(RESEARCH_CAL)

    def test_outside_coverage_raises_rather_than_guessing(self):
        with pytest.raises(CalendarCoverageError, match="outside verified coverage"):
            RESEARCH_CAL.is_session(date(2030, 3, 4))


class TestInformationAvailableTime:
    """P0: ingest_time must participate."""

    def test_late_ingest_binds_availability(self):
        publish = datetime(2026, 8, 17, 8, 0, tzinfo=ET)
        ingest = datetime(2026, 8, 19, 12, 0, tzinfo=ET)  # backfilled two days later
        assert derive_information_available_time(publish, ingest) == ingest

    def test_prompt_ingest_leaves_buffer_binding(self):
        publish = datetime(2026, 8, 17, 8, 0, tzinfo=ET)
        ingest = publish + timedelta(seconds=5)
        assert derive_information_available_time(publish, ingest) == (
            publish + DEFAULT_DISSEMINATION_BUFFER
        )

    def test_backfilled_document_cannot_be_used_at_publish_time(self):
        """The bug this fixes: a doc the pipeline had not yet received."""
        record = TextRecord(
            doc_id="backfill",
            symbol="AAPL",
            publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 21, 8, 0, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        ).resolve(RESEARCH_CAL)
        with pytest.raises(LookaheadError):
            assert_no_lookahead([record], datetime(2026, 8, 17, 9, 30, tzinfo=ET))
        assert record.ingest_binding is True

    def test_ingest_binding_false_for_realtime_capture(self):
        assert _record("live", datetime(2026, 8, 17, 8, 0, tzinfo=ET)).ingest_binding is False

    def test_negative_buffer_rejected(self):
        moment = datetime(2026, 8, 17, 9, 0, tzinfo=ET)
        with pytest.raises(ValueError, match="non-negative"):
            derive_information_available_time(
                moment, moment, dissemination_buffer=-timedelta(minutes=1)
            )


class TestDerivedFieldsCannotBeSupplied:
    """P0: derived, never supplied."""

    def test_constructor_rejects_derived_instants(self):
        with pytest.raises(TypeError):
            TextRecord(
                doc_id="x",
                symbol="AAPL",
                publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
                ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
                ingest_time_source=IngestSource.OBSERVED,
                information_available_time=datetime(2020, 1, 1, tzinfo=ET),
            )

    def test_unresolved_record_exposes_none(self):
        raw = TextRecord(
            doc_id="x",
            symbol="AAPL",
            publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        )
        assert raw.resolved is False
        assert raw.information_available_time is None
        assert raw.execution_time is None

    def test_resolve_records_the_calendar_used(self):
        record = TextRecord(
            doc_id="x",
            symbol="AAPL",
            publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        ).resolve(RESEARCH_CAL)
        assert record.calendar_name == "us-equity-2026-test"


class TestAvailabilityVersusExecution:
    """P1: the two instants are distinct and must not be conflated."""

    def test_available_intraday_but_executable_next_open(self):
        record = _record("intraday", datetime(2026, 8, 17, 11, 0, tzinfo=ET))
        assert record.information_available_time == datetime(
            2026, 8, 17, 11, 30, tzinfo=ET
        )
        assert record.execution_time == datetime(2026, 8, 18, 9, 30, tzinfo=ET)
        assert record.execution_time > record.information_available_time

    def test_availability_equal_to_computation_instant_is_admissible(self):
        record = _record("edge", datetime(2026, 8, 17, 8, 0, tzinfo=ET))
        exact = record.information_available_time
        assert_no_lookahead([record], exact)
        with pytest.raises(LookaheadError):
            assert_no_lookahead([record], exact - timedelta(seconds=1))

    def test_execution_is_always_after_publish(self):
        for publish in (
            datetime(2026, 8, 17, 4, 0, tzinfo=ET),
            datetime(2026, 8, 17, 9, 29, tzinfo=ET),
            datetime(2026, 8, 17, 16, 5, tzinfo=ET),
            datetime(2026, 8, 22, 11, 0, tzinfo=ET),  # Saturday
        ):
            assert _record("r", publish).execution_time > publish


class TestLookaheadGuard:
    def test_future_record_is_rejected(self):
        record = _record("0001", datetime(2026, 8, 17, 16, 5, tzinfo=ET))
        with pytest.raises(LookaheadError, match="is after signal computation"):
            assert_no_lookahead([record], datetime(2026, 8, 17, 9, 30, tzinfo=ET))

    def test_past_record_passes(self):
        record = _record("0001", datetime(2026, 8, 14, 16, 5, tzinfo=ET))
        assert_no_lookahead([record], datetime(2026, 8, 18, 9, 30, tzinfo=ET))

    def test_unresolved_record_is_an_error_not_a_pass(self):
        raw = TextRecord(
            doc_id="0002",
            symbol="MSFT",
            publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        )
        with pytest.raises(LookaheadError, match="unresolved"):
            assert_no_lookahead([raw], datetime(2026, 8, 20, 9, 30, tzinfo=ET))


class TestUsableAt:
    def test_filters_to_knowable_records(self):
        records = [
            _record("early", datetime(2026, 8, 13, 10, 0, tzinfo=ET)),
            _record("late", datetime(2026, 8, 19, 10, 0, tzinfo=ET)),
        ]
        visible = usable_at(records, datetime(2026, 8, 17, 9, 30, tzinfo=ET))
        assert [r.doc_id for r in visible] == ["early"]

    def test_unresolved_records_are_never_usable(self):
        raw = TextRecord(
            doc_id="raw",
            symbol="X",
            publish_time=datetime(2020, 1, 2, 10, 0, tzinfo=ET),
            ingest_time=datetime(2020, 1, 2, 10, 1, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        )
        assert usable_at([raw], datetime(2026, 8, 17, 9, 30, tzinfo=ET)) == []


class TestGapSummary:
    def test_weekend_filing_has_a_long_gap(self):
        record = _record("weekend", datetime(2026, 8, 22, 10, 0, tzinfo=ET))
        assert record.publish_to_execution_gap.total_seconds() / 3600.0 > 40

    def test_summary_reports_distribution_and_ingest_binding(self):
        records = [
            _record("a", datetime(2026, 8, 17, 8, 0, tzinfo=ET)),
            _record("b", datetime(2026, 8, 18, 8, 0, tzinfo=ET)),
            _record(
                "c",
                datetime(2026, 8, 19, 8, 0, tzinfo=ET),
                ingest_delay=timedelta(days=2),  # backfilled
            ),
        ]
        summary = gap_summary(records)
        assert summary["n_records"] == 3
        assert summary["ingest_bound_share"] == pytest.approx(1 / 3)
        assert summary["max_gap_hours"] > summary["median_gap_hours"]

    def test_empty_input_returns_nulls_not_zeros(self):
        summary = gap_summary([])
        assert summary["n_records"] == 0
        assert summary["median_gap_hours"] is None
        assert summary["ingest_bound_share"] is None


class TestIngestProvenance:
    """A backfilled corpus must not claim it observed its own history."""

    def test_ingest_source_has_no_default(self):
        with pytest.raises(TypeError):
            TextRecord(
                doc_id="x",
                symbol="AAPL",
                publish_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
                ingest_time=datetime(2026, 8, 17, 8, 1, tzinfo=ET),
            )

    def test_observed_claim_after_study_end_is_rejected(self):
        record = TextRecord(
            doc_id="backfilled-but-mislabelled",
            symbol="AAPL",
            publish_time=datetime(2020, 3, 15, 8, 0, tzinfo=ET),
            ingest_time=datetime(2026, 8, 17, 8, 0, tzinfo=ET),
            ingest_time_source=IngestSource.OBSERVED,
        )
        with pytest.raises(IngestIntegrityError, match="must be\n *declared SIMULATED|declared SIMULATED"):
            assert_ingest_integrity([record], datetime(2025, 12, 31, tzinfo=ET))

    def test_simulated_claim_after_study_end_is_fine(self):
        record = TextRecord(
            doc_id="honest-backfill",
            symbol="AAPL",
            publish_time=datetime(2020, 3, 15, 8, 0, tzinfo=ET),
            ingest_time=simulated_ingest_time(
                datetime(2020, 3, 15, 8, 0, tzinfo=ET),
                polling_interval=timedelta(minutes=15),
            ),
            ingest_time_source=IngestSource.SIMULATED,
        )
        assert_ingest_integrity([record], datetime(2025, 12, 31, tzinfo=ET))

    def test_observed_within_study_period_passes(self):
        record = _record("live", datetime(2026, 8, 17, 8, 0, tzinfo=ET))
        assert_ingest_integrity([record], datetime(2026, 12, 31, tzinfo=ET))

    def test_simulated_ingest_is_conservative_not_instant(self):
        publish = datetime(2020, 3, 15, 8, 0, tzinfo=ET)
        assert simulated_ingest_time(
            publish, polling_interval=timedelta(minutes=15)
        ) == publish + timedelta(minutes=15)

    def test_negative_polling_interval_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            simulated_ingest_time(
                datetime(2020, 3, 15, 8, 0, tzinfo=ET),
                polling_interval=-timedelta(minutes=1),
            )

    def test_gap_summary_reports_simulated_share(self):
        live = _record("live", datetime(2026, 8, 17, 8, 0, tzinfo=ET))
        published = datetime(2026, 8, 18, 8, 0, tzinfo=ET)
        backfilled = TextRecord(
            doc_id="hist",
            symbol="AAPL",
            publish_time=published,
            ingest_time=simulated_ingest_time(
                published, polling_interval=timedelta(minutes=15)
            ),
            ingest_time_source=IngestSource.SIMULATED,
        ).resolve(TEST_CAL, research=False)
        summary = gap_summary([live, backfilled])
        assert summary["simulated_ingest_share"] == pytest.approx(0.5)
