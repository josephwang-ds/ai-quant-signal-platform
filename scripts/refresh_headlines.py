"""Refresh bounded company and market headline metadata from Finnhub."""

from __future__ import annotations

import argparse
import os

from company_lens.news import FinnhubNewsProvider, refresh_headlines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=None)
    parser.add_argument("--universe", default="data/build/universe.csv")
    parser.add_argument("--out", default="data/build/headlines.json")
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--max-per-ticker", type=int, default=5)
    parser.add_argument("--max-market", type=int, default=20)
    parser.add_argument("--request-delay", type=float, default=1.05)
    args = parser.parse_args()

    api_key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not api_key:
        parser.error("FINNHUB_API_KEY is not set; add it to .env and source the file")
    provider = FinnhubNewsProvider(api_key)
    result = refresh_headlines(
        provider=provider,
        output_path=args.out,
        universe_path=args.universe,
        tickers=args.tickers,
        lookback_days=args.lookback_days,
        retention_days=args.retention_days,
        max_per_ticker=args.max_per_ticker,
        max_market=args.max_market,
        request_delay=args.request_delay,
    )
    print(
        f"Headline refresh {result.status}: {result.headline_count} cached rows; "
        f"checked {result.companies_checked} companies via {result.provider}."
    )
    if result.failed_tickers:
        print(f"failed tickers: {', '.join(result.failed_tickers)}")
    if result.market_failed:
        print("market headline request failed; retained last-good market rows")
    print(f"cache written to {result.output_path}; checked at {result.checked_at}")
    return 0 if result.status == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
