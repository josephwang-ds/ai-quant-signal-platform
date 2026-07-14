"""Fixture-backed MarketDataPort for offline CI tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.research_execution.market_data_port import (
    DataProvenance,
    MarketDataUnavailableError,
    NormalizedMarketSeries,
    series_actual_bounds,
    utc_now_iso,
    validate_normalized_ohlcv,
)


class FixtureMarketDataAdapter:
    """Loads a fixed local CSV; never contacts the network."""

    name = "fixture"
    source_label = "Local Fixture"

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> NormalizedMarketSeries:
        if not self.csv_path.exists():
            raise MarketDataUnavailableError(f"Fixture missing: {self.csv_path}")

        frame = pd.read_csv(self.csv_path)
        symbol_u = symbol.upper().strip()
        frame = validate_normalized_ohlcv(frame, symbol=symbol_u)
        frame = frame[frame["date"] >= pd.Timestamp(start_date)]
        if end_date:
            frame = frame[frame["date"] <= pd.Timestamp(end_date)]
        frame = frame.reset_index(drop=True)
        if frame.empty:
            raise MarketDataUnavailableError(
                f"Fixture has no rows for {symbol_u} in requested range."
            )

        actual_start, actual_end = series_actual_bounds(frame)
        return NormalizedMarketSeries(
            symbol=symbol_u,
            frame=frame,
            provenance=DataProvenance(
                provider=self.name,
                symbol=symbol_u,
                source=self.source_label,
                retrieved_at=utc_now_iso(),
                requested_start=start_date,
                requested_end=end_date,
                actual_start=actual_start,
                actual_end=actual_end,
                interval="1d",
                cache_hit=False,
                cache_stale=False,
                currency="USD",
            ),
            warnings=["Using deterministic local fixture — not live market data."],
        )
