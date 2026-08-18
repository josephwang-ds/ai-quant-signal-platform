"""Point-in-time universe of 10-K filers, and the survivorship funnel.

Membership for year *Y* is read from EDGAR's quarterly full-index
(``full-index/YYYY/QTRn/form.idx``), which lists filings as they happened.
Companies that have since been acquired, delisted or gone bankrupt are in it,
because they filed. That makes the **text side** of this study free of
selection bias, which is not true of any universe assembled from a current
ticker list.

It does not make the **return side** unbiased, and this module is built so
that the residual bias is a measured quantity rather than a caveat. Mapping a
historical CIK to a tradeable symbol goes through SEC's current
``company_tickers.json``; a company that no longer exists has no entry and
drops out. :class:`UniverseFunnel` records how many names are lost at each
stage:

```
10-K filers in year Y          point-in-time, unbiased
  → resolvable to a ticker     drops acquired / delisted / renamed
  → usable price history       drops illiquid and data-gap names
  → top N by liquidity         the traded universe
```

The distance between the first and last row is the survivorship leak. Reporting
it as a number is the whole point: "survivorship bias exists" is a sentence
every backtest writes, and almost none of them say how large it is.

See ``docs/PREREGISTRATION_TEXT_SIGNALS.md`` D8.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

FORM_INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/form.idx"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

#: form.idx is fixed-width-ish but not reliably column-aligned across years, so
#: the parser is whitespace-driven with the filename as the right anchor.
#:
#: The date field appears in two shapes and they are not interchangeable:
#: the **quarterly** index writes ``2017-03-24`` while the **daily** index
#: writes ``20260814``. Accepting only one silently yields zero matches against
#: the other — which reads as "no filings that day" rather than as a parse
#: failure, and is exactly the sort of quiet zero this codebase refuses to
#: emit. Both are accepted and normalised by :func:`_normalise_date`.
_FORM_LINE = re.compile(
    r"^(?P<form>\S+)\s+"
    r"(?P<company>.+?)\s{2,}"
    r"(?P<cik>\d+)\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2}|\d{8})\s+"
    r"(?P<path>edgar/data/\S+)\s*$"
)


def _normalise_date(raw: str) -> str:
    """Return an ISO date from either index dialect."""
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw


@dataclass(frozen=True)
class FilingIndexEntry:
    """One 10-K filing as listed in the quarterly index."""

    form_type: str
    company_name: str
    cik: int
    filing_date: str
    document_path: str

    @property
    def accession_number(self) -> str:
        """Derive the accession number from the index path.

        The index gives ``edgar/data/<cik>/<accession>.txt``; the accession is
        the stem, dashes included.
        """
        stem = self.document_path.rsplit("/", 1)[-1]
        return stem[:-4] if stem.endswith(".txt") else stem


@dataclass
class UniverseFunnel:
    """Attrition accounting from filing population to traded universe."""

    year: int
    filers: int = 0
    with_ticker: int = 0
    with_prices: int = 0
    selected: int = 0
    dropped_no_ticker: list[str] = field(default_factory=list)

    @property
    def ticker_attrition(self) -> float | None:
        """Share of point-in-time filers with no current ticker.

        This is the survivorship leak on the return side, expressed as a
        fraction. A large number does not invalidate the study; concealing it
        would.
        """
        if self.filers == 0:
            return None
        return 1.0 - (self.with_ticker / self.filers)

    def as_dict(self) -> dict[str, object]:
        return {
            "year": self.year,
            "filers_point_in_time": self.filers,
            "resolvable_to_ticker": self.with_ticker,
            "with_usable_prices": self.with_prices,
            "selected": self.selected,
            "ticker_attrition": self.ticker_attrition,
            "example_dropped": self.dropped_no_ticker[:10],
        }


def parse_form_index(text: str, *, form_type: str = "10-K") -> list[FilingIndexEntry]:
    """Extract entries of one form type from a quarterly ``form.idx``.

    Matching is exact on the form field: ``10-K`` must not also collect
    ``10-K/A`` (an amendment, which restates rather than reports and would
    double-count the year) or ``10-KT`` (a transition-period report covering a
    non-standard span).
    """
    entries: list[FilingIndexEntry] = []
    for line in text.splitlines():
        match = _FORM_LINE.match(line.rstrip())
        if not match:
            continue
        if match.group("form") != form_type:
            continue
        entries.append(
            FilingIndexEntry(
                form_type=match.group("form"),
                company_name=match.group("company").strip(),
                cik=int(match.group("cik")),
                filing_date=_normalise_date(match.group("date")),
                document_path=match.group("path"),
            )
        )
    return entries


def parse_company_tickers(payload: str | bytes) -> dict[int, str]:
    """CIK → ticker from SEC's ``company_tickers.json``.

    Deliberately current-state: this file is what a historical CIK is resolved
    against, and the fact that it cannot resolve dead companies is the
    measurement :class:`UniverseFunnel` exists to take.
    """
    data = json.loads(payload)
    mapping: dict[int, str] = {}
    for row in data.values():
        cik = row.get("cik_str")
        ticker = row.get("ticker")
        if cik is None or not ticker:
            continue
        # First entry wins: the file lists share classes separately and the
        # primary listing appears first.
        mapping.setdefault(int(cik), str(ticker))
    return mapping


def annual_filers(
    entries: Iterable[FilingIndexEntry],
    *,
    year: int,
) -> dict[int, FilingIndexEntry]:
    """One filing per CIK for the given year, keeping the earliest.

    A company occasionally files more than once in a year (a late prior-year
    10-K plus the current one). Keeping the earliest keeps the series annual
    and avoids a duplicate observation for that firm.
    """
    chosen: dict[int, FilingIndexEntry] = {}
    for entry in entries:
        if not entry.filing_date.startswith(str(year)):
            continue
        existing = chosen.get(entry.cik)
        if existing is None or entry.filing_date < existing.filing_date:
            chosen[entry.cik] = entry
    return chosen


def build_universe_for_year(
    entries: Iterable[FilingIndexEntry],
    ticker_map: Mapping[int, str],
    *,
    year: int,
    price_filter: Callable[[Sequence[str]], set[str]] | None = None,
    max_names: int | None = None,
    liquidity_rank: Callable[[Sequence[str]], list[str]] | None = None,
) -> tuple[dict[int, FilingIndexEntry], UniverseFunnel]:
    """Resolve one year's point-in-time universe, recording attrition.

    ``price_filter`` and ``liquidity_rank`` are injected so this module stays
    free of market-data dependencies and remains testable offline; the price
    side is the caller's concern.
    """
    filers = annual_filers(entries, year=year)
    funnel = UniverseFunnel(year=year, filers=len(filers))

    resolved: dict[int, FilingIndexEntry] = {}
    for cik, entry in filers.items():
        ticker = ticker_map.get(cik)
        if ticker is None:
            funnel.dropped_no_ticker.append(entry.company_name)
            continue
        resolved[cik] = entry
    funnel.with_ticker = len(resolved)

    symbols = [ticker_map[cik] for cik in resolved]
    if price_filter is not None:
        usable = price_filter(symbols)
        resolved = {c: e for c, e in resolved.items() if ticker_map[c] in usable}
        symbols = [ticker_map[cik] for cik in resolved]
    funnel.with_prices = len(resolved)

    if max_names is not None and len(resolved) > max_names:
        ordered = (
            liquidity_rank(symbols) if liquidity_rank is not None else sorted(symbols)
        )
        keep = set(ordered[:max_names])
        resolved = {c: e for c, e in resolved.items() if ticker_map[c] in keep}
    funnel.selected = len(resolved)

    return resolved, funnel


def summarize_funnels(funnels: Sequence[UniverseFunnel]) -> dict[str, object]:
    """Sample-wide attrition summary for the evidence package."""
    if not funnels:
        return {"years": 0, "mean_ticker_attrition": None, "by_year": []}
    attritions = [f.ticker_attrition for f in funnels if f.ticker_attrition is not None]
    return {
        "years": len(funnels),
        "total_filer_observations": sum(f.filers for f in funnels),
        "total_selected": sum(f.selected for f in funnels),
        "mean_ticker_attrition": (
            sum(attritions) / len(attritions) if attritions else None
        ),
        "by_year": [f.as_dict() for f in funnels],
    }
