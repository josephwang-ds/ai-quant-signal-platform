"""Retrospective, point-in-time market context for company filings."""

from __future__ import annotations

import math
from datetime import date

import pandas as pd

from company_lens.contracts import FilingReaction
from filing_triage.pit import TradingClock

MIN_PRIOR_REACTIONS = 5


def build_filing_reactions(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    ticker: str,
    benchmark: str = "SPY",
) -> dict[str, FilingReaction]:
    """Measure each filing after it became knowable, using only earlier filings as context.

    The observed move is the issuer's open-to-close return on the first session whose
    open follows SEC acceptance, less the benchmark's move over the same session.
    Historical magnitude percentiles never include later filings.
    """
    required_events = {"ticker", "accession", "acceptance_time"}
    missing_events = required_events - set(events.columns)
    if missing_events:
        raise ValueError(f"event panel missing columns: {sorted(missing_events)}")
    required_prices = {"ticker", "date", "open", "close"}
    missing_prices = required_prices - set(prices.columns)
    if missing_prices:
        raise ValueError(f"price panel missing columns: {sorted(missing_prices)}")

    issuer = events[
        events["ticker"].astype(str).str.upper() == ticker.upper()
    ].sort_values(["acceptance_time", "accession"])
    if issuer.empty:
        return {}

    asset_bars = _bar_lookup(prices, ticker)
    benchmark_bars = _bar_lookup(prices, benchmark)
    clock = TradingClock()
    prior_magnitudes: list[float] = []
    reactions: dict[str, FilingReaction] = {}

    for row in issuer.itertuples():
        accepted_at = pd.Timestamp(row.acceptance_time).to_pydatetime()
        session = clock.entry_session(accepted_at)
        asset_move = _open_to_close(asset_bars.get(session))
        benchmark_move = _open_to_close(benchmark_bars.get(session))
        if asset_move is None or benchmark_move is None:
            continue

        adjusted_move = asset_move - benchmark_move
        percentile = (
            _inclusive_percentile(prior_magnitudes, abs(adjusted_move))
            if len(prior_magnitudes) >= MIN_PRIOR_REACTIONS
            else None
        )
        reactions[str(row.accession)] = FilingReaction(
            session=session.isoformat(),
            asset_open_to_close=asset_move,
            benchmark_open_to_close=benchmark_move,
            benchmark_adjusted_move=adjusted_move,
            magnitude_percentile=percentile,
            prior_sample_size=len(prior_magnitudes),
        )
        prior_magnitudes.append(abs(adjusted_move))

    return reactions


def _bar_lookup(prices: pd.DataFrame, ticker: str) -> dict[date, tuple[float, float]]:
    selected = prices[prices["ticker"].astype(str).str.upper() == ticker.upper()]
    return {
        pd.Timestamp(row.date).date(): (float(row.open), float(row.close))
        for row in selected.itertuples()
    }


def _open_to_close(bar: tuple[float, float] | None) -> float | None:
    if bar is None:
        return None
    open_price, close_price = bar
    if not math.isfinite(open_price) or not math.isfinite(close_price) or open_price <= 0:
        return None
    return close_price / open_price - 1.0


def _inclusive_percentile(prior: list[float], current: float) -> float:
    return sum(value <= current for value in prior) / len(prior)
