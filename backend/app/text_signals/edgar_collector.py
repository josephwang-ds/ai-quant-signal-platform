"""EDGAR filing collection, in two modes that must never be confused.

**Live** — a collector polls EDGAR and records receipt as it happens. Every
record it produces carries ``IngestSource.OBSERVED``, and that label is true.

**Backfill** — historical filings are downloaded long after the fact. Receipt
time is reconstructed from publish time plus an assumed polling interval, and
every record carries ``IngestSource.SIMULATED``.

Both are legitimate. Only one is a measurement. The point of this module is
that the mode is chosen explicitly at the call site and travels with the data,
so a downstream reader never has to guess which one produced a number.

Network access is injected rather than imported, so the collection logic is
tested deterministically against fixtures. Any real fetcher must send an SEC
declared User-Agent (``Name email``) or requests will be refused.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.text_signals.timestamps import (
    IngestSource,
    TextRecord,
    simulated_ingest_time,
)

MARKET_TZ = ZoneInfo("America/New_York")

#: Assumed poll cadence when reconstructing receipt for historical filings.
#: Conservative: a collector on this cadence sees a filing at worst this long
#: after acceptance. Pre-register it with the hypothesis.
DEFAULT_BACKFILL_POLLING_INTERVAL = timedelta(minutes=15)

#: Forms worth collecting for filing-change research. 10-K first: annual
#: filings are the ones firms copy forward year over year, which is the
#: behaviour the change signal is built on.
DEFAULT_FORM_TYPES = ("10-K",)


@dataclass(frozen=True)
class RawFiling:
    """One filing as reported by EDGAR, before any research interpretation.

    ``acceptance_datetime`` is the authoritative public instant. It is not the
    same as EDGAR's ``filing_date``: a submission accepted after 17:30 ET is
    *dated* the next business day, while the document itself became visible at
    acceptance. Research must use acceptance; using filing_date silently
    shifts a document by up to a day.
    """

    accession_number: str
    cik: str
    symbol: str
    form_type: str
    acceptance_datetime: datetime
    filing_date: datetime | None = None
    document_url: str | None = None


#: Injected network boundary: given a window, return the filings in it.
FilingFetcher = Callable[[datetime, datetime], Iterable[RawFiling]]

#: Injected clock, so live collection is testable.
Clock = Callable[[], datetime]


def _ensure_market_tz(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("naive datetime rejected; EDGAR times are ET-aware")
    return moment.astimezone(MARKET_TZ)


class EdgarCollector:
    """Turns raw filings into research records with honest provenance."""

    def __init__(
        self,
        fetcher: FilingFetcher,
        *,
        clock: Clock | None = None,
        form_types: Sequence[str] = DEFAULT_FORM_TYPES,
    ) -> None:
        self._fetcher = fetcher
        self._clock = clock or (lambda: datetime.now(MARKET_TZ))
        self._form_types = tuple(form_types)

    def _accepted(self, filing: RawFiling) -> bool:
        return not self._form_types or filing.form_type in self._form_types

    def poll(self, since: datetime, until: datetime | None = None) -> list[TextRecord]:
        """Live collection. Receipt time is measured, so OBSERVED is truthful.

        Call this on a schedule starting now. Even a few months of genuinely
        observed receipt times gives a short sample where the availability
        claim rests on measurement rather than on an assumption — which no
        amount of backfilling can produce retroactively.
        """
        window_start = _ensure_market_tz(since)
        window_end = _ensure_market_tz(until) if until else self._clock()

        records: list[TextRecord] = []
        for filing in self._fetcher(window_start, window_end):
            if not self._accepted(filing):
                continue
            received_at = self._clock()
            records.append(
                TextRecord(
                    doc_id=filing.accession_number,
                    symbol=filing.symbol,
                    publish_time=_ensure_market_tz(filing.acceptance_datetime),
                    ingest_time=received_at,
                    ingest_time_source=IngestSource.OBSERVED,
                    source=f"edgar:{filing.form_type}",
                )
            )
        return records

    def backfill(
        self,
        since: datetime,
        until: datetime,
        *,
        polling_interval: timedelta = DEFAULT_BACKFILL_POLLING_INTERVAL,
    ) -> list[TextRecord]:
        """Historical collection. Receipt time is reconstructed, so SIMULATED.

        The counterfactual is defensible for EDGAR specifically: the index is
        public and continuously updated, so a collector on this cadence really
        would have seen the filing within one interval. That does not make it
        an observation.
        """
        window_start = _ensure_market_tz(since)
        window_end = _ensure_market_tz(until)

        records: list[TextRecord] = []
        for filing in self._fetcher(window_start, window_end):
            if not self._accepted(filing):
                continue
            published = _ensure_market_tz(filing.acceptance_datetime)
            records.append(
                TextRecord(
                    doc_id=filing.accession_number,
                    symbol=filing.symbol,
                    publish_time=published,
                    ingest_time=simulated_ingest_time(
                        published, polling_interval=polling_interval
                    ),
                    ingest_time_source=IngestSource.SIMULATED,
                    source=f"edgar:{filing.form_type}",
                )
            )
        return records


def provenance_report(records: Sequence[TextRecord]) -> dict[str, int | float | None]:
    """Counts by ingest provenance, for the evidence package.

    A study that is 100% simulated is not disqualified — it is *described*.
    The number belongs next to the result, not in a footnote.
    """
    total = len(records)
    if total == 0:
        return {
            "n_records": 0,
            "n_observed": 0,
            "n_simulated": 0,
            "observed_share": None,
        }
    observed = sum(r.ingest_time_source is IngestSource.OBSERVED for r in records)
    return {
        "n_records": total,
        "n_observed": observed,
        "n_simulated": total - observed,
        "observed_share": observed / total,
    }
