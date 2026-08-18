"""Retrieve the primary document of a filing.

``edgar_fetcher`` resolves the submissions *index* — which filings exist and
when they became public. This module fetches the filing's actual document, the
thing the text signal is computed from.

They are separate modules because they are separate resources with different
costs: an index response is tens of kilobytes and changes as filings arrive,
while a modern inline-XBRL 10-K is several megabytes and never changes once
accepted. That difference is why documents are cached on disk by accession
number and the index is not.

Transport primitives (declared User-Agent, rate limiting, gzip handling) are
reused from ``edgar_fetcher`` rather than reimplemented, so there is one place
where SEC's access rules are encoded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.text_signals.edgar_collector import RawFiling
from app.text_signals.edgar_fetcher import (
    EdgarHttpError,
    HttpGet,
    RateLimiter,
    SecUserAgent,
    _default_http_get,
)

#: Documents live on www.sec.gov, not data.sec.gov. The transport sets no Host
#: header precisely so that this works through the same code path.
_ARCHIVES_HOST = "https://www.sec.gov/Archives/"


class DocumentUnavailableError(RuntimeError):
    """Raised when a filing's primary document cannot be retrieved."""


@dataclass(frozen=True)
class FilingDocument:
    """A retrieved primary document plus where it came from."""

    accession_number: str
    symbol: str
    url: str
    markup: str
    byte_length: int
    from_cache: bool


class FilesystemDocumentCache:
    """Disk cache keyed by accession number.

    Filings are immutable once accepted, so a cached document is not merely a
    speed-up: it is what makes the corpus reproducible. Re-running a study
    reads the same bytes rather than whatever SEC serves that day.
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, accession_number: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9]", "", accession_number)
        if not safe:
            raise ValueError(f"unusable accession number: {accession_number!r}")
        return self._root / f"{safe}.html"

    def get(self, accession_number: str) -> str | None:
        path = self._path(accession_number)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    def put(self, accession_number: str, markup: str) -> None:
        path = self._path(accession_number)
        tmp = path.with_suffix(".html.tmp")
        tmp.write_text(markup, encoding="utf-8")
        tmp.replace(path)


class FilingDocumentFetcher:
    """Fetches primary filing documents, with cache and rate limiting."""

    def __init__(
        self,
        user_agent: SecUserAgent,
        *,
        http_get: HttpGet | None = None,
        cache: FilesystemDocumentCache | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        if not isinstance(user_agent, SecUserAgent):
            raise TypeError(
                "user_agent must be a SecUserAgent; SEC refuses undeclared clients"
            )
        self._user_agent = user_agent
        self._http_get = http_get or _default_http_get
        self._cache = cache
        self._rate_limiter = rate_limiter or RateLimiter()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._user_agent.header,
            "Accept-Encoding": "gzip, deflate",
        }

    def fetch(self, filing: RawFiling) -> FilingDocument:
        """Retrieve one filing's primary document.

        A filing whose ``document_url`` is absent is a real condition, not a
        bug — older submissions predate the primary-document field. It raises
        rather than returning an empty string, because a downstream similarity
        computed on "" would silently look like a total rewrite.
        """
        if not filing.document_url:
            raise DocumentUnavailableError(
                f"{filing.accession_number}: no primary document URL on the "
                "submissions record; nothing to retrieve"
            )
        if not filing.document_url.startswith(_ARCHIVES_HOST):
            raise DocumentUnavailableError(
                f"{filing.accession_number}: refusing to fetch off-archive URL "
                f"{filing.document_url!r}"
            )

        if self._cache is not None:
            cached = self._cache.get(filing.accession_number)
            if cached is not None:
                return FilingDocument(
                    accession_number=filing.accession_number,
                    symbol=filing.symbol,
                    url=filing.document_url,
                    markup=cached,
                    byte_length=len(cached.encode("utf-8")),
                    from_cache=True,
                )

        self._rate_limiter.acquire()
        try:
            body = self._http_get(filing.document_url, self.headers)
        except EdgarHttpError as exc:
            raise DocumentUnavailableError(
                f"{filing.accession_number}: {exc}"
            ) from exc

        markup = body.decode("utf-8", errors="replace")
        if not markup.strip():
            raise DocumentUnavailableError(
                f"{filing.accession_number}: empty document body"
            )

        if self._cache is not None:
            self._cache.put(filing.accession_number, markup)

        return FilingDocument(
            accession_number=filing.accession_number,
            symbol=filing.symbol,
            url=filing.document_url,
            markup=markup,
            byte_length=len(body),
            from_cache=False,
        )
