"""What we predict: how hard the market reacted -- not which way.

Direction is the part institutions with faster data and better models have
already competed away. Magnitude is a different question and a useful one: an
analyst covering fifty issuers wants to know which of today's forty filings are
worth opening. That is a ranking problem over reaction size, and it is
answerable.

The reaction measure is a standard market-model event study:

    estimation window   [event - gap - 120,  event - gap]   sessions
                        regress issuer close-to-close return on the market's
                        -> alpha, beta, and the residual standard deviation
    event window        [entry_session,  entry_session + H)  sessions
                        abnormal return = actual - (alpha + beta * market)
                        CAR = sum over the window

    reaction = |CAR| / (resid_sd * sqrt(H))

expressed in standard deviations of that issuer's own normal noise, so a sleepy
utility and a biotech are on the same scale.

The `gap` matters. Without it the estimation window butts against the event and
absorbs any pre-announcement drift, which shrinks the very abnormality we are
trying to measure.

**Where the event window starts is a correctness decision, not a detail.** A
close-to-close series anchors the entry session's return at the previous close.
For the 63.5% of 8-Ks accepted outside market hours, that price was printed
before the filing existed, so the measured reaction contains the overnight gap
in which the news was priced -- while `pit_entry` claims the entry is the open.
The guards cannot catch this: `causal(acceptance_time <= entry_open)` passes on
every row precisely because the label never touches `entry_open`.

That is not a bug, and `open_anchored_returns` is off by default because of it:
the label answers *was this filing material*, and the overnight gap is part of
that reaction rather than contamination of it. See the switch's own docstring in
`config.py` for the full argument.

Switch it on and the entry session is measured from its opening print, with
subsequent sessions still close-to-close, so the first price in the label is the
first price the entry rule could transact at. That asks a different and harder
question -- how much of the reaction was still on the table at the open -- and
`experiments.anchoring_study` reports both rows side by side. Alpha and beta stay
estimated on close-to-close returns either way, which is the conventional market
model; an open-to-close day has less variance than the close-to-close days the
residual sd was learned from, so the resulting reaction statistic is mildly
conservative rather than flattering.
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
class Panel:
    """One issuer's series, padded onto the shared session axis."""

    ret: np.ndarray
    """Close-to-close. The market model is estimated on this."""
    ret_open_to_close: np.ndarray
    """Same sessions, measured from the opening print. Used for the entry
    session only, and only when `open_anchored_returns` is on."""
    volume: np.ndarray
    volume_baseline: np.ndarray


@dataclass
class SessionGrid:
    """Every series padded onto one shared axis of trading sessions."""

    sessions: list[date]
    position: dict[date, int]
    market: np.ndarray | None
    market_open_to_close: np.ndarray | None
    panels: dict[str, Panel]

    @classmethod
    def build(cls, returns: pd.DataFrame) -> SessionGrid:
        sessions = sorted(returns["date"].unique())
        position = {day: i for i, day in enumerate(sessions)}
        n = len(sessions)

        has_open_anchor = "ret_open_to_close" in returns.columns
        market = None
        market_open_to_close = None
        panels: dict[str, Panel] = {}
        for ticker, group in returns.groupby("ticker", sort=False):
            at = group["date"].map(position).to_numpy()
            ret = np.full(n, np.nan)
            open_to_close = np.full(n, np.nan)
            volume = np.full(n, np.nan)
            baseline = np.full(n, np.nan)
            ret[at] = group["ret"].to_numpy(dtype=float)
            if has_open_anchor:
                open_to_close[at] = group["ret_open_to_close"].to_numpy(dtype=float)
            volume[at] = group["volume"].to_numpy(dtype=float)
            baseline[at] = group["volume_median_60"].to_numpy(dtype=float)
            panels[ticker] = Panel(ret, open_to_close, volume, baseline)
            if ticker == MARKET_TICKER:
                market = ret
                market_open_to_close = open_to_close

        return cls(sessions=sessions, position=position, market=market,
                   market_open_to_close=market_open_to_close, panels=panels)


def _measure(panel: Panel, grid: SessionGrid,
             entry: int, config: PipelineConfig) -> dict | str:
    """Returns the measurement, or a string naming why it could not be made."""
    ret, volume, baseline = panel.ret, panel.volume, panel.volume_baseline
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
    event_stock = ret[entry:window_end + 1].copy()
    event_market = market[entry:window_end + 1].copy()
    if config.open_anchored_returns:
        # Only the first session moves. Everything after entry is an ordinary
        # close-to-close return, because by then the previous close is a price
        # that postdates the filing.
        if grid.market_open_to_close is None:
            raise ValueError(
                "open_anchored_returns needs a `ret_open_to_close` column; "
                "the price panel was built without opening prints"
            )
        event_stock[0] = panel.ret_open_to_close[entry]
        event_market[0] = grid.market_open_to_close[entry]
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
    """OLS of stock on market. Returns (beta, alpha, residual sd).

    `ddof=2` on the residuals, not 1: alpha and beta were both estimated from
    this same window, so two degrees of freedom are already spent. On a
    120-session window the difference is under 1%, but it is a downward bias in
    the denominator of every reaction score -- which is the direction that
    quietly moves filings across the 2.0-sigma threshold.
    """
    var = mkt.var()
    if var <= 0:
        # No market variation to regress on: the model degenerates to the
        # issuer's own mean, and only that one parameter has been estimated.
        return 0.0, float(stock.mean()), float(stock.std(ddof=1))
    beta = float(np.cov(stock, mkt, ddof=1)[0, 1] / (var * len(mkt) / (len(mkt) - 1)))
    alpha = float(stock.mean() - beta * mkt.mean())
    resid = stock - (alpha + beta * mkt)
    if len(resid) <= 2:
        return beta, alpha, float("nan")
    return beta, alpha, float(resid.std(ddof=2))
