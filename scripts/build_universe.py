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
import io
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

    still_in = int(membership["end_date"].isna().sum())
    historical = len(membership) - still_in
    print(f"{len(membership):,} membership intervals -> {out}")
    print(f"  {still_in} current constituents, {historical} historical "
          f"(kept: these are the ones a present-day screen would have deleted)")
    unresolved = int(membership["cik"].isna().sum())
    if unresolved:
        print(f"  {unresolved} interval(s) have no CIK and cannot be fetched: "
              f"neither the SEC mapping nor Wikipedia resolves an issuer that has\n"
              f"  already left the index. They stay in the file so the universe "
              f"records them; ingest reports them as a coverage gap.")

    if historical == 0:
        print("\n  WARNING: no historical members. The changes table was parsed but "
              "yielded nothing,\n  so this file describes only today's survivors -- "
              "the survivorship bias this\n  file exists to prevent. Do not ingest "
              "against it.", file=sys.stderr)
        return 1
    return 0


def _read_wikipedia(headers: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The constituents table and the dated changes table.

    Located by what their columns contain, not by position. Wikipedia pages get
    re-ordered, tables get inserted above them, and an index that is right today
    silently reads the wrong table tomorrow -- producing a membership file that is
    wrong rather than a script that fails.
    """
    response = requests.get(WIKI, headers=headers, timeout=60)
    response.raise_for_status()
    # StringIO, not the string itself: pandas 3 reads a bare string as a file
    # path, so a literal document fails with FileNotFoundError -- and the
    # message quotes the whole document, which fills the terminal with the
    # page you were trying to parse and buries the actual error.
    tables = [_flatten(t) for t in pd.read_html(io.StringIO(response.text))]

    current = _pick(tables, lambda cols: (
        any("symbol" in c or "ticker" in c for c in cols)
        and any("security" in c or "company" in c for c in cols)))
    changes = _pick(tables, lambda cols: (
        any("added" in c for c in cols) and any("removed" in c for c in cols)))

    if current is None or changes is None:
        found = [list(t.columns)[:4] for t in tables]
        raise RuntimeError(
            "could not find the expected tables on " + WIKI + ".\n"
            f"Found {len(tables)} table(s) with leading columns: {found}\n"
            "The page layout probably changed; adjust the matchers in _read_wikipedia."
        )

    current = current.rename(columns=lambda c: (
        "ticker" if ("symbol" in c or "ticker" in c) else
        "name" if ("security" in c or "company" in c) else c))
    return current, changes


def _flatten(table: pd.DataFrame) -> pd.DataFrame:
    """MultiIndex headers ('Added','Ticker') -> 'added_ticker', lowercased."""
    table = table.copy()
    table.columns = [
        "_".join(str(part) for part in column
                 if not str(part).startswith("Unnamed")).strip().lower()
        if isinstance(column, tuple) else str(column).strip().lower()
        for column in table.columns
    ]
    return table


def _pick(tables: list[pd.DataFrame], matches) -> pd.DataFrame | None:
    """The largest table whose columns satisfy the predicate."""
    hits = [t for t in tables if matches(list(t.columns))]
    return max(hits, key=len) if hits else None


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
    added_col = _find(changes, "added", "ticker")
    removed_col = _find(changes, "removed", "ticker")
    date_col = _find(changes, "date")

    dates = pd.to_datetime(changes[date_col], errors="coerce").dt.date
    moves: dict[str, list[tuple[date, str]]] = {}
    for added, removed, when in zip(changes[added_col], changes[removed_col], dates, strict=True):
        if pd.isna(when):
            continue
        if pd.notna(added):
            moves.setdefault(_clean(added), []).append((when, "add"))
        if pd.notna(removed):
            moves.setdefault(_clean(removed), []).append((when, "remove"))

    members_now = {_clean(t) for t in current["ticker"]}
    # Wikipedia's constituents table carries a CIK column of its own. The SEC's
    # mapping is authoritative and wins, but it only lists current registrants,
    # so this covers issuers that have since been acquired or delisted -- which
    # are precisely the ones the point-in-time universe exists to keep.
    fallback = _wikipedia_ciks(current)
    rows = []
    for ticker in sorted(members_now | set(moves)):
        for spell_start, spell_end in _spells(moves.get(ticker, []), ticker in members_now,
                                              start):
            rows.append({
                "ticker": ticker,
                "cik": (ciks.get(ticker.replace("-", ".")) or ciks.get(ticker)
                        or fallback.get(ticker)),
                "name": _name_for(current, ticker),
                "start_date": spell_start,
                "end_date": spell_end,
            })

    # Rows without a CIK are kept, not dropped. Neither source resolves one for an
    # issuer that has left the index -- the SEC mapping lists current registrants
    # and Wikipedia's table lists current constituents -- so dropping them would
    # delete precisely the historical members this file exists to preserve, and
    # would do it *after* the survivorship warning had already looked. Their
    # filings cannot be fetched, and that gap is reported rather than hidden.
    frame = pd.DataFrame(rows)
    frame["cik"] = frame["cik"].astype("Int64")
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


def _wikipedia_ciks(current: pd.DataFrame) -> dict[str, int]:
    column = next((c for c in current.columns if "cik" in c), None)
    if column is None:
        return {}
    ciks = pd.to_numeric(current[column], errors="coerce")
    return {_clean(t): int(c)
            for t, c in zip(current["ticker"], ciks, strict=True) if pd.notna(c)}


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
    raise KeyError(
        f"no column matching {needles} in {list(frame.columns)} -- the Wikipedia "
        "table layout has probably changed")


if __name__ == "__main__":
    raise SystemExit(main())
