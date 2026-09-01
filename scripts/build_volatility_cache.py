"""Forecast every filing's next twenty sessions once, and cache the quantiles.

Chronos-2 is zero-shot, so there is no training pass -- but there are ~11,000
forecasts, and repeating them on every evidence export would make the export slow
for no reason. This is the only script that loads the model.

Rerunning it over unchanged prices touches no model at all: the cache is keyed by
a digest of each context series, so an unchanged series is a cache hit and a
corrected price bar is a miss.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from filing_triage.chronos_model import ForecastCache, available, forecast
from filing_triage.ingest.prices import load_prices, to_returns
from filing_triage.pit import TradingClock
from filing_triage.volatility import build_forecast_frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=Path("data/build"))
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None,
                        help="forecast only the first N filings, for a smoke test")
    args = parser.parse_args()
    cache_path = args.cache or args.build / "volatility_cache"

    if not available():
        raise SystemExit(
            "chronos-forecasting and torch are not installed. This is an "
            "optional feature group: `pip install -e '.[ts]'`. The volatility "
            "baselines run without it and the export reports them alone."
        )

    events = pd.read_parquet(args.build / "events.parquet")
    events["entry_session"] = events["acceptance_time"].map(
        TradingClock().entry_session)
    returns = to_returns(load_prices(args.build / "prices.parquet"))

    frame, contexts = build_forecast_frame(events, returns)
    if args.limit:
        frame = frame.head(args.limit)
    series = [contexts[event_id] for event_id in frame.index]
    print(f"{len(series):,} filings with enough history "
          f"({frame['actual'].notna().sum():,} have a complete target window)")

    cache = ForecastCache(cache_path)
    started = time.time()
    forecast(series, cache, progress=True)
    print(f"cache: {cache.fingerprint()}")
    print(f"elapsed {time.time() - started:.0f}s -> {cache_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
