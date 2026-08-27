"""Check SEC submission heads and append newly observed 8-K filings."""

from __future__ import annotations

import argparse

from company_lens.refresh import refresh_filings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=None)
    parser.add_argument("--data-dir", default="data/build")
    parser.add_argument("--universe", default=None)
    parser.add_argument("--since", default=None)
    args = parser.parse_args()
    result = refresh_filings(
        data_dir=args.data_dir,
        universe_path=args.universe,
        tickers=args.tickers,
        since=args.since,
    )
    print(
        f"SEC filing refresh {result.status}: checked {result.companies_checked} companies, "
        f"added {result.new_filings} filing(s)."
    )
    if result.changed_tickers:
        print(f"changed tickers: {', '.join(result.changed_tickers)}")
    if result.failed_tickers:
        print(f"failed tickers: {', '.join(result.failed_tickers)}")
    print(f"checked at {result.checked_at}")
    return 0 if result.status == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
