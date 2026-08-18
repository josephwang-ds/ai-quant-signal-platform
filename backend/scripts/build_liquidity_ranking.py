#!/usr/bin/env python3
"""Rank point-in-time filers by tradeable liquidity.

The universe must be *investable*, not merely *filed*. A 10-K filer with no
exchange listing or a few thousand dollars of daily turnover cannot carry a
quintile portfolio, so the traded universe is the liquid subset of the
point-in-time filing population.

This is a liquidity screen, not a survivorship filter: it is applied to each
year's filers using data from **that year**, so it does not consult the future
and does not prefer companies that later survived.

Two things it produces:

* ``liquidity.json`` — per-year tickers ranked by median daily dollar volume.
* the price-stage attrition count, which is the third rung of the survivorship
  funnel (filers -> ticker -> **priceable** -> selected).

Prices come from Yahoo via ``yfinance``. Tickers that return nothing are not
errors: a company that had not yet listed in that year genuinely has no price
history, and that is the point-in-time answer.

Usage (from backend/):

    .venv/bin/python scripts/build_liquidity_ranking.py --start-year 2015 --end-year 2025
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import warnings
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

warnings.filterwarnings("ignore")

from app.text_signals.filing_universe import (  # noqa: E402
    annual_filers,
    parse_company_tickers,
    parse_form_index,
)

DEFAULT_ROOT = _BACKEND_ROOT / "outputs" / "text_corpus"
BATCH = 80
#: Yahoo throttles sustained batch downloads. Observed live: the first year
#: returned 85% of tickers, the next two returned ~30% — not a market fact but
#: a rate-limit artefact, and one that a per-year cache would have frozen into
#: the universe permanently. Pace the requests and retry rather than accepting
#: whatever survives.
BATCH_PAUSE_SECONDS = 2.0
MAX_RETRIES = 4
#: A year whose success rate falls far below its neighbours is throttled, not
#: sparse. Refuse to cache it; a missing year is recoverable, a silently
#: truncated one is not.
MIN_SUCCESS_RATE = 0.55


def _log(msg: str) -> None:
    from datetime import datetime

    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def candidates_by_year(root: Path, start: int, end: int) -> dict[int, dict[str, int]]:
    """Every point-in-time filer that resolves to a ticker, per year."""
    ticker_map = parse_company_tickers((root / "company_tickers.json").read_bytes())
    out: dict[int, dict[str, int]] = {}
    for year in range(start, end + 1):
        entries = []
        for quarter in (1, 2, 3, 4):
            path = root / "index" / f"form-{year}-QTR{quarter}.idx.gz"
            if path.exists():
                entries.extend(
                    parse_form_index(
                        gzip.decompress(path.read_bytes()).decode("utf-8", "replace")
                    )
                )
        if not entries:
            continue
        filers = annual_filers(entries, year=year)
        out[year] = {
            ticker_map[cik]: cik for cik in filers if cik in ticker_map
        }
        _log(f"  {year}: {len(out[year]):,} candidates with tickers")
    return out


def price_union_once(
    tickers: list[str], start_year: int, end_year: int, cache_dir: Path
) -> dict[int, dict[str, float]]:
    """Median daily dollar volume per ticker per year, fetched **once**.

    The first implementation priced every candidate separately for every year,
    which issued roughly eleven times more requests than necessary and got the
    session rate-limited: the opening year returned 85% of tickers and the next
    two returned ~30%. That was not sparsity in the market, it was throttling,
    and a per-year cache would have frozen the artefact into the universe.

    Downloading each ticker's whole history once and slicing per year locally
    removes the redundancy at the source, which is a better fix than retrying
    harder against a limit we were creating ourselves.
    """
    import pandas as pd
    import yfinance as yf

    per_year: dict[int, dict[str, float]] = {y: {} for y in range(start_year, end_year + 1)}
    cache_dir.mkdir(parents=True, exist_ok=True)
    done_path = cache_dir / "batches_done.json"
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()

    total = len(tickers)
    for i in range(0, total, BATCH):
        key = str(i)
        batch_cache = cache_dir / f"batch_{i}.json"
        if key in done and batch_cache.exists():
            for year_str, values in json.loads(batch_cache.read_text()).items():
                per_year[int(year_str)].update(values)
            continue

        chunk = tickers[i : i + BATCH]
        frame = None
        for attempt in range(MAX_RETRIES):
            try:
                frame = yf.download(
                    chunk,
                    start=f"{start_year}-01-01",
                    end=f"{end_year}-12-31",
                    progress=False,
                    auto_adjust=False,
                    threads=False,   # serial inside a batch is gentler on the API
                )
            except Exception as exc:
                _log(f"    batch {i}: attempt {attempt + 1} failed ({exc})")
                frame = None
            if frame is not None and not frame.empty:
                break
            wait = BATCH_PAUSE_SECONDS * (2 ** attempt)
            _log(f"    batch {i}: backing off {wait:.0f}s")
            time.sleep(wait)
        if frame is None or frame.empty:
            _log(f"    batch {i}: no data after {MAX_RETRIES} attempts")
            continue

        try:
            close, volume = frame["Close"], frame["Volume"]
        except KeyError:
            continue
        if isinstance(close, pd.Series):
            close = close.to_frame(chunk[0])
            volume = volume.to_frame(chunk[0])

        dollar = close * volume
        batch_out: dict[str, dict[str, float]] = {}
        for year in range(start_year, end_year + 1):
            window = dollar.loc[str(year)] if str(year) in dollar.index.astype(str).str[:4].unique() else None
            try:
                window = dollar[dollar.index.year == year]
            except Exception:
                window = None
            if window is None or window.empty:
                continue
            medians = window.median().dropna()
            values = {str(t): float(v) for t, v in medians.items() if v and v > 0}
            per_year[year].update(values)
            batch_out[str(year)] = values

        batch_cache.write_text(json.dumps(batch_out))
        done.add(key)
        done_path.write_text(json.dumps(sorted(done)))
        priced_now = sum(len(v) for v in per_year.values())
        _log(f"    {min(i + BATCH, total):,}/{total:,} tickers, {priced_now:,} ticker-years")
        time.sleep(BATCH_PAUSE_SECONDS)

    return per_year


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-year", type=int, default=2015)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    args = ap.parse_args()

    root = Path(args.root)
    started = time.time()

    _log("collecting point-in-time candidates")
    candidates = candidates_by_year(root, args.start_year, args.end_year)

    union = sorted({t for year in candidates.values() for t in year})
    _log(f"union of candidates across all years: {len(union):,} tickers")
    priced_by_year = price_union_once(
        union, args.start_year, args.end_year, root / "prices"
    )

    ranking: dict[str, list[str]] = {}
    attrition: dict[str, dict[str, int]] = {}
    for year, tickers in candidates.items():
        # Rank only names that actually filed that year, using that year's data.
        priced = {t: v for t, v in priced_by_year.get(year, {}).items() if t in tickers}
        ordered = sorted(priced, key=lambda t: priced[t], reverse=True)
        ranking[str(year)] = ordered
        attrition[str(year)] = {
            "candidates_with_ticker": len(tickers),
            "with_price_history": len(priced),
        }
        _log(
            f"  {year}: {len(priced):,}/{len(tickers):,} priceable "
            f"({1 - len(priced)/max(1,len(tickers)):.1%} price attrition)"
        )

    (root / "liquidity.json").write_text(
        json.dumps({"ranking": ranking, "attrition": attrition}, indent=1)
    )
    _log(f"done in {time.time() - started:.0f}s -> {root/'liquidity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
