"""What we predict: how hard the market reacted -- not which way.

Direction is the part institutions with faster data and better models have
already competed away. Magnitude is a different question and a useful one: an
analyst covering fifty issuers wants to know which of today's forty filings are
worth opening. That is a ranking problem over reaction size, and it is
answerable.

The reaction measure is a standard market-model event study:

    estimation window   [event - gap - 120,  event - gap]   sessions
                        regress issuer return on market return -> alpha, beta,
                        and the residual standard deviation
    event window        [entry_session,  entry_session + H)  sessions
                        abnormal return = actual - (alpha + beta * market)
                        CAR = sum over the window

    reaction = |CAR| / (resid_sd * sqrt(H))

expressed in standard deviations of that issuer's own normal noise, so a sleepy
utility and a biotech are on the same scale.

The `gap` matters. Without it the estimation window butts against the event and
absorbs any pre-announcement drift, which shrinks the very abnormality we are
trying to measure.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from filing_triage.config import PipelineConfig

MARKET_TICKER = "SPY"


def build_labels(events: pd.DataFrame, returns: pd.DataFrame,
                 config: PipelineConfig) -> pd.DataFrame:
    """Attach a reaction magnitude and a binary 'worth reading' label to each event.

    `events` needs `event_id`, `ticker` and `entry_session`.
    `returns` is the output of `ingest.prices.to_returns`.

    Everything is aligned onto one global grid of trading sessions first, so the
    per-event work is integer slicing of numpy arrays. The obvious implementation
    -- boolean-masking a DataFrame and joining the benchmark once per event --
    is two orders of magnitude slower and was the whole runtime of this project.
    Aligning on the sessions the price data actually contains is also more honest
    than trusting the rule calendar: a day with no print is not tradable, whatever
    the calendar says.
    """
    grid = SessionGrid.build(returns)
    if grid.market is None:
        raise ValueError(f"no {MARKET_TICKER} rows in the price panel; "
                         "the market model needs a benchmark")

    rows: list[dict] = []
    dropped: Counter[str] = Counter()
    for event in events.itertuples():
        panel = grid.panels.get(event.ticker)
        if panel is None:
            dropped["no price series for the issuer"] += 1
            continue
        entry = grid.position.get(event.entry_session)
        if entry is None:
            dropped["entry session has no price bar"] += 1
            continue
        measured = _measure(panel, grid, entry, config)
        if isinstance(measured, str):
            dropped[measured] += 1
            continue
        rows.append({"event_id": event.event_id, **measured})

    if not rows:
        return pd.DataFrame(columns=["event_id", "car", "reaction", "volume_surprise",
                                     "label", "estimation_end", "label_end_session"])

    out = pd.DataFrame(rows)
    # Fixed ex ante. A quantile estimated over this full frame would use future
    # test-fold outcomes to define what counts as material, even if the model
    # itself never trains on those outcomes.
    threshold = config.reaction_threshold
    out["label"] = (out["reaction"] >= threshold).astype(int)
    out.attrs["reaction_threshold"] = float(threshold)
    # Attrition, itemised. An event that cannot be measured is not a bug, but an
    # unexplained 17% of them going missing between ingest and scoring is
    # indistinguishable from one -- and silent data loss is the same class of
    # problem as silent leakage: it changes the answer and nothing says so.
    out.attrs["attrition"] = dict(dropped)
    out.attrs["measured"] = len(out)
    return out


@dataclass
class SessionGrid:
    """Every series padded onto one shared axis of trading sessions."""

    sessions: list[date]
    position: dict[date, int]
    market: np.ndarray | None
    panels: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]

    @classmethod
    def build(cls, returns: pd.DataFrame) -> SessionGrid:
        sessions = sorted(returns["date"].unique())
        position = {day: i for i, day in enumerate(sessions)}
        n = len(sessions)

        market = None
        panels: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for ticker, group in returns.groupby("ticker", sort=False):
            at = group["date"].map(position).to_numpy()
            ret = np.full(n, np.nan)
            volume = np.full(n, np.nan)
            baseline = np.full(n, np.nan)
            ret[at] = group["ret"].to_numpy(dtype=float)
            volume[at] = group["volume"].to_numpy(dtype=float)
            baseline[at] = group["volume_median_60"].to_numpy(dtype=float)
            panels[ticker] = (ret, volume, baseline)
            if ticker == MARKET_TICKER:
                market = ret

        return cls(sessions=sessions, position=position, market=market, panels=panels)


def _measure(panel: tuple[np.ndarray, np.ndarray, np.ndarray], grid: SessionGrid,
             entry: int, config: PipelineConfig) -> dict | str:
    """Returns the measurement, or a string naming why it could not be made."""
    ret, volume, baseline = panel
    market = grid.market

    est_end = entry - config.estimation_gap_sessions
    # Both slice endpoints are inclusive below, so +1 is required for exactly
    # `estimation_sessions` observations rather than 121 for a 120-session config.
    est_start = est_end - config.estimation_sessions + 1
    if est_start < 0:
        return "not enough history before the event"

    stock_window = ret[est_start:est_end + 1]
    market_window = market[est_start:est_end + 1]
    usable = np.isfinite(stock_window) & np.isfinite(market_window)
    if usable.sum() < config.estimation_sessions // 2:
        return "estimation window too sparse"

    beta, alpha, resid_sd = _market_model(stock_window[usable], market_window[usable])
    if not np.isfinite(resid_sd) or resid_sd <= 0:
        return "no usable residual variance"

    window_end = entry + config.event_window_sessions - 1
    if window_end >= len(ret):
        return "event window runs past the end of the price data"
    event_stock = ret[entry:window_end + 1]
    event_market = market[entry:window_end + 1]
    if not (np.isfinite(event_stock).all() and np.isfinite(event_market).all()):
        return "missing price bars inside the event window"

    abnormal = event_stock - (alpha + beta * event_market)
    car = float(abnormal.sum())
    reaction = abs(car) / (resid_sd * np.sqrt(config.event_window_sessions))

    base = baseline[entry]
    volume_surprise = (
        float(np.log(np.nanmean(volume[entry:window_end + 1]) / base))
        if np.isfinite(base) and base > 0 else np.nan
    )

    return {
        "car": car,
        "reaction": float(reaction),
        "volume_surprise": volume_surprise,
        "estimation_end": grid.sessions[est_end],
        # When this label is fully observed. Purged CV keys off this, not the
        # event date -- the outcome is not known until the window closes.
        "label_end_session": grid.sessions[window_end],
    }


def _market_model(stock: np.ndarray, mkt: np.ndarray) -> tuple[float, float, float]:
    """OLS of stock on market. Returns (beta, alpha, residual sd)."""
    var = mkt.var()
    if var <= 0:
        return 0.0, float(stock.mean()), float(stock.std(ddof=1))
    beta = float(np.cov(stock, mkt, ddof=1)[0, 1] / (var * len(mkt) / (len(mkt) - 1)))
    alpha = float(stock.mean() - beta * mkt.mean())
    resid = stock - (alpha + beta * mkt)
    return beta, alpha, float(resid.std(ddof=1))
