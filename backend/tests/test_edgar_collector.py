"""EDGAR collector tests.

The property under protection: live collection produces OBSERVED receipt
times, backfill produces SIMULATED ones, and neither mode can accidentally
produce the other's label.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.text_signals.edgar_collector import (
    DEFAULT_BACKFILL_POLLING_INTERVAL,
    EdgarCollector,
    RawFiling,
    provenance_report,
)
from app.text_signals.timestamps import (
    IngestSource,
    assert_ingest_integrity,
)

ET = ZoneInfo("America/New_York")


def _filing(
    accession: str,
    accepted: datetime,
    *,
    form_type: str = "10-K",
    symbol: str = "AAPL",
) -> RawFiling:
    return RawFiling(
        accession_number=accession,
        cik="0000320193",
        symbol=symbol,
        form_type=form_type,
        acceptance_datetime=accepted,
    )


FIXTURE = [
    _filing("0001-10K", datetime(2026, 8, 14, 16, 30, tzinfo=ET)),
    _filing("0002-10Q", datetime(2026, 8, 14, 17, 5, tzinfo=ET), form_type="10-Q"),
    _filing("0003-10K", datetime(2026, 8, 17, 8, 0, tzinfo=ET), symbol="MSFT"),
]


def _fetcher(filings):
    def fetch(start, end):
        return [f for f in filings if start <= f.acceptance_datetime <= end]

    return fetch


class TestLiveCollection:
    def test_live_records_are_observed(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=ET)
        collector = EdgarCollector(_fetcher(FIXTURE), clock=lambda: now)
        records = collector.poll(datetime(2026, 8, 10, tzinfo=ET))
        assert records
        assert all(r.ingest_time_source is IngestSource.OBSERVED for r in records)

    def test_live_ingest_time_is_the_clock_not_the_filing(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=ET)
        collector = EdgarCollector(_fetcher(FIXTURE), clock=lambda: now)
        records = collector.poll(datetime(2026, 8, 10, tzinfo=ET))
        assert all(r.ingest_time == now for r in records)

    def test_observed_records_pass_integrity_within_the_period(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=ET)
        collector = EdgarCollector(_fetcher(FIXTURE), clock=lambda: now)
        records = collector.poll(datetime(2026, 8, 10, tzinfo=ET))
        assert_ingest_integrity(records, datetime(2026, 12, 31, tzinfo=ET))


class TestBackfill:
    def test_backfill_records_are_simulated(self):
        collector = EdgarCollector(_fetcher(FIXTURE))
        records = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 20, tzinfo=ET)
        )
        assert records
        assert all(r.ingest_time_source is IngestSource.SIMULATED for r in records)

    def test_backfill_ingest_lags_publish_by_the_polling_interval(self):
        collector = EdgarCollector(_fetcher(FIXTURE))
        records = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 20, tzinfo=ET)
        )
        for record in records:
            assert record.ingest_time == (
                record.publish_time + DEFAULT_BACKFILL_POLLING_INTERVAL
            )

    def test_backfill_survives_integrity_check_on_a_past_period(self):
        """The point: honest labelling makes a historical study admissible."""
        collector = EdgarCollector(_fetcher(FIXTURE))
        records = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 20, tzinfo=ET)
        )
        assert_ingest_integrity(records, datetime(2026, 8, 20, tzinfo=ET))

    def test_polling_interval_is_configurable_and_moves_ingest(self):
        collector = EdgarCollector(_fetcher(FIXTURE))
        slow = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET),
            datetime(2026, 8, 20, tzinfo=ET),
            polling_interval=timedelta(hours=6),
        )
        assert slow[0].ingest_time == slow[0].publish_time + timedelta(hours=6)


class TestFormFiltering:
    def test_defaults_to_10k_only(self):
        collector = EdgarCollector(_fetcher(FIXTURE))
        records = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 20, tzinfo=ET)
        )
        assert {r.doc_id for r in records} == {"0001-10K", "0003-10K"}

    def test_form_types_can_be_widened(self):
        collector = EdgarCollector(_fetcher(FIXTURE), form_types=("10-K", "10-Q"))
        records = collector.backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 20, tzinfo=ET)
        )
        assert len(records) == 3


class TestProvenanceReport:
    def test_mixed_corpus_reports_observed_share(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=ET)
        live = EdgarCollector(
            _fetcher([FIXTURE[2]]), clock=lambda: now
        ).poll(datetime(2026, 8, 16, tzinfo=ET))
        hist = EdgarCollector(_fetcher([FIXTURE[0]])).backfill(
            datetime(2026, 8, 10, tzinfo=ET), datetime(2026, 8, 15, tzinfo=ET)
        )
        report = provenance_report(live + hist)
        assert report["n_records"] == 2
        assert report["n_observed"] == 1
        assert report["n_simulated"] == 1
        assert report["observed_share"] == pytest.approx(0.5)

    def test_empty_corpus_reports_none_not_zero_share(self):
        report = provenance_report([])
        assert report["n_records"] == 0
        assert report["observed_share"] is None


class TestTimezoneDiscipline:
    def test_naive_window_is_rejected(self):
        collector = EdgarCollector(_fetcher(FIXTURE))
        with pytest.raises(ValueError, match="naive datetime"):
            collector.backfill(datetime(2026, 8, 10), datetime(2026, 8, 20))
