#!/usr/bin/env python3
"""Build a point-in-time S&P 500 membership file.

    python scripts/build_universe.py --out data/build/sp500_membership.csv

Two sources, joined:

  Wikipedia's "List of S&P 500 companies" page carries both the current
  constituents and a dated table of additions and removals, which is what makes
  the result point-in-time rather than a snapshot of the survivors.

  The SEC's own company_tickers.json maps ticker to CIK. Going through the SEC
  rather than guessing avoids the tickers that have been recycled between
  different registrants.

Output columns: ticker, cik, name, start_date, end_date  (empty end_date = current).

Deliberately not committed to the repository. A membership file generated today
is a fact about today; regenerating it is cheap, and a stale one checked into git
is the survivorship bug wearing a helpful face.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import requests

WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
DEFAULT_START = "2010-01-01"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/build/sp500_membership.csv")
    parser.add_argument("--start", default=DEFAULT_START,
                        help="assumed join date for constituents already in the "
                             "index before the changes table begins")
    args = parser.parse_args()

    agent = os.environ.get("EDGAR_USER_AGENT")
    if not agent:
        print('set EDGAR_USER_AGENT="Your Name you@example.com" -- the SEC requires it',
              file=sys.stderr)
        return 1

    headers = {"User-Agent": agent}
    current, changes = _read_wikipedia(headers)
    ciks = _read_sec_ciks(headers)

    membership = _assemble(current, changes, ciks, pd.Timestamp(args.start).date())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    membership.to_csv(out, index=False)

    still_in = membership["end_date"].isna().sum()
    print(f"{len(membership):,} membership intervals -> {out}")
    print(f"  {still_in} current constituents, "
          f"{len(membership) - still_in} historical (kept: these are the ones a "
          f"present-day screen would have deleted)")
    return 0


def _read_wikipedia(headers: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    response = requests.get(WIKI, headers=headers, timeout=60)
    response.raise_for_status()
    tables = pd.read_html(response.text)
    current = tables[0].rename(columns={"Symbol": "ticker", "Security": "name"})
    changes = tables[1]
    changes.columns = ["_".join(str(p) for p in col).strip() if isinstance(col, tuple)
                       else str(col) for col in changes.columns]
    return current, changes


def _read_sec_ciks(headers: dict) -> dict[str, int]:
    response = requests.get(SEC_TICKERS, headers=headers, timeout=60)
    response.raise_for_status()
    return {v["ticker"].upper(): int(v["cik_str"]) for v in response.json().values()}


def _assemble(current: pd.DataFrame, changes: pd.DataFrame, ciks: dict[str, int],
              start: object) -> pd.DataFrame:
    added_col = _find(changes, "Added", "Ticker")
    removed_col = _find(changes, "Removed", "Ticker")
    date_col = _find(changes, "Date")

    dates = pd.to_datetime(changes[date_col], errors="coerce").dt.date
    added = {str(t).upper(): d for t, d in zip(changes[added_col], dates)
             if pd.notna(t) and pd.notna(d)}
    removed = {str(t).upper(): d for t, d in zip(changes[removed_col], dates)
               if pd.notna(t) and pd.notna(d)}

    rows = []
    for ticker in {*current["ticker"].str.upper(), *added, *removed}:
        ticker = ticker.replace(".", "-")          # BRK.B on Wikipedia, BRK-B elsewhere
        rows.append({
            "ticker": ticker,
            "cik": ciks.get(ticker.replace("-", ".")) or ciks.get(ticker),
            "name": _name_for(current, ticker),
            "start_date": added.get(ticker, start),
            "end_date": removed.get(ticker),
        })

    frame = pd.DataFrame(rows).dropna(subset=["cik"])
    frame["cik"] = frame["cik"].astype(int)
    return frame.sort_values("ticker").reset_index(drop=True)


def _name_for(current: pd.DataFrame, ticker: str) -> str:
    hit = current[current["ticker"].str.upper() == ticker]
    return str(hit["name"].iloc[0]) if len(hit) else ticker


def _find(frame: pd.DataFrame, *needles: str) -> str:
    for column in frame.columns:
        if all(n.lower() in column.lower() for n in needles):
            return column
    raise KeyError(f"no column matching {needles} in {list(frame.columns)}")


if __name__ == "__main__":
    raise SystemExit(main())
