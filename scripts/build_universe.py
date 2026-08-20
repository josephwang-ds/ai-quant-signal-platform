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
from datetime import date
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
              start: date) -> pd.DataFrame:
    """Turn the dated additions-and-removals table into membership intervals.

    One row per spell, not one row per ticker. An issuer dropped from the index
    and re-added years later holds two intervals, and collapsing them to one
    would quietly re-admit it for the years it was absent -- reintroducing, in
    the file that exists to prevent it, exactly the survivorship error.
    """
    added_col = _find(changes, "Added", "Ticker")
    removed_col = _find(changes, "Removed", "Ticker")
    date_col = _find(changes, "Date")

    dates = pd.to_datetime(changes[date_col], errors="coerce").dt.date
    moves: dict[str, list[tuple[date, str]]] = {}
    for added, removed, when in zip(changes[added_col], changes[removed_col], dates):
        if pd.isna(when):
            continue
        if pd.notna(added):
            moves.setdefault(_clean(added), []).append((when, "add"))
        if pd.notna(removed):
            moves.setdefault(_clean(removed), []).append((when, "remove"))

    members_now = {_clean(t) for t in current["ticker"]}
    rows = []
    for ticker in sorted(members_now | set(moves)):
        for spell_start, spell_end in _spells(moves.get(ticker, []), ticker in members_now,
                                              start):
            rows.append({
                "ticker": ticker,
                "cik": ciks.get(ticker.replace("-", ".")) or ciks.get(ticker),
                "name": _name_for(current, ticker),
                "start_date": spell_start,
                "end_date": spell_end,
            })

    frame = pd.DataFrame(rows).dropna(subset=["cik"])
    frame["cik"] = frame["cik"].astype(int)
    return frame.sort_values(["ticker", "start_date"]).reset_index(drop=True)


def _spells(moves: list[tuple[date, str]], is_current: bool,
            start: date) -> list[tuple[date, date | None]]:
    """Walk one ticker's moves into (start, end) pairs; end None means still in.

    A ticker whose first recorded move is a removal was a member before the
    changes table begins, so its first spell opens at `start`.
    """
    spells: list[tuple[date, date | None]] = []
    open_from: date | None = None

    for when, kind in sorted(moves):
        if kind == "add":
            if open_from is None:
                open_from = when
        elif open_from is not None:
            spells.append((open_from, when))
            open_from = None
        else:
            spells.append((start, when))       # member since before the table

    if open_from is not None:
        spells.append((open_from, None))
    elif is_current and not any(end is None for _, end in spells):
        # In the index today with no open spell: either it never moved, or it was
        # re-added before the table's coverage. Either way it is in now.
        spells.append((max((end for _, end in spells if end), default=start), None))

    return spells or [(start, None)]


def _clean(ticker: object) -> str:
    """BRK.B on Wikipedia, BRK-B most other places."""
    return str(ticker).strip().upper().replace(".", "-")


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
