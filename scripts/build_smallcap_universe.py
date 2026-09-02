#!/usr/bin/env python3
"""Screen a small-cap universe from SEC data, for the insider-trading study.

    python scripts/build_smallcap_universe.py --out data/build/universe_smallcap.csv

**Why a different universe at all.** The 8-K ranker runs on 193 mega-caps, and
that is the wrong place to look for insider information: across ten large caps
from different sectors, open-market activity ran 6 purchases against 114 sales.
Executives at those companies are paid in stock and sell to diversify, which
says nothing about what they think. The half of the literature with predictive
power is insider *buying*, and in a mega-cap sample it barely exists.

**How market cap is obtained without a data vendor.** The SEC's XBRL frames API
returns one fact for every filer that reported it, in a single request:
`dei:EntityCommonStockSharesOutstanding` gives share counts for thousands of
companies at once. Multiplied by a recent close -- from the price source this
project already uses -- that is a market capitalisation good enough to screen on.
It is not good enough to report as a number, and it is not reported as one.

**Survivorship is worse here, not better, and it cuts the wrong way.**
`company_tickers.json` lists registrants that exist *today*. Small companies fail
far more often than large ones, so a screen built from today's list omits a much
larger fraction of its historical population than the mega-cap list does. And the
direction of that bias is unhelpful: insiders who bought shortly before their
company collapsed are exactly the observations missing, so a study on survivors
will tend to make insider buying look better than it was.

Fixing it needs prices for delisted tickers, which the free sources do not serve.
So the bias is stated -- in the meta file, in the ingest provenance, and on any
page that shows a result from this universe -- rather than quietly carried. It is
the same honesty the large-cap path already practises, applied to a case where
the problem is bigger.
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
FRAMES = ("https://data.sec.gov/api/xbrl/frames/dei/"
          "EntityCommonStockSharesOutstanding/shares/{frame}.json")

# Recent quarterly instants, newest first. Several because a filer appears in the
# frame for the quarter it reported, and not every company reports every quarter.
DEFAULT_FRAMES = ("CY2025Q4I", "CY2025Q3I", "CY2025Q2I", "CY2025Q1I", "CY2024Q4I")

# The band. Below it are shells and micro-caps whose prices are too thin for an
# event study; above it is where insiders stop buying.
MIN_CAP = 300_000_000
MAX_CAP = 3_000_000_000

# A cheap pre-filter so the screen does not fetch a price for every filer in the
# country. A company inside the cap band with a plausible share price sits inside
# this range; the bound is deliberately loose, since a wrong exclusion here is
# invisible later.
MIN_SHARES = 3_000_000
MAX_SHARES = 800_000_000

DEFAULT_START = "2018-01-02"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/build/universe_smallcap.csv")
    parser.add_argument("--min-cap", type=float, default=MIN_CAP)
    parser.add_argument("--max-cap", type=float, default=MAX_CAP)
    parser.add_argument("--start", default=DEFAULT_START,
                        help="interval start; leave room for the routine/opportunistic "
                             "classification's three-year burn-in")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after screening this many candidates")
    args = parser.parse_args()

    agent = os.environ.get("EDGAR_USER_AGENT")
    if not agent:
        print('set EDGAR_USER_AGENT="Your Name you@example.com" -- the SEC requires it',
              file=sys.stderr)
        return 1

    shares = fetch_shares(agent)
    print(f"  {len(shares):,} filers with a reported share count", flush=True)

    tickers = fetch_tickers(agent)
    print(f"  {len(tickers):,} tickers in the SEC mapping", flush=True)

    candidates = build_candidates(shares, tickers)
    if args.limit:
        candidates = candidates.head(args.limit)
    print(f"  {len(candidates):,} candidates inside the share-count pre-filter",
          flush=True)

    screened = screen(candidates, args.min_cap, args.max_cap)
    if screened.empty:
        print("no issuer survived the screen", file=sys.stderr)
        return 1

    start = pd.Timestamp(args.start).date()
    universe = screened[["ticker", "cik", "name"]].copy()
    universe["start_date"] = start
    universe["end_date"] = None

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(out, index=False)

    caps = screened["market_cap"]
    meta = {
        "universe_quality": "screened-sample",
        "survivorship_controlled": False,
        "note": ("Companies currently listed whose screened market cap falls in the "
                 "band. Not an index and not point-in-time. Survivorship is NOT "
                 "controlled and matters more here than for large caps: small "
                 "companies fail more often, and insiders who bought shortly before "
                 "a collapse are the observations most likely to be missing -- which "
                 "biases insider buying to look better than it was."),
        "screen": {
            "min_market_cap": args.min_cap,
            "max_market_cap": args.max_cap,
            "shares_from": "SEC XBRL dei:EntityCommonStockSharesOutstanding",
            "price_from": "last available daily close",
            "caveat": ("Screening market cap only. Share counts are as last "
                       "reported and prices are current, so the product is an "
                       "approximation adequate for bucketing and not for display."),
        },
        "issuers": len(universe),
        "market_cap_percentiles": {
            f"p{int(q * 100)}": float(caps.quantile(q)) for q in (0.1, 0.5, 0.9)
        },
        "candidates_screened": len(candidates),
        "start_date": str(start),
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\n{len(universe)} issuers -> {out}")
    print(f"  market cap: p10 ${caps.quantile(0.1) / 1e6:,.0f}M · "
          f"median ${caps.median() / 1e6:,.0f}M · "
          f"p90 ${caps.quantile(0.9) / 1e6:,.0f}M")
    print(f"  meta -> {out.with_suffix('.meta.json')}")
    print()
    print("  NOTE: survivorship NOT controlled, and the bias is larger here than")
    print("  on the large-cap path. See the module docstring and the meta file.")
    return 0


def fetch_shares(agent: str, frames: tuple[str, ...] = DEFAULT_FRAMES) -> pd.DataFrame:
    """Share counts for every filer, from the newest frame that reports each.

    Frames are read newest-first and the first value for a CIK wins, so a company
    that stopped reporting keeps its last known count rather than dropping out.
    """
    seen: dict[int, dict] = {}
    for frame in frames:
        response = requests.get(FRAMES.format(frame=frame),
                                headers={"User-Agent": agent}, timeout=120)
        if response.status_code != 200:
            continue
        for row in response.json().get("data", []):
            cik = int(row["cik"])
            if cik not in seen and row.get("val"):
                seen[cik] = {"cik": cik, "name": row.get("entityName", ""),
                             "shares": float(row["val"]), "frame": frame}
    return pd.DataFrame(seen.values())


def fetch_tickers(agent: str) -> pd.DataFrame:
    response = requests.get(SEC_TICKERS, headers={"User-Agent": agent}, timeout=60)
    response.raise_for_status()
    rows = [{"cik": int(v["cik_str"]), "ticker": v["ticker"].upper()}
            for v in response.json().values()]
    # A CIK can map to several tickers when a company has multiple share classes.
    # The first is kept, so a dual-class issuer enters once rather than twice.
    return pd.DataFrame(rows).drop_duplicates("cik")


def build_candidates(shares: pd.DataFrame, tickers: pd.DataFrame) -> pd.DataFrame:
    merged = shares.merge(tickers, on="cik", how="inner")
    inside = merged["shares"].between(MIN_SHARES, MAX_SHARES)
    return merged[inside].sort_values("ticker").reset_index(drop=True)


def screen(candidates: pd.DataFrame, min_cap: float, max_cap: float) -> pd.DataFrame:
    """Keep the candidates whose last close puts them inside the band.

    A ticker with no price history is dropped and counted rather than assumed:
    without prices there is no event study, so it could not be used anyway.
    """
    from filing_triage.ingest.prices import fetch_daily

    rows, missing = [], 0
    for position, row in enumerate(candidates.itertuples(), start=1):
        try:
            prices = fetch_daily(row.ticker)
        except Exception:                       # noqa: BLE001 - one dead ticker
            missing += 1                        # must not stop the screen
            continue
        if prices.empty or "close" not in prices:
            missing += 1
            continue
        close = float(prices.sort_values("date")["close"].iloc[-1])
        cap = close * row.shares
        if min_cap <= cap <= max_cap:
            rows.append({"ticker": row.ticker, "cik": row.cik, "name": row.name,
                         "shares": row.shares, "close": close, "market_cap": cap})
        if position % 100 == 0:
            print(f"    screened {position:,}/{len(candidates):,}, "
                  f"kept {len(rows):,}, no prices {missing:,}", flush=True)
    print(f"    screened {len(candidates):,}, kept {len(rows):,}, "
          f"no prices {missing:,}", flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    raise SystemExit(main())
