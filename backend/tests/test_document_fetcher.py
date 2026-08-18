"""Filing document retrieval tests.

Offline throughout: the HTTP boundary is injected, and the bodies served are
the same trimmed real 10-K fixtures the extractor tests use. One live test is
marked ``live`` and excluded from the default run.
"""

from __future__ import annotations

import os

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.text_signals.document_fetcher import (
    DocumentUnavailableError,
    FilesystemDocumentCache,
    FilingDocumentFetcher,
)
from app.text_signals.edgar_collector import RawFiling
from app.text_signals.edgar_fetcher import EdgarHttpError, RateLimiter, SecUserAgent
from app.text_signals.section_extraction import extract_risk_factors

ET = ZoneInfo("America/New_York")
FIXTURES = Path(__file__).parent / "fixtures" / "tenk"
UA = SecUserAgent(name="Research Bot", email="research@example.com")

DOC_URL = (
    "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/"
    "aapl-20230930.htm"
)


def _filing(url: str | None = DOC_URL) -> RawFiling:
    return RawFiling(
        accession_number="0000320193-23-000106",
        cik="0000320193",
        symbol="AAPL",
        form_type="10-K",
        acceptance_datetime=datetime(2023, 11, 2, 18, 8, 27, tzinfo=ET),
        document_url=url,
    )


def _serving(path: Path, calls: list[str] | None = None):
    body = path.read_bytes()

    def http_get(url, headers):
        assert "User-Agent" in headers, "SEC refuses undeclared clients"
        if calls is not None:
            calls.append(url)
        return body

    return http_get


class TestRetrieval:
    def test_fetches_and_reports_provenance(self):
        fetcher = FilingDocumentFetcher(
            UA, http_get=_serving(FIXTURES / "aapl-10k-2023.htm")
        )
        doc = fetcher.fetch(_filing())
        assert doc.accession_number == "0000320193-23-000106"
        assert doc.symbol == "AAPL"
        assert doc.url == DOC_URL
        assert doc.byte_length > 10_000
        assert doc.from_cache is False

    def test_retrieved_document_feeds_the_extractor(self):
        """The A2 handoff in one assertion: URL in, Item 1A text out."""
        fetcher = FilingDocumentFetcher(
            UA, http_get=_serving(FIXTURES / "aapl-10k-2023.htm")
        )
        doc = fetcher.fetch(_filing())
        section = extract_risk_factors(doc.markup)
        assert section.ok, section.unavailable_reason
        assert section.char_count > 5_000

    def test_user_agent_is_required(self):
        with pytest.raises(TypeError):
            FilingDocumentFetcher("Research Bot research@example.com")  # type: ignore[arg-type]

    def test_rate_limiter_is_consulted(self):
        acquired: list[int] = []
        limiter = RateLimiter(clock=lambda: 0.0, sleep=lambda s: None)
        original = limiter.acquire
        limiter.acquire = lambda: (acquired.append(1), original())  # type: ignore[method-assign]
        fetcher = FilingDocumentFetcher(
            UA,
            http_get=_serving(FIXTURES / "aapl-10k-2023.htm"),
            rate_limiter=limiter,
        )
        fetcher.fetch(_filing())
        assert len(acquired) == 1


class TestRefusals:
    def test_missing_document_url_raises_rather_than_returning_empty(self):
        """An empty body would look downstream like a total rewrite of the filing."""
        fetcher = FilingDocumentFetcher(UA, http_get=_serving(FIXTURES / "aapl-10k-2023.htm"))
        with pytest.raises(DocumentUnavailableError, match="no primary document URL"):
            fetcher.fetch(_filing(url=None))

    def test_off_archive_url_is_refused(self):
        fetcher = FilingDocumentFetcher(UA, http_get=_serving(FIXTURES / "aapl-10k-2023.htm"))
        with pytest.raises(DocumentUnavailableError, match="off-archive"):
            fetcher.fetch(_filing(url="https://example.invalid/evil.htm"))

    def test_empty_body_is_refused(self):
        fetcher = FilingDocumentFetcher(UA, http_get=lambda u, h: b"   ")
        with pytest.raises(DocumentUnavailableError, match="empty document body"):
            fetcher.fetch(_filing())

    def test_http_failure_is_wrapped(self):
        def boom(url, headers):
            raise EdgarHttpError("EDGAR returned HTTP 403")

        fetcher = FilingDocumentFetcher(UA, http_get=boom)
        with pytest.raises(DocumentUnavailableError, match="403"):
            fetcher.fetch(_filing())


class TestCache:
    def test_second_fetch_is_served_from_disk(self, tmp_path):
        calls: list[str] = []
        cache = FilesystemDocumentCache(tmp_path)
        fetcher = FilingDocumentFetcher(
            UA,
            http_get=_serving(FIXTURES / "aapl-10k-2023.htm", calls),
            cache=cache,
        )
        first = fetcher.fetch(_filing())
        second = fetcher.fetch(_filing())

        assert first.from_cache is False
        assert second.from_cache is True
        assert len(calls) == 1, "cached fetch must not hit the network"
        assert second.markup == first.markup

    def test_cache_makes_the_corpus_reproducible(self, tmp_path):
        """A filing is immutable once accepted; a re-run must see the same bytes."""
        cache = FilesystemDocumentCache(tmp_path)
        FilingDocumentFetcher(
            UA, http_get=_serving(FIXTURES / "aapl-10k-2023.htm"), cache=cache
        ).fetch(_filing())

        # SEC now serves something different under the same accession number.
        drifted = FilingDocumentFetcher(
            UA, http_get=lambda u, h: b"<html><body>replaced</body></html>", cache=cache
        ).fetch(_filing())
        assert drifted.from_cache is True
        assert "replaced" not in drifted.markup

    def test_accession_number_cannot_escape_the_cache_directory(self, tmp_path):
        cache = FilesystemDocumentCache(tmp_path / "docs")
        cache.put("../../etc/passwd", "<html></html>")
        written = list((tmp_path / "docs").glob("*.html"))
        assert len(written) == 1
        assert written[0].parent == tmp_path / "docs"

    def test_missing_entry_returns_none(self, tmp_path):
        assert FilesystemDocumentCache(tmp_path).get("0000000000-00-000000") is None


@pytest.mark.live
class TestLiveDocumentRetrieval:
    """Excluded from the default run by ``addopts = -m "not live"``."""

    def test_real_apple_10k_yields_risk_factors(self):
        # SEC requires a real contact, so the live tests take one from the
        # environment rather than baking a personal address into a public repo.
        name = os.environ.get("SEC_UA_NAME")
        email = os.environ.get("SEC_UA_EMAIL")
        if not name or not email:
            pytest.skip("set SEC_UA_NAME and SEC_UA_EMAIL to run live SEC tests")
        ua = SecUserAgent(name=name, email=email)
        doc = FilingDocumentFetcher(ua).fetch(_filing())
        assert doc.byte_length > 100_000
        section = extract_risk_factors(doc.markup)
        assert section.ok, section.unavailable_reason
        assert section.char_count > 20_000
        assert "unresolved staff comments" not in section.text.lower()
