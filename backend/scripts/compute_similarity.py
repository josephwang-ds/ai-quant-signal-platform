#!/usr/bin/env python3
"""Compute year-over-year Item 1A similarity across the corpus.

For every company, each filing is compared with that company's own previous
filing. IDF is fit **point-in-time**: only documents already available at the
current filing's availability instant contribute term weights, so a filing
that had not yet been submitted cannot influence the weighting applied to an
earlier one.

Availability is derived from the filing date rather than assumed. The corpus
records `filing_date` (EDGAR's assigned date); the study treats a filing as
usable from that date onward, which is conservative: acceptance can precede
the filing date, never follow it.

Output: `similarity.json` — one record per (company, year) pair, plus coverage
counts. No return data is touched here; this stage produces the signal only.

Usage (from backend/):

    .venv/bin/python scripts/compute_similarity.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.text_signals.similarity import (  # noqa: E402
    TimedDocument,
    fit_idf,
    pair_consecutive_filings,
    select_point_in_time_corpus,
    year_over_year_similarity,
)

ET = ZoneInfo("America/New_York")
DEFAULT_ROOT = _BACKEND_ROOT / "outputs" / "text_corpus"


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_documents(root: Path) -> list[TimedDocument]:
    docs: list[TimedDocument] = []
    skipped = 0
    skipped_dupe = 0
    # Strict filename match. A bare *.json glob also picks up the
    # "<name> 2.json" copies that iCloud creates for files in ~/Documents when
    # many are written quickly. Those duplicates silently double-count filings
    # and corrupt the pairing — 2,000 of them appeared during the corpus build.
    valid = re.compile(r"^\d{18}\.json$")
    for path in sorted((root / "sections").glob("*.json")):
        if not valid.match(path.name):
            skipped_dupe += 1
            continue
        rec = json.loads(path.read_text())
        if not rec.get("ok") or not rec.get("text"):
            skipped += 1
            continue
        docs.append(
            TimedDocument(
                doc_id=rec["accession"],
                symbol=rec["ticker"],
                text=rec["text"],
                available_at=datetime.fromisoformat(rec["filing_date"]).replace(
                    tzinfo=ET
                ),
                fiscal_year=rec["year"],
            )
        )
    _log(
        f"  loaded {len(docs):,} extracted sections ({skipped:,} unavailable"
        + (f", {skipped_dupe:,} filename duplicates ignored" if skipped_dupe else "")
        + ")"
    )
    return docs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument(
        "--idf-cap",
        type=int,
        default=400,
        help="Most recent N available documents used to fit IDF. Bounds cost; "
        "the vectoriser does not need the whole history to weight terms.",
    )
    args = ap.parse_args()
    root = Path(args.root)
    started = time.time()

    _log("loading corpus")
    docs = load_documents(root)
    pairs = pair_consecutive_filings(docs)
    _log(f"  {len(pairs):,} consecutive same-company pairs")

    by_time = sorted(docs, key=lambda d: d.available_at)

    # One IDF fit per filing year rather than per pair. The corpus is identical
    # for every pair sharing a cutoff, so refitting per pair costs ~1,900 fits
    # over hundreds of 60k-character documents to reproduce the same weights.
    # The cutoff is the *start* of each year, so no filing contributes term
    # weights to its own comparison or to any earlier one.
    fits: dict[int, tuple[object, list[TimedDocument]]] = {}
    for year in sorted({c.fiscal_year for c, _ in pairs if c.fiscal_year}):
        cutoff = datetime(year, 1, 1, tzinfo=ET)
        usable = select_point_in_time_corpus(by_time, cutoff)
        corpus = usable[-args.idf_cap :] if args.idf_cap else usable
        fits[year] = (fit_idf(corpus), corpus)
        _log(f"  IDF {year}: fit on {len(corpus):,} documents available before {year}")

    results = []
    reasons: Counter = Counter()
    for i, (current, prior) in enumerate(pairs, 1):
        vec, corpus = fits.get(current.fiscal_year, (None, []))
        r = year_over_year_similarity(
            current, prior, idf_corpus=corpus, vectorizer=vec
        )
        results.append(
            {
                "symbol": r.symbol,
                "year": current.fiscal_year,
                "current_doc_id": r.current_doc_id,
                "prior_doc_id": r.prior_doc_id,
                "available_at": current.available_at.isoformat(),
                "cosine_similarity": r.cosine_similarity,
                "change_score": r.change_score,
                "idf_corpus_size": r.idf_corpus_size,
                "unavailable_reason": r.unavailable_reason,
            }
        )
        if not r.ok:
            reasons[(r.unavailable_reason or "?")[:48]] += 1
        if i % 250 == 0:
            _log(f"  {i:,}/{len(pairs):,} pairs")

    ok = [r for r in results if r["cosine_similarity"] is not None]
    by_year: dict[int, list[float]] = defaultdict(list)
    for r in ok:
        by_year[r["year"]].append(r["cosine_similarity"])

    payload = {
        "generated_at": datetime.now(ET).isoformat(),
        "n_pairs": len(results),
        "n_scored": len(ok),
        "idf_cap": args.idf_cap,
        "unavailable_reasons": dict(reasons),
        "coverage_by_year": {
            str(y): len(v) for y, v in sorted(by_year.items())
        },
        "results": results,
    }
    (root / "similarity.json").write_text(json.dumps(payload, indent=1))

    _log(f"  scored {len(ok):,}/{len(results):,} pairs")
    for reason, n in reasons.most_common():
        _log(f"    unavailable: {n:>4}  {reason}")
    _log(f"done in {time.time() - started:.0f}s -> {root/'similarity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
