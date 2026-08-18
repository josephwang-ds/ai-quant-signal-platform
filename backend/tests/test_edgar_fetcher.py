"""EDGAR fetcher tests.

Everything here runs offline against saved, *real* submissions payloads in
``tests/fixtures/edgar``. The one test that touches the network is marked
``live`` and is excluded from the default run by ``pytest.ini``.

The load-bearing test in this file is
:class:`TestAcceptanceIsUtcNotEastern`. It re-derives, from real data, the
claim that ``acceptanceDateTime`` is UTC — the assumption every downstream
timestamp rests on, and the one a reasonable person would get wrong.
"""

from __future__ import annotations

import os

import gzip
import json
import zlib
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.text_signals.edgar_collector import EdgarCollector, RawFiling
from app.text_signals.edgar_fetcher import (
    EdgarParseError,
    EdgarSubmissionsFetcher,
    FilesystemFilingCache,
    RateLimiter,
    SecUserAgent,
    SecUserAgentError,
    SymbolResolutionError,
    decode_body,
    parse_acceptance_datetime,
)
from app.text_signals.timestamps import IngestSource

ET = ZoneInfo("America/New_York")
UTC = timezone.utc

FIXTURES = Path(__file__).parent / "fixtures" / "edgar"
AAPL_CIK = 320193
MSFT_CIK = 789019

UA = SecUserAgent(name="Research Bot", email="research@example.com")

#: SEC dates a submission to the next business day when it is accepted after
#: this instant. Section 16 forms (3/4/5) are exempt and are excluded wherever
#: this constant is used.
SEC_FILING_DATE_CUTOFF = time(17, 30)
SECTION_16_FORMS = {"3", "4", "5"}


def _fixture_http(calls: list[str] | None = None):
    """Serve saved submissions payloads; record every URL requested."""

    def http_get(url: str, headers):
        assert "User-Agent" in headers, "SEC refuses requests without a User-Agent"
        if calls is not None:
            calls.append(url)
        name = url.rsplit("/", 1)[-1]
        path = FIXTURES / name
        if not path.exists():
            raise AssertionError(f"unexpected URL requested: {url}")
        return path.read_bytes()

    return http_get


def _load(cik: int) -> dict:
    return json.loads((FIXTURES / f"CIK{cik:010d}.json").read_text())


def _rows(cik: int) -> list[dict]:
    recent = _load(cik)["filings"]["recent"]
    return [
        {k: recent[k][i] for k in recent}
        for i in range(len(recent["accessionNumber"]))
    ]


class TestSecUserAgent:
    def test_header_is_name_then_email(self):
        assert SecUserAgent("Jane Doe", "jane@example.com").header == (
            "Jane Doe jane@example.com"
        )

    @pytest.mark.parametrize("email", ["", "not-an-email", "a@b", "a b@c.com"])
    def test_malformed_email_rejected(self, email):
        with pytest.raises(SecUserAgentError):
            SecUserAgent("Jane Doe", email)

    @pytest.mark.parametrize("name", ["", "   "])
    def test_empty_name_rejected(self, name):
        with pytest.raises(SecUserAgentError):
            SecUserAgent(name, "jane@example.com")

    def test_fetcher_refuses_a_bare_string(self):
        """A string would format fine and still be an undeclared client."""
        with pytest.raises(SecUserAgentError):
            EdgarSubmissionsFetcher([AAPL_CIK], "Jane jane@example.com")  # type: ignore[arg-type]


class TestAcceptanceParsing:
    def test_z_suffix_is_utc_and_converts_to_eastern(self):
        parsed = parse_acceptance_datetime("2016-10-26T20:42:16.000Z")
        assert parsed == datetime(2016, 10, 26, 16, 42, 16, tzinfo=ET)

    def test_explicit_offset_accepted(self):
        assert parse_acceptance_datetime("2016-10-26T20:42:16+00:00") == (
            datetime(2016, 10, 26, 16, 42, 16, tzinfo=ET)
        )

    def test_naive_value_is_rejected_not_assumed_utc(self):
        """An absent offset means the upstream format changed. Stop, don't guess."""
        with pytest.raises(EdgarParseError, match="no UTC offset"):
            parse_acceptance_datetime("2016-10-26T20:42:16")

    @pytest.mark.parametrize("raw", ["", "   ", "not-a-date", "2016-13-45T99:99:99Z"])
    def test_unparseable_values_rejected(self, raw):
        with pytest.raises(EdgarParseError):
            parse_acceptance_datetime(raw)


class TestAcceptanceIsUtcNotEastern:
    """Re-derive the UTC claim from real data, on every run.

    EDGAR is an Eastern-time system whose filing-date rule is published in
    Eastern time, so reading ``acceptanceDateTime``'s wall clock as ET is the
    natural assumption. It is wrong, and being wrong shifts every document by
    four or five hours — enough to move an after-hours filing across a session
    boundary and change which day it could first be traded on.

    The discriminator is SEC's own rule: accepted after 17:30 ET, dated the
    next business day.
    """

    @staticmethod
    def _predict_filing_date(moment_et: datetime) -> date:
        if moment_et.time() <= SEC_FILING_DATE_CUTOFF:
            return moment_et.date()
        nxt = moment_et.date() + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        return nxt

    def _score(self, cik: int) -> tuple[int, int, int, int]:
        """(utc_hits, utc_misses, eastern_hits, eastern_misses)."""
        utc_hits = utc_miss = et_hits = et_miss = 0
        for row in _rows(cik):
            form = str(row.get("form") or "")
            raw = row.get("acceptanceDateTime")
            filed = row.get("filingDate")
            if form in SECTION_16_FORMS or not raw or not filed:
                continue
            naive = datetime.strptime(str(raw), "%Y-%m-%dT%H:%M:%S.%fZ")
            actual = date.fromisoformat(str(filed))

            as_utc = naive.replace(tzinfo=UTC).astimezone(ET)
            as_eastern = naive.replace(tzinfo=ET)

            if self._predict_filing_date(as_utc) == actual:
                utc_hits += 1
            else:
                utc_miss += 1
            if self._predict_filing_date(as_eastern) == actual:
                et_hits += 1
            else:
                et_miss += 1
        return utc_hits, utc_miss, et_hits, et_miss

    @pytest.mark.parametrize("cik", [AAPL_CIK, MSFT_CIK])
    def test_utc_reading_predicts_sec_filing_dates_far_better(self, cik):
        utc_hits, utc_miss, et_hits, et_miss = self._score(cik)
        assert utc_hits + utc_miss > 0, "fixture has no forms subject to the cutoff"
        # Not a marginal preference: the wrong reading should fail loudly.
        assert utc_hits > et_hits
        assert utc_hits >= 0.9 * (utc_hits + utc_miss)
        assert et_miss > utc_miss

    def test_the_single_discriminating_filing(self):
        """One row where the two readings genuinely disagree.

        Apple's FY2016 10-K: accepted 20:42Z, dated the *same* day. Only the
        UTC reading (16:42 ET, before the cutoff) explains that.
        """
        row = next(
            r
            for r in _rows(AAPL_CIK)
            if r["accessionNumber"] == "0001628280-16-020309"
        )
        assert row["acceptanceDateTime"] == "2016-10-26T20:42:16.000Z"
        assert row["filingDate"] == "2016-10-26"

        parsed = parse_acceptance_datetime(row["acceptanceDateTime"])
        assert parsed.time() < SEC_FILING_DATE_CUTOFF
        assert parsed.date() == date.fromisoformat(row["filingDate"])

        misread_as_eastern = datetime(2016, 10, 26, 20, 42, 16, tzinfo=ET)
        assert misread_as_eastern.time() > SEC_FILING_DATE_CUTOFF  # would misdate


class TestResponseDecoding:
    """Regression cover for a bug only the live path could surface.

    The fixture transport is injected, so it never exercises real HTTP. The
    default transport asks for gzip — as SEC requests, to spare their
    bandwidth — but ``urllib`` does not decompress the reply, so parsing the
    raw bytes failed with what looked like an upstream format change.
    """

    def test_gzip_body_is_decompressed(self):
        payload = json.dumps({"cik": "0000320193"}).encode()
        assert decode_body(gzip.compress(payload), "gzip") == payload

    def test_deflate_body_is_decompressed(self):
        payload = b'{"cik": "0000320193"}'
        assert decode_body(zlib.compress(payload), "deflate") == payload

    def test_raw_deflate_without_zlib_wrapper_is_decompressed(self):
        payload = b'{"cik": "0000320193"}'
        compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        raw = compressor.compress(payload) + compressor.flush()
        assert decode_body(raw, "deflate") == payload

    @pytest.mark.parametrize("encoding", [None, "", "identity"])
    def test_uncompressed_body_passes_through(self, encoding):
        payload = b'{"cik": "0000320193"}'
        assert decode_body(payload, encoding) == payload

    def test_gzipped_submissions_payload_parses_end_to_end(self):
        """The precise failure: compressed bytes reaching json.loads."""
        source = (FIXTURES / f"CIK{AAPL_CIK:010d}.json").read_bytes()

        def gzip_http(url, headers):
            return decode_body(gzip.compress(source), "gzip")

        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=gzip_http, include_archives=False
        )
        results = fetcher(
            datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET)
        )
        assert results


class TestRateLimiter:
    def test_waits_between_consecutive_requests(self):
        now = [0.0]
        slept: list[float] = []
        limiter = RateLimiter(
            timedelta(milliseconds=150),
            clock=lambda: now[0],
            sleep=lambda s: (slept.append(s), now.__setitem__(0, now[0] + s)),
        )
        limiter.acquire()
        limiter.acquire()
        assert slept and slept[0] == pytest.approx(0.15)

    def test_no_wait_when_caller_was_already_slow(self):
        now = [0.0]
        slept: list[float] = []
        limiter = RateLimiter(
            timedelta(milliseconds=150),
            clock=lambda: now[0],
            sleep=lambda s: slept.append(s),
        )
        limiter.acquire()
        now[0] = 5.0
        limiter.acquire()
        assert slept == []

    def test_negative_interval_rejected(self):
        with pytest.raises(ValueError):
            RateLimiter(timedelta(seconds=-1))

    def test_fetcher_rate_limits_every_request(self):
        calls: list[str] = []
        acquired = []
        limiter = RateLimiter(
            timedelta(0), clock=lambda: 0.0, sleep=lambda s: acquired.append(s)
        )
        original = limiter.acquire

        def counting_acquire():
            acquired.append(0.0)
            original()

        limiter.acquire = counting_acquire  # type: ignore[method-assign]
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=_fixture_http(calls), rate_limiter=limiter
        )
        fetcher(datetime(2024, 1, 1, tzinfo=ET), datetime(2026, 1, 1, tzinfo=ET))
        assert len(acquired) == len(calls) == 1


class TestWindowingAndFiltering:
    def _fetch(self, start, end, **kwargs):
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=_fixture_http(), **kwargs
        )
        return fetcher(start, end)

    def test_only_filings_inside_the_window_are_returned(self):
        results = self._fetch(
            datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET)
        )
        assert results
        assert all(r.acceptance_datetime.year == 2023 for r in results)

    def test_results_are_sorted_by_acceptance(self):
        results = self._fetch(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        stamps = [r.acceptance_datetime for r in results]
        assert stamps == sorted(stamps)

    def test_form_filter_is_opt_in(self):
        everything = self._fetch(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        tenks = self._fetch(
            datetime(2015, 1, 1, tzinfo=ET),
            datetime(2026, 12, 31, tzinfo=ET),
            form_types=("10-K",),
        )
        assert {r.form_type for r in tenks} == {"10-K"}
        assert len(tenks) < len(everything)

    def test_symbol_comes_from_the_payload(self):
        results = self._fetch(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        assert {r.symbol for r in results} == {"AAPL"}

    def test_cik_is_zero_padded(self):
        results = self._fetch(
            datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET)
        )
        assert all(r.cik == "0000320193" for r in results)

    def test_document_url_points_at_the_primary_document(self):
        results = self._fetch(
            datetime(2025, 1, 1, tzinfo=ET),
            datetime(2026, 12, 31, tzinfo=ET),
            form_types=("10-K",),
        )
        assert results
        url = results[0].document_url
        assert url is not None
        assert url.startswith("https://www.sec.gov/Archives/edgar/data/320193/")
        assert "-" not in url.rsplit("/", 2)[1]  # accession stripped of dashes

    def test_naive_window_rejected(self):
        with pytest.raises(ValueError, match="naive datetime"):
            self._fetch(datetime(2023, 1, 1), datetime(2023, 12, 31))

    def test_backwards_window_rejected(self):
        with pytest.raises(ValueError, match="start must not be after end"):
            self._fetch(
                datetime(2024, 1, 1, tzinfo=ET), datetime(2023, 1, 1, tzinfo=ET)
            )

    def test_multiple_ciks_are_merged_and_sorted(self):
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK, MSFT_CIK], UA, http_get=_fixture_http()
        )
        results = fetcher(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        assert {r.symbol for r in results} == {"AAPL", "MSFT"}
        stamps = [r.acceptance_datetime for r in results]
        assert stamps == sorted(stamps)


class TestArchivePagination:
    def test_archive_pages_outside_the_window_are_not_requested(self):
        """Apple's archive page covers 1994-01-26..2015-06-02.

        A 2023 window cannot intersect it, so it must not be fetched. The
        archive fixture *is* present, so this asserts the window check —
        not merely that a missing file went unread. Each skip is a real
        request saved against SEC's rate limit.
        """
        calls: list[str] = []
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=_fixture_http(calls)
        )
        fetcher(datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET))
        assert len(calls) == 1
        assert all("submissions-001" not in url for url in calls)

    def test_overlapping_archive_page_is_requested(self):
        calls: list[str] = []

        def http_get(url, headers):
            calls.append(url)
            name = url.rsplit("/", 1)[-1]
            if name == "CIK0000320193-submissions-001.json":
                return json.dumps({"accessionNumber": [], "form": []}).encode()
            return (FIXTURES / name).read_bytes()

        fetcher = EdgarSubmissionsFetcher([AAPL_CIK], UA, http_get=http_get)
        fetcher(datetime(2000, 1, 1, tzinfo=ET), datetime(2001, 1, 1, tzinfo=ET))
        assert any("submissions-001" in url for url in calls)

    def test_archives_can_be_disabled(self):
        calls: list[str] = []
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=_fixture_http(calls), include_archives=False
        )
        fetcher(datetime(2000, 1, 1, tzinfo=ET), datetime(2001, 1, 1, tzinfo=ET))
        assert len(calls) == 1


class TestFilingCache:
    def test_roundtrip_preserves_the_record(self, tmp_path):
        cache = FilesystemFilingCache(tmp_path)
        filing = RawFiling(
            accession_number="0000320193-23-000106",
            cik="0000320193",
            symbol="AAPL",
            form_type="10-K",
            acceptance_datetime=datetime(2023, 11, 2, 18, 8, 27, tzinfo=ET),
            filing_date=datetime(2023, 11, 3),
            document_url="https://example.invalid/doc.htm",
        )
        cache.put(filing)
        restored = cache.get("0000320193-23-000106")
        assert restored == filing

    def test_missing_entry_returns_none(self, tmp_path):
        assert FilesystemFilingCache(tmp_path).get("0000000000-00-000000") is None

    def test_cached_record_wins_over_a_restated_payload(self, tmp_path):
        """The reproducibility guarantee: an existing record does not drift."""
        cache = FilesystemFilingCache(tmp_path)
        fetcher = EdgarSubmissionsFetcher(
            [AAPL_CIK], UA, http_get=_fixture_http(), cache=cache
        )
        window = (datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET))
        first = fetcher(*window)
        assert first

        # SEC restates an acceptance time under the same accession number.
        target = first[0]
        cache.put(
            RawFiling(
                accession_number=target.accession_number,
                cik=target.cik,
                symbol=target.symbol,
                form_type=target.form_type,
                acceptance_datetime=target.acceptance_datetime + timedelta(hours=3),
                filing_date=target.filing_date,
                document_url=target.document_url,
            )
        )
        second = {f.accession_number: f for f in fetcher(*window)}
        assert second[target.accession_number].acceptance_datetime == (
            target.acceptance_datetime + timedelta(hours=3)
        ), "cache must be authoritative once a record exists"

    def test_accession_number_cannot_escape_the_cache_directory(self, tmp_path):
        cache = FilesystemFilingCache(tmp_path / "cache")
        cache.put(
            RawFiling(
                accession_number="../../etc/passwd",
                cik="0000320193",
                symbol="AAPL",
                form_type="10-K",
                acceptance_datetime=datetime(2023, 11, 2, 18, 8, tzinfo=ET),
            )
        )
        written = list((tmp_path / "cache").glob("*.json"))
        assert len(written) == 1
        assert written[0].parent == tmp_path / "cache"


class TestSymbolResolution:
    def test_missing_ticker_raises_rather_than_emitting_a_blank_symbol(self, tmp_path):
        payload = {"cik": "0000000001", "tickers": [], "filings": {"recent": {}}}
        path = FIXTURES / "CIK0000000001.json"
        path.write_text(json.dumps(payload))
        try:
            fetcher = EdgarSubmissionsFetcher([1], UA, http_get=_fixture_http())
            with pytest.raises(SymbolResolutionError):
                fetcher(datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET))
        finally:
            path.unlink()

    def test_override_supplies_the_mapping(self):
        payload = {"cik": "0000000001", "tickers": [], "filings": {"recent": {}}}
        path = FIXTURES / "CIK0000000001.json"
        path.write_text(json.dumps(payload))
        try:
            fetcher = EdgarSubmissionsFetcher(
                [1], UA, http_get=_fixture_http(), symbol_overrides={"1": "PRIV"}
            )
            assert fetcher(
                datetime(2023, 1, 1, tzinfo=ET), datetime(2023, 12, 31, tzinfo=ET)
            ) == []
        finally:
            path.unlink()


class TestCollectorIntegration:
    """The point of A1: this fetcher drops into the existing collector."""

    def test_backfill_through_the_real_fetcher_is_simulated(self):
        fetcher = EdgarSubmissionsFetcher([AAPL_CIK], UA, http_get=_fixture_http())
        collector = EdgarCollector(fetcher)
        records = collector.backfill(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        assert records
        assert all(r.ingest_time_source is IngestSource.SIMULATED for r in records)
        assert all(r.source == "edgar:10-K" for r in records)

    def test_poll_through_the_real_fetcher_is_observed(self):
        now = datetime(2026, 12, 31, 9, 0, tzinfo=ET)
        fetcher = EdgarSubmissionsFetcher([AAPL_CIK], UA, http_get=_fixture_http())
        collector = EdgarCollector(fetcher, clock=lambda: now)
        records = collector.poll(datetime(2015, 1, 1, tzinfo=ET), now)
        assert records
        assert all(r.ingest_time_source is IngestSource.OBSERVED for r in records)

    def test_collector_form_filter_still_governs(self):
        fetcher = EdgarSubmissionsFetcher([AAPL_CIK], UA, http_get=_fixture_http())
        records = EdgarCollector(fetcher, form_types=("10-Q",)).backfill(
            datetime(2015, 1, 1, tzinfo=ET), datetime(2026, 12, 31, tzinfo=ET)
        )
        assert records
        assert all(r.source == "edgar:10-Q" for r in records)


@pytest.mark.live
class TestLiveEdgar:
    """Excluded from the default run by ``addopts = -m "not live"``."""

    def test_real_submissions_payload_still_has_the_expected_shape(self):
        # SEC requires a real contact, so the live tests take one from the
        # environment rather than baking a personal address into a public repo.
        name = os.environ.get("SEC_UA_NAME")
        email = os.environ.get("SEC_UA_EMAIL")
        if not name or not email:
            pytest.skip("set SEC_UA_NAME and SEC_UA_EMAIL to run live SEC tests")
        ua = SecUserAgent(name=name, email=email)
        fetcher = EdgarSubmissionsFetcher([AAPL_CIK], ua, form_types=("10-K",))
        results = fetcher(
            datetime(2023, 1, 1, tzinfo=ET), datetime(2024, 12, 31, tzinfo=ET)
        )
        assert results
        assert all(r.form_type == "10-K" for r in results)
        assert all(r.symbol == "AAPL" for r in results)
        assert all(r.acceptance_datetime.tzinfo is not None for r in results)
