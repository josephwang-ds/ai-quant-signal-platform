"""Build every locally available company page plus three featured examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_lens import build_snapshots
from company_lens.universe import UnsupportedCompanyError
from company_lens.web import render_company_page, render_index, render_unsupported

DEFAULT_TICKERS = ("AAPL", "MSFT", "NVDA")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tickers", nargs="+", default=None, help="optional subset; default is all local"
    )
    parser.add_argument("--featured", nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--data-dir", type=Path, default=Path("data/build"))
    parser.add_argument(
        "--headline-index",
        type=Path,
        default=None,
        help="optional cached JSON/CSV headline index; omitted by normal production builds",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/build/company_pages")
    )
    args = parser.parse_args()
    try:
        snapshots = build_snapshots(
            args.tickers,
            data_dir=args.data_dir,
            headline_index=args.headline_index,
        )
    except UnsupportedCompanyError as error:
        parser.error(str(error))
    tickers = tuple(snapshot.ticker for snapshot in snapshots)
    featured = tuple(ticker.upper() for ticker in args.featured)
    args.out.mkdir(parents=True, exist_ok=True)
    companies = []

    for snapshot in snapshots:
        ticker = snapshot.ticker
        companies.append(
            {"ticker": snapshot.ticker, "name": snapshot.profile["display_name"]}
        )
        json_path = args.out / f"{ticker.lower()}.json"
        json_path.write_text(
            json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        html_path = render_company_page(snapshot, args.out / f"{ticker.lower()}.html")
        print(f"  {ticker}: {html_path}")
    index = render_index(
        args.out / "index.html",
        tickers=tickers,
        companies=companies,
        featured_tickers=featured,
    )
    render_unsupported(
        args.out / "404.html", company_count=len(companies), featured_tickers=featured
    )
    print(f"company-page index written to {index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
