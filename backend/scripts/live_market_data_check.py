#!/usr/bin/env python3
"""Bounded local live market-data verification (optional, manual)."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from app.research_execution.live_verification import (
    AKSHARE_LIVE_END,
    AKSHARE_LIVE_START,
    LiveVerificationError,
    YAHOO_LIVE_END,
    YAHOO_LIVE_START,
    assert_no_fabricated_fallback,
    assert_ohlcv_frame,
    assert_provenance_contract,
    dumps_check_payload,
    series_to_check_payload,
)
from app.research_execution.market_data_port import MarketDataError, MarketDataValidationError
from app.research_execution.market_data_router import MarketDataRouter
from app.research_execution.price_cache import PriceCache
from app.research_execution.symbol import classify_symbol


def _default_range(symbol: str) -> tuple[str, str | None]:
    descriptor = classify_symbol(symbol)
    if descriptor.preferred_provider == "akshare":
        return AKSHARE_LIVE_START, AKSHARE_LIVE_END
    return YAHOO_LIVE_START, YAHOO_LIVE_END


def _error_payload(symbol: str, exc: Exception) -> dict:
    category = getattr(exc, "category", None)
    if isinstance(exc, MarketDataValidationError):
        category = category or "unsupported_symbol"
    elif isinstance(exc, MarketDataError):
        category = category or "provider_unavailable"
    elif isinstance(exc, LiveVerificationError):
        category = category or exc.category
    else:
        category = category or "unknown"
    return {
        "ok": False,
        "symbol": symbol,
        "provider": None,
        "error_category": category,
        "message": str(exc),
    }


def run_check(
    *,
    symbol: str,
    start_date: str | None,
    end_date: str | None,
    cache_root: Path | None,
) -> dict:
    default_start, default_end = _default_range(symbol)
    start = start_date or default_start
    end = end_date if end_date is not None else default_end
    descriptor = classify_symbol(symbol)

    cache = PriceCache(root=cache_root) if cache_root else PriceCache()
    router = MarketDataRouter(cache=cache)
    series = router.get_daily_ohlcv(symbol, start, end)

    assert_ohlcv_frame(series.frame)
    assert_provenance_contract(
        series.provenance,
        expected_provider=descriptor.preferred_provider,
        expected_asset_class=descriptor.asset_class,
        expected_canonical_symbol=descriptor.canonical_symbol,
        expected_exchange=descriptor.exchange,
        expected_adjustment="qfq" if descriptor.preferred_provider == "akshare" else None,
    )
    assert_no_fabricated_fallback(series.warnings)
    return series_to_check_payload(series)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded live market-data check")
    parser.add_argument("--symbol", required=True, help="Canonical symbol, e.g. SPY or 600519.SH")
    parser.add_argument("--start-date", default=None, help="Inclusive start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Inclusive end date YYYY-MM-DD")
    parser.add_argument(
        "--cache-root",
        default=None,
        help="Optional cache directory (defaults to backend/.cache/market_data)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print stack traces on failure (local diagnostics only)",
    )
    args = parser.parse_args(argv)

    cache_root = Path(args.cache_root) if args.cache_root else None
    try:
        payload = run_check(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            cache_root=cache_root,
        )
        print(dumps_check_payload(payload))
        return 0
    except Exception as exc:  # noqa: BLE001 — script boundary
        payload = _error_payload(args.symbol, exc)
        print(json.dumps(payload, indent=2, sort_keys=True))
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
