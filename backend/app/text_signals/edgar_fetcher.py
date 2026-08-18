"""Real SEC EDGAR access, behind the injected ``FilingFetcher`` boundary.

``edgar_collector`` decides *what a record means* (observed vs simulated
receipt). This module decides *where the bytes come from*. Keeping them apart
is what lets every collector test run offline against fixtures while the
network path stays a thin, separately-tested shell.

Source of truth is the per-company submissions JSON:

    https://data.sec.gov/submissions/CIK##########.json

which carries ``acceptanceDateTime`` — the instant the document actually
became public — alongside ``filingDate``, which does not. See
:func:`parse_acceptance_datetime` for why that distinction is load-bearing and
how the timezone was established empirically rather than assumed.

Three obligations SEC places on automated clients, all enforced here:

* a declared ``User-Agent`` carrying a real name and email, or requests are
  refused (:class:`SecUserAgent`, required — there is no default),
* a request rate under roughly 10/second (:class:`RateLimiter`),
* no hammering of endpoints that have not changed (the pagination window
  check in :meth:`EdgarSubmissionsFetcher.__call__` skips archive pages whose
  date range cannot overlap the request).
"""

from __future__ import annotations

import gzip
import json
import re
import time as time_module
import urllib.error
import urllib.request
import zlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

from app.text_signals.edgar_collector import RawFiling

MARKET_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"

#: SEC fair-access guidance is ~10 requests/second. Sit comfortably under it:
#: the marginal minute saved is worth far less than the access is.
DEFAULT_MIN_REQUEST_INTERVAL = timedelta(milliseconds=150)

#: ``filingFrom``/``filingTo`` on archive pages are *filing* dates, while the
#: window being matched is in *acceptance* time, and acceptance can precede
#: its filing date by a day. Widen the overlap test rather than risk dropping
#: a filing that sits exactly on the seam.
_PAGE_WINDOW_PAD = timedelta(days=2)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SecUserAgentError(ValueError):
    """Raised when the declared SEC User-Agent is missing or malformed."""


class EdgarHttpError(RuntimeError):
    """Raised when EDGAR cannot be reached or returns a non-success status."""


class EdgarParseError(ValueError):
    """Raised when a submissions payload does not have the expected shape."""


class SymbolResolutionError(ValueError):
    """Raised when a CIK cannot be mapped to a ticker.

    Not recoverable by guessing. A filing that cannot be joined to a return
    series is useless to this study, and emitting a blank symbol would create
    a phantom row that silently survives into a cross-section.
    """


@dataclass(frozen=True)
class SecUserAgent:
    """The contact header SEC requires of automated clients.

    Deliberately has no default. SEC asks for a real name and address so a
    misbehaving client can be contacted; a placeholder satisfies the parser
    and defeats the purpose, so the value has to be a decision made at the
    call site rather than something inherited silently.
    """

    name: str
    email: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise SecUserAgentError("SEC User-Agent requires a non-empty name")
        if not _EMAIL_RE.match(self.email or ""):
            raise SecUserAgentError(
                f"SEC User-Agent requires a contact email; got {self.email!r}"
            )

    @property
    def header(self) -> str:
        return f"{self.name.strip()} {self.email.strip()}"


#: Injected HTTP boundary: given a URL and headers, return the response body.
HttpGet = Callable[[str, Mapping[str, str]], bytes]


class FilingMetadataCache(Protocol):
    """Accession-keyed store of filing metadata.

    Reproducibility here means a specific thing, and only that thing: **a
    record already in the corpus never changes underneath a re-run.** It does
    not mean the corpus is frozen — a filing genuinely submitted after the
    last run will legitimately appear on the next one. Restatement is the
    hazard being defended against; new information is not.
    """

    def get(self, accession_number: str) -> RawFiling | None: ...
    def put(self, filing: RawFiling) -> None: ...


class NullFilingCache:
    """No-op cache. Explicit opt-out, so 'uncached' is visible at the call site."""

    def get(self, accession_number: str) -> RawFiling | None:  # noqa: ARG002
        return None

    def put(self, filing: RawFiling) -> None:
        return None


class FilesystemFilingCache:
    """One JSON file per accession number, written atomically.

    Filenames are derived from the accession number with separators stripped,
    so a hostile or malformed value cannot escape the cache directory.
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, accession_number: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9]", "", accession_number)
        if not safe:
            raise ValueError(f"unusable accession number: {accession_number!r}")
        return self._root / f"{safe}.json"

    def get(self, accession_number: str) -> RawFiling | None:
        path = self._path(accession_number)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return RawFiling(
            accession_number=payload["accession_number"],
            cik=payload["cik"],
            symbol=payload["symbol"],
            form_type=payload["form_type"],
            acceptance_datetime=datetime.fromisoformat(
                payload["acceptance_datetime"]
            ).astimezone(MARKET_TZ),
            filing_date=(
                datetime.fromisoformat(payload["filing_date"])
                if payload.get("filing_date")
                else None
            ),
            document_url=payload.get("document_url"),
        )

    def put(self, filing: RawFiling) -> None:
        path = self._path(filing.accession_number)
        payload = {
            "accession_number": filing.accession_number,
            "cik": filing.cik,
            "symbol": filing.symbol,
            "form_type": filing.form_type,
            "acceptance_datetime": filing.acceptance_datetime.isoformat(),
            "filing_date": (
                filing.filing_date.isoformat() if filing.filing_date else None
            ),
            "document_url": filing.document_url,
        }
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        tmp.replace(path)


class RateLimiter:
    """Minimum spacing between outbound requests.

    Clock and sleep are injected so the limiter's behaviour is asserted in
    tests without spending the wall-clock time it exists to spend.
    """

    def __init__(
        self,
        min_interval: timedelta = DEFAULT_MIN_REQUEST_INTERVAL,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if min_interval < timedelta(0):
            raise ValueError("min_interval must be non-negative")
        self._min_interval = min_interval.total_seconds()
        self._clock = clock or time_module.monotonic
        self._sleep = sleep or time_module.sleep
        self._last: float | None = None

    def acquire(self) -> None:
        now = self._clock()
        if self._last is not None:
            wait = self._min_interval - (now - self._last)
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last = now


def decode_body(body: bytes, content_encoding: str | None) -> bytes:
    """Decompress a response body according to its ``Content-Encoding``.

    ``urllib`` sends whatever ``Accept-Encoding`` it is given but does **not**
    decompress the reply, so asking for gzip and then parsing the raw bytes
    yields a JSON error that looks like an upstream format change. SEC asks
    clients to accept compression to reduce load on their infrastructure, so
    the right fix is to honour it here rather than to stop requesting it.
    """
    encoding = (content_encoding or "").strip().lower()
    if encoding == "gzip":
        return gzip.decompress(body)
    if encoding == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            # Some servers send raw deflate without the zlib wrapper.
            return zlib.decompress(body, -zlib.MAX_WBITS)
    return body


def _default_http_get(url: str, headers: Mapping[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return decode_body(response.read(), response.headers.get("Content-Encoding"))
    except urllib.error.HTTPError as exc:
        raise EdgarHttpError(f"EDGAR returned HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise EdgarHttpError(f"EDGAR unreachable for {url}: {exc.reason}") from exc


def parse_acceptance_datetime(raw: str) -> datetime:
    """Parse ``acceptanceDateTime`` into an Eastern-time aware instant.

    **The values are genuine UTC.** This was established empirically, not
    assumed, and the assumption is worth stating because the plausible guess
    is wrong: EDGAR is an Eastern-time system and its filing-date rule is
    published in Eastern time, so reading the wall clock as ET is the natural
    mistake. It would shift every document four or five hours and push
    after-hours filings across a session boundary.

    The discriminating evidence is SEC's own dating rule — a submission
    accepted after 17:30 ET is *dated* the next business day:

        acceptance 2016-10-26T20:42:16Z, filingDate 2016-10-26 (same day)
            read as UTC -> 16:42 ET, before the cutoff  -> same day   ✓
            read as ET  -> 20:42 ET, after the cutoff   -> next day   ✗

    Checked across Apple's filing history on the forms where the cutoff
    applies strictly (Section 16 forms are exempt and were excluded), the UTC
    reading predicts the published filing date 175 times against 1 miss; the
    Eastern reading manages 43 against 133. ``test_edgar_fetcher`` re-runs
    that comparison against the saved fixtures so the invariant is enforced
    rather than merely recorded here.

    Naive values are rejected rather than assumed to be UTC: an absent offset
    would mean the upstream format changed, and that is precisely the moment
    to stop rather than to guess.
    """
    text = (raw or "").strip()
    if not text:
        raise EdgarParseError("empty acceptanceDateTime")

    # Python 3.9's fromisoformat does not accept the "Z" designator.
    normalised = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise EdgarParseError(
            f"unrecognised acceptanceDateTime format: {raw!r}"
        ) from exc

    if parsed.tzinfo is None:
        raise EdgarParseError(
            f"acceptanceDateTime {raw!r} carries no UTC offset; SEC supplies one, "
            "so this indicates an upstream format change rather than a value to "
            "be guessed at"
        )
    return parsed.astimezone(MARKET_TZ)


def _parse_filing_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _document_url(cik: str, accession_number: str, primary_document: str | None) -> str | None:
    if not primary_document:
        return None
    stripped = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{stripped}/"
        f"{primary_document}"
    )


def _page_may_overlap(page: Mapping[str, object], start: datetime, end: datetime) -> bool:
    """Whether an archive page's date range can intersect the request window."""
    raw_from = str(page.get("filingFrom") or "")
    raw_to = str(page.get("filingTo") or "")
    if not raw_from or not raw_to:
        return True  # undated page: cannot rule it out, so fetch it
    try:
        page_from = datetime.fromisoformat(raw_from).replace(tzinfo=MARKET_TZ)
        page_to = datetime.fromisoformat(raw_to).replace(tzinfo=MARKET_TZ)
    except ValueError:
        return True
    return (page_from - _PAGE_WINDOW_PAD) <= end and (page_to + _PAGE_WINDOW_PAD) >= start


class EdgarSubmissionsFetcher:
    """A :data:`~app.text_signals.edgar_collector.FilingFetcher` backed by EDGAR.

    Instances are callable as ``fetcher(start, end)`` and yield
    :class:`RawFiling` records whose ``acceptance_datetime`` falls inside the
    window, which is exactly the contract ``EdgarCollector`` injects.

    Form filtering is deliberately *not* duplicated here by default:
    ``EdgarCollector`` already owns that policy, and two components filtering
    on the same axis is how the two quietly disagree. ``form_types`` is
    available as a bandwidth optimisation for callers who want it.
    """

    def __init__(
        self,
        ciks: Sequence[str | int],
        user_agent: SecUserAgent,
        *,
        http_get: HttpGet | None = None,
        cache: FilingMetadataCache | None = None,
        rate_limiter: RateLimiter | None = None,
        form_types: Sequence[str] | None = None,
        symbol_overrides: Mapping[str, str] | None = None,
        include_archives: bool = True,
    ) -> None:
        if not ciks:
            raise ValueError("at least one CIK is required")
        if not isinstance(user_agent, SecUserAgent):
            raise SecUserAgentError(
                "user_agent must be a SecUserAgent; SEC refuses undeclared clients"
            )
        self._ciks = [int(cik) for cik in ciks]
        self._user_agent = user_agent
        self._http_get = http_get or _default_http_get
        self._cache = cache or NullFilingCache()
        self._rate_limiter = rate_limiter or RateLimiter()
        self._form_types = frozenset(form_types) if form_types else None
        self._symbol_overrides = {
            str(int(k)): v for k, v in (symbol_overrides or {}).items()
        }
        self._include_archives = include_archives

    @property
    def headers(self) -> dict[str, str]:
        # Host is deliberately not set: urllib derives it from the URL, and
        # pinning it here would send the wrong Host the moment a document URL
        # on www.sec.gov is fetched through the same transport.
        return {
            "User-Agent": self._user_agent.header,
            "Accept-Encoding": "gzip, deflate",
        }

    def _get_json(self, url: str) -> dict:
        self._rate_limiter.acquire()
        body = self._http_get(url, self.headers)
        try:
            payload = json.loads(body)
        except (ValueError, TypeError) as exc:
            raise EdgarParseError(f"non-JSON response from {url}") from exc
        if not isinstance(payload, dict):
            raise EdgarParseError(f"unexpected JSON shape from {url}")
        return payload

    def _resolve_symbol(self, cik: int, payload: Mapping[str, object]) -> str:
        override = self._symbol_overrides.get(str(cik))
        if override:
            return override
        tickers = payload.get("tickers") or []
        if isinstance(tickers, list) and tickers:
            return str(tickers[0])
        raise SymbolResolutionError(
            f"CIK {cik:010d} has no ticker in its submissions payload; supply "
            "symbol_overrides to state the mapping explicitly"
        )

    def _rows(self, block: Mapping[str, object]) -> Iterable[dict]:
        """Transpose EDGAR's parallel-array encoding into records."""
        accessions = block.get("accessionNumber")
        if not isinstance(accessions, list):
            return []
        keys = [k for k, v in block.items() if isinstance(v, list)]
        count = len(accessions)
        rows = []
        for i in range(count):
            row = {}
            for key in keys:
                values = block[key]
                row[key] = values[i] if i < len(values) else None
            rows.append(row)
        return rows

    def _to_filing(self, cik: int, symbol: str, row: Mapping[str, object]) -> RawFiling | None:
        accession = row.get("accessionNumber")
        if not accession:
            return None
        accession = str(accession)

        cached = self._cache.get(accession)
        if cached is not None:
            return cached

        raw_acceptance = row.get("acceptanceDateTime")
        if not raw_acceptance:
            return None
        acceptance = parse_acceptance_datetime(str(raw_acceptance))

        filing = RawFiling(
            accession_number=accession,
            cik=f"{cik:010d}",
            symbol=symbol,
            form_type=str(row.get("form") or ""),
            acceptance_datetime=acceptance,
            filing_date=_parse_filing_date(
                str(row["filingDate"]) if row.get("filingDate") else None
            ),
            document_url=_document_url(
                str(cik),
                accession,
                str(row["primaryDocument"]) if row.get("primaryDocument") else None,
            ),
        )
        self._cache.put(filing)
        return filing

    def __call__(self, start: datetime, end: datetime) -> list[RawFiling]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("naive datetime rejected; supply aware datetimes")
        window_start = start.astimezone(MARKET_TZ)
        window_end = end.astimezone(MARKET_TZ)
        if window_start > window_end:
            raise ValueError("start must not be after end")

        collected: list[RawFiling] = []
        for cik in self._ciks:
            payload = self._get_json(SUBMISSIONS_URL.format(cik=cik))
            symbol = self._resolve_symbol(cik, payload)
            filings = payload.get("filings")
            if not isinstance(filings, dict):
                raise EdgarParseError(f"CIK {cik:010d}: payload has no 'filings' block")

            blocks: list[Mapping[str, object]] = []
            recent = filings.get("recent")
            if isinstance(recent, dict):
                blocks.append(recent)

            if self._include_archives:
                for page in filings.get("files") or []:
                    if not isinstance(page, dict):
                        continue
                    if not _page_may_overlap(page, window_start, window_end):
                        continue
                    name = page.get("name")
                    if not name:
                        continue
                    archive = self._get_json(
                        SUBMISSIONS_PAGE_URL.format(name=str(name))
                    )
                    blocks.append(archive)

            for block in blocks:
                for row in self._rows(block):
                    if self._form_types is not None:
                        if str(row.get("form") or "") not in self._form_types:
                            continue
                    filing = self._to_filing(cik, symbol, row)
                    if filing is None:
                        continue
                    if window_start <= filing.acceptance_datetime <= window_end:
                        collected.append(filing)

        collected.sort(key=lambda f: (f.acceptance_datetime, f.accession_number))
        return collected
