#!/usr/bin/env python3
"""Build a universe file for the demo ingest from a committed ticker list.

    python scripts/build_demo_universe.py --out data/build/universe.csv

The full builder (`build_universe.py`) reconstructs point-in-time S&P 500
membership from Wikipedia's dated additions-and-removals table. That table has
moved off the page, and scraping a live page for a load-bearing input is how the
last three failures started. This script does the simple thing instead: read a
list of tickers from the repository, resolve each to a CIK through the SEC's own
mapping, and write the intervals.

The consequence is stated rather than hidden. A hand-picked list of companies
that are large today is a survivor sample: the issuers that failed, were acquired
or were delisted are absent by construction. So this path does not control
survivorship bias, and everything downstream says so -- the meta file, the
ingest provenance, and the banner on the report. That leak is demonstrated on the
synthetic corpus, where membership is generated with issuers that join and leave.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
DEFAULT_TICKERS = Path("data/sample/demo_tickers.txt")
DEFAULT_START = "2022-01-03"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tickers", default=str(DEFAULT_TICKERS))
    parser.add_argument("--out", default="data/build/universe.csv")
    parser.add_argument("--start", default=DEFAULT_START,
                        help="interval start; make it match the ingest window")
    args = parser.parse_args()

    agent = os.environ.get("EDGAR_USER_AGENT")
    if not agent:
        print('set EDGAR_USER_AGENT="Your Name you@example.com" -- the SEC requires it',
              file=sys.stderr)
        return 1

    tickers = read_tickers(Path(args.tickers))
    if not tickers:
        print(f"no tickers in {args.tickers}", file=sys.stderr)
        return 1

    ciks = fetch_ciks(agent)
    start = pd.Timestamp(args.start).date()

    rows, missing = [], []
    for ticker in tickers:
        cik = ciks.get(ticker) or ciks.get(ticker.replace("-", "."))
        if cik is None:
            missing.append(ticker)
            continue
        rows.append({"ticker": ticker, "cik": cik, "name": ciks_name(ciks, ticker),
                     "start_date": start, "end_date": None})

    if not rows:
        print("no ticker resolved to a CIK", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)

    meta = {
        "universe_quality": "convenience-sample",
        "survivorship_controlled": False,
        "note": ("Hand-picked large caps that still exist today. Not an index and "
                 "not point-in-time; issuers that failed, were acquired or were "
                 "delisted are absent by construction."),
        "tickers_requested": len(tickers),
        "tickers_resolved": len(rows),
        "unresolved": missing,
        "start_date": str(start),
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))

    print(f"{len(rows)} issuers -> {out}")
    if missing:
        print(f"  unresolved: {', '.join(missing)}")
    print(f"  meta -> {out.with_suffix('.meta.json')}")
    print()
    print("  NOTE: convenience sample, survivorship NOT controlled on this path.")
    print("  See docs/LEAKAGE.md section 3.")
    return 0


def read_tickers(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return [line.strip().upper() for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def fetch_ciks(agent: str) -> dict[str, int]:
    response = requests.get(SEC_TICKERS, headers={"User-Agent": agent}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    mapping = {v["ticker"].upper(): int(v["cik_str"]) for v in payload.values()}
    mapping["_names"] = {v["ticker"].upper(): v["title"] for v in payload.values()}
    return mapping


def ciks_name(ciks: dict, ticker: str) -> str:
    return ciks.get("_names", {}).get(ticker, ticker)


if __name__ == "__main__":
    raise SystemExit(main())
