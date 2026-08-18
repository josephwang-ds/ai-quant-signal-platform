#!/usr/bin/env python3
"""Build the Item 1A text corpus for Experiment A.

Staged and resumable. Every stage skips work already on disk, so an
interrupted run continues rather than restarting, and a re-run is a no-op.

    stage 1  index      quarterly form.idx for the sample years
    stage 2  universe   point-in-time filers -> tickers -> survivorship funnel
    stage 3  documents  fetch primary 10-K documents (gzip-cached)
    stage 4  sections   extract Item 1A from cached documents

Raw HTML is kept **gzipped** rather than discarded. Extraction is the part of
this pipeline most likely to need revision, and keeping the source means a
methodology change costs a local re-run instead of several thousand fresh
requests to SEC. The cost is roughly 1 GB against 80 MB.

A filing is immutable once accepted, so this is a one-time build. Extending the
sample to a new year appends; it never re-fetches. Refreshing the corpus
changes the sample and therefore the result, so it is a deliberate, declared
act — see docs/PREREGISTRATION_TEXT_SIGNALS.md — not a scheduled job.

Usage (from backend/):

    .venv/bin/python scripts/build_text_corpus.py \\
        --name "Your Name" --email you@example.com \\
        --start-year 2015 --end-year 2025 --max-names 200 --stage all
"""

from __future__ import annotations

import argparse
import gzip
import re
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.text_signals.edgar_fetcher import (  # noqa: E402
    RateLimiter,
    SecUserAgent,
    _default_http_get,
)
from app.text_signals.filing_universe import (  # noqa: E402
    COMPANY_TICKERS_URL,
    FORM_INDEX_URL,
    FilingIndexEntry,
    build_universe_for_year,
    parse_company_tickers,
    parse_form_index,
    summarize_funnels,
)
from app.text_signals.section_extraction import extract_risk_factors  # noqa: E402

DEFAULT_ROOT = _BACKEND_ROOT / "outputs" / "text_corpus"
DOCUMENT_URL = "https://www.sec.gov/Archives/{path}"


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


class Corpus:
    def __init__(self, root: Path, user_agent: SecUserAgent) -> None:
        self.root = root
        self.index_dir = root / "index"
        self.docs_dir = root / "documents"
        self.sections_dir = root / "sections"
        for d in (self.index_dir, self.docs_dir, self.sections_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.ua = user_agent
        self.limiter = RateLimiter()
        self.headers = {
            "User-Agent": user_agent.header,
            "Accept-Encoding": "gzip, deflate",
        }

    def _get(self, url: str) -> bytes:
        self.limiter.acquire()
        return _default_http_get(url, self.headers)

    # ---------------------------------------------------------------- stage 1
    def fetch_indexes(self, start_year: int, end_year: int) -> None:
        for year in range(start_year, end_year + 1):
            for quarter in (1, 2, 3, 4):
                dst = self.index_dir / f"form-{year}-QTR{quarter}.idx.gz"
                if dst.exists():
                    continue
                url = FORM_INDEX_URL.format(year=year, quarter=quarter)
                try:
                    body = self._get(url)
                except Exception as exc:  # a future quarter simply does not exist
                    _log(f"  index {year} Q{quarter}: unavailable ({exc})")
                    continue
                dst.write_bytes(gzip.compress(body))
                _log(f"  index {year} Q{quarter}: {len(body):,} bytes")

    def _entries_for_year(self, year: int) -> list[FilingIndexEntry]:
        entries: list[FilingIndexEntry] = []
        for quarter in (1, 2, 3, 4):
            path = self.index_dir / f"form-{year}-QTR{quarter}.idx.gz"
            if not path.exists():
                continue
            text = gzip.decompress(path.read_bytes()).decode("utf-8", "replace")
            entries.extend(parse_form_index(text))
        return entries

    # ---------------------------------------------------------------- stage 2
    def build_universe(
        self, start_year: int, end_year: int, max_names: int
    ) -> dict[int, dict[int, FilingIndexEntry]]:
        tickers_path = self.root / "company_tickers.json"
        if not tickers_path.exists():
            tickers_path.write_bytes(self._get(COMPANY_TICKERS_URL))
        ticker_map = parse_company_tickers(tickers_path.read_bytes())
        _log(f"  CIK->ticker entries: {len(ticker_map):,}")

        # Liquidity ranking, when built, replaces the arbitrary fallback order.
        # Without it selection would degenerate to alphabetical, which is a sort
        # artefact rather than a universe.
        liquidity_path = self.root / "liquidity.json"
        liquidity = (
            json.loads(liquidity_path.read_text()) if liquidity_path.exists() else None
        )
        if liquidity is None:
            _log(
                "  WARNING: liquidity.json missing — selection would fall back to "
                "alphabetical order, which is not a defensible universe. Run "
                "scripts/build_liquidity_ranking.py first."
            )

        selected: dict[int, dict[int, FilingIndexEntry]] = {}
        funnels = []
        for year in range(start_year, end_year + 1):
            entries = self._entries_for_year(year)
            if not entries:
                continue

            ranker = None
            price_filter = None
            if liquidity is not None:
                ordered = liquidity["ranking"].get(str(year), [])
                rank_of = {t: i for i, t in enumerate(ordered)}
                priceable = set(ordered)
                price_filter = lambda syms, _p=priceable: {s for s in syms if s in _p}
                ranker = lambda syms, _r=rank_of: sorted(
                    syms, key=lambda s: _r.get(s, 10**9)
                )

            resolved, funnel = build_universe_for_year(
                entries, ticker_map, year=year, max_names=max_names,
                price_filter=price_filter, liquidity_rank=ranker,
            )
            selected[year] = resolved
            funnels.append(funnel)
            _log(
                f"  {year}: {funnel.filers:,} filers -> {funnel.with_ticker:,} ticker "
                f"({funnel.ticker_attrition:.1%} lost) -> {funnel.with_prices:,} priceable "
                f"-> {funnel.selected} selected"
            )

        summary = summarize_funnels(funnels)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat()
        summary["note"] = (
            "Attrition mixes delisted/acquired companies with filers that were "
            "never exchange-listed (OTC issuers, private companies with public "
            "debt). It bounds the survivorship problem rather than isolating "
            "it; separating the two requires a historical listing database."
        )
        (self.root / "funnel.json").write_text(json.dumps(summary, indent=1))

        (self.root / "universe.json").write_text(
            json.dumps(
                {
                    str(year): {
                        str(cik): {
                            "ticker": ticker_map[cik],
                            "company": e.company_name,
                            "accession": e.accession_number,
                            "filing_date": e.filing_date,
                            "path": e.document_path,
                        }
                        for cik, e in resolved.items()
                    }
                    for year, resolved in selected.items()
                },
                indent=1,
            )
        )
        return selected

    @staticmethod
    def _primary_document(submission: str) -> str | None:
        """Pull the 10-K itself out of an SGML submission file.

        EDGAR's index points at the *complete* submission: one 3M filing
        expanded to 31 MB across 154 documents, almost all of it XBRL and
        exhibits. Storing that whole-hog would cost ~68 GB for this corpus.
        The 10-K document alone gzips to roughly half a megabyte, so the
        submission is parsed and everything except the report is discarded.
        """
        for block in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", submission, re.S):
            kind = re.search(r"<TYPE>([^\r\n<]+)", block)
            if not kind or kind.group(1).strip() != "10-K":
                continue
            body = re.search(r"<TEXT>(.*?)$", block, re.S)
            return body.group(1) if body else None
        return None

    # ---------------------------------------------------------------- stage 3
    def fetch_documents(self) -> None:
        universe = json.loads((self.root / "universe.json").read_text())
        targets = [
            (rec["accession"], rec["path"], rec["ticker"])
            for year in universe.values()
            for rec in year.values()
        ]
        total, done, failed = len(targets), 0, 0
        _log(f"  {total:,} documents to consider")

        for i, (accession, path, ticker) in enumerate(targets, 1):
            dst = self.docs_dir / f"{accession.replace('-', '')}.html.gz"
            if dst.exists():
                done += 1
                continue
            # The index points at the full submission .txt; the primary document
            # lives beside it. The submission text file always exists, so it is
            # the reliable target.
            url = DOCUMENT_URL.format(path=path)
            try:
                submission = self._get(url).decode("utf-8", "replace")
                primary = self._primary_document(submission)
                if primary is None:
                    failed += 1
                    _log(f"    {ticker} {accession}: no 10-K document in submission")
                    continue
                dst.write_bytes(gzip.compress(primary.encode("utf-8")))
                done += 1
            except Exception as exc:
                failed += 1
                _log(f"    {ticker} {accession}: FAILED ({exc})")
            if i % 100 == 0:
                _log(f"  progress {i:,}/{total:,} (ok={done:,} failed={failed:,})")
        _log(f"  documents: ok={done:,} failed={failed:,}")

    # ---------------------------------------------------------------- stage 4
    def extract_sections(self) -> None:
        universe = json.loads((self.root / "universe.json").read_text())
        lookup = {
            rec["accession"]: (year, cik, rec)
            for year, names in universe.items()
            for cik, rec in names.items()
        }
        ok = short = missing = 0
        for path in sorted(self.docs_dir.glob("*.html.gz")):
            key = path.name[: -len(".html.gz")]
            accession = f"{key[:10]}-{key[10:12]}-{key[12:]}"
            meta = lookup.get(accession)
            dst = self.sections_dir / f"{key}.json"
            if dst.exists():
                ok += 1
                continue
            markup = gzip.decompress(path.read_bytes()).decode("utf-8", "replace")
            result = extract_risk_factors(markup)
            if meta is None:
                missing += 1
                continue
            year, cik, rec = meta
            payload = {
                "accession": accession,
                "cik": int(cik),
                "ticker": rec["ticker"],
                "company": rec["company"],
                "filing_date": rec["filing_date"],
                "year": int(year),
                "ok": result.ok,
                "char_count": result.char_count,
                "candidates_considered": result.candidates_considered,
                "terminator": result.terminator,
                "unavailable_reason": result.unavailable_reason,
                "text": result.text,
            }
            dst.write_text(json.dumps(payload))
            if result.ok:
                ok += 1
            else:
                short += 1
        _log(f"  sections: extracted={ok:,} unavailable={short:,} unmatched={missing:,}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="SEC User-Agent name")
    ap.add_argument("--email", required=True, help="SEC User-Agent contact email")
    ap.add_argument("--start-year", type=int, default=2015)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--max-names", type=int, default=200)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument(
        "--stage",
        default="all",
        choices=["index", "universe", "documents", "sections", "all"],
    )
    args = ap.parse_args()

    corpus = Corpus(Path(args.root), SecUserAgent(args.name, args.email))
    started = time.time()

    if args.stage in ("index", "all"):
        _log("stage 1: quarterly indexes")
        corpus.fetch_indexes(args.start_year, args.end_year)
    if args.stage in ("universe", "all"):
        _log("stage 2: point-in-time universe + survivorship funnel")
        corpus.build_universe(args.start_year, args.end_year, args.max_names)
    if args.stage in ("documents", "all"):
        _log("stage 3: primary documents")
        corpus.fetch_documents()
    if args.stage in ("sections", "all"):
        _log("stage 4: Item 1A extraction")
        corpus.extract_sections()

    _log(f"done in {time.time() - started:.0f}s -> {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
