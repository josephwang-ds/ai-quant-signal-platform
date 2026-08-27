"""Refresh cached daily price histories and the consolidated market panel."""

from __future__ import annotations

import argparse

from company_lens.refresh import refresh_market_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=None)
    parser.add_argument("--data-dir", default="data/build")
    parser.add_argument("--universe", default=None)
    parser.add_argument("--cache-dir", default="data/cache/prices")
    args = parser.parse_args()
    result = refresh_market_data(
        data_dir=args.data_dir,
        universe_path=args.universe,
        cache_dir=args.cache_dir,
        tickers=args.tickers,
    )
    print(
        f"Market refresh {result.status}: refreshed {len(result.refreshed_tickers)} "
        f"of {result.tickers_checked + len(result.failed_tickers)} symbols."
    )
    if result.failed_tickers:
        print(f"failed tickers: {', '.join(result.failed_tickers)}")
    print(f"latest price date {result.latest_price_date}; checked at {result.checked_at}")
    return 0 if result.status == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
