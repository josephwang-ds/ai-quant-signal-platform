"""Forecasting how turbulent the next month is, and the bar it has to clear.

This answers a different question from the rest of the project. The ranker asks
*which filing deserves a read*; this asks *how much movement to expect from this
issuer over the next twenty sessions*, as a distribution rather than a number.
It is a risk statement, and it is deliberately kept away from the ranker: no
forecast produced here is a feature there, because a volatility forecast fed
into a filing ranker is a short step from a return prediction wearing a risk
label.

**The forecast is made where the reader stands.** History ends at the session
before entry; the target covers the entry session and the nineteen after it. So
the model has seen nothing from the window it predicts -- not the filing's own
reaction, not the session a reader would act on. That costs one session of
information and buys a forecast that means what it says.

**Volatility is forecast in logs.** Realized volatility is bounded below by zero,
strongly right-skewed, and roughly log-normal; a Gaussian interval on the raw
scale puts probability mass below zero and is too narrow in the tail that
matters. Every baseline here works on log volatility and exponentiates at the
end, which is why their intervals are asymmetric.

**Three baselines, because "a foundation model beat nothing" is not a result.**

`random_walk` carries the last observation forward. It is the hardest baseline to
beat in volatility forecasting and the one most often omitted from papers that
claim to beat it.

`climatology` ignores the present entirely and quotes the issuer's own historical
distribution. A model that cannot beat this has learned nothing about *now*.

`har` is the Heterogeneous Autoregressive model -- daily, weekly and monthly
volatility components in a linear regression on logs. It is the standard
workhorse, it is twelve lines, and it is usually competitive with far more
elaborate machinery.

All three produce full quantiles, not point forecasts, because the card being
proposed shows a band and a band that is never scored is decoration.

**Scored on pinball loss and on coverage, and both are needed.** Pinball loss
alone rewards a model that is sharp and wrong in a way coverage catches; coverage
alone is maximised by an interval from zero to infinity. A forecast ships only if
its 50% and 80% intervals contain the outcome about 50% and 80% of the time
*and* its pinball loss beats the baselines.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Twenty sessions is about a calendar month, and it is the horizon the card
# states. Changing it changes the target, so it is a constant rather than a
# parameter with a default nobody revisits.
HORIZON = 20
ANNUALISE = float(np.sqrt(252))

# The quantiles scored everywhere. 0.1/0.9 and 0.25/0.75 give the 80% and 50%
# bands the card would draw; the median is the point forecast.
QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)

# HAR's three components: yesterday, last week, last month.
HAR_LAGS = (1, 5, 22)
# Enough history to fit HAR and to have a climatology worth quoting. Below this
# an issuer gets no forecast rather than a fitted one.
MIN_HISTORY = 260
# How much history each forecaster is handed: four years of sessions. The
# distinction from MIN_HISTORY matters. A one-year window would make
# `climatology` quietly adaptive -- "this issuer's usual volatility" would mean
# "last year's", and the baseline that is supposed to ignore the present would
# stop ignoring it. Four years spans at least one regime change for most issuers,
# which is what makes it a fair opponent rather than a straw one.
LOOKBACK = 1008

BASELINES = ("random_walk", "climatology", "har")


def realized_volatility(returns: np.ndarray) -> float:
    """Annualised standard deviation of a window of daily returns.

    `ddof=1`: the window is a sample of the issuer's behaviour over those
    sessions, not the population of everything it could have done.
    """
    usable = returns[np.isfinite(returns)]
    if usable.size < 2:
        return float("nan")
    return float(np.std(usable, ddof=1) * ANNUALISE)


@dataclass
class VolatilityPanel:
    """One issuer's return series on the shared session axis.

    Built once and sliced per event, because an issuer with 60 filings would
    otherwise rebuild the same series 60 times.
    """

    sessions: np.ndarray
    position: dict
    returns: dict[str, np.ndarray]

    @classmethod
    def build(cls, returns: pd.DataFrame) -> VolatilityPanel:
        sessions = np.array(sorted(pd.to_datetime(returns["date"]).unique()))
        position = {day: i for i, day in enumerate(sessions)}
        series: dict[str, np.ndarray] = {}
        frame = returns.copy()
        frame["date"] = pd.to_datetime(frame["date"])
        for ticker, group in frame.groupby("ticker", sort=False):
            values = np.full(len(sessions), np.nan)
            at = group["date"].map(position).to_numpy()
            known = pd.notna(at)
            values[at[known].astype(int)] = group.loc[known, "ret"].to_numpy(float)
            series[ticker] = values
        return cls(sessions=sessions, position=position, returns=series)

    def trailing_series(self, ticker: str, end: int, window: int = HORIZON,
                        lookback: int = LOOKBACK) -> np.ndarray:
        """Rolling realized volatility, one value per session, ending at `end`.

        This is what the forecaster is given. Its last point is the trailing
        window ending at `end`, and `end` is the session *before* the one being
        forecast, so no part of the target window is inside it.
        """
        series = self.returns.get(ticker)
        if series is None or end < window:
            return np.array([])
        start = max(0, end - lookback - window)
        rolled = pd.Series(series[start:end + 1]).rolling(
            window, min_periods=window // 2).std() * ANNUALISE
        return rolled.dropna().to_numpy()

    def forward_volatility(self, ticker: str, anchor: int,
                           horizon: int = HORIZON) -> float:
        """The target: realized volatility over `anchor` .. `anchor + horizon - 1`.

        Returns NaN when the window runs past the end of the price data, so a
        filing near the edge of the sample is dropped rather than scored on a
        truncated window that would look artificially calm.
        """
        series = self.returns.get(ticker)
        if series is None or anchor + horizon > len(series):
            return float("nan")
        return realized_volatility(series[anchor:anchor + horizon])


def _log_quantiles(centre: float, spread: np.ndarray,
                   quantiles=QUANTILES) -> dict[float, float]:
    """Quantiles on the log scale, exponentiated back.

    `spread` is an empirical distribution of log errors, so the returned band is
    asymmetric in volatility units -- wider above than below, which is the shape
    realized volatility actually has.
    """
    if not np.isfinite(centre) or spread.size < 20:
        return dict.fromkeys(quantiles, float("nan"))
    offsets = np.quantile(spread, quantiles)
    return {q: float(np.exp(centre + offset))
            for q, offset in zip(quantiles, offsets, strict=True)}


def _fit_har(log_vol: np.ndarray, horizon: int = HORIZON
             ) -> tuple[np.ndarray, np.ndarray] | None:
    """Least squares on daily, weekly and monthly log-volatility components.

    Returns the coefficients and the in-sample residuals; the residual
    distribution becomes the forecast's interval. Residuals from a fit are
    optimistic about spread, which is a reason to prefer wider baselines rather
    than to distrust the comparison -- it makes HAR's intervals harder to beat,
    not easier.
    """
    longest = max(HAR_LAGS)
    rows, targets = [], []
    for t in range(longest, len(log_vol) - horizon):
        rows.append([1.0] + [float(np.mean(log_vol[t - lag + 1:t + 1]))
                             for lag in HAR_LAGS])
        targets.append(float(log_vol[t + horizon]))
    if len(rows) < 60:
        return None
    design = np.array(rows)
    y = np.array(targets)
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    return coefficients, y - design @ coefficients


def baseline_forecast(name: str, history: np.ndarray,
                      horizon: int = HORIZON) -> dict[float, float]:
    """Quantile forecast from one baseline, given that issuer's history only.

    `history` is the trailing-volatility series ending before the target window,
    so every one of these is point-in-time by construction: there is no way to
    reach a future observation from inside this function.
    """
    usable = history[np.isfinite(history) & (history > 0)]
    if usable.size < MIN_HISTORY // 2:
        return dict.fromkeys(QUANTILES, float("nan"))
    log_vol = np.log(usable)

    if name == "climatology":
        # No centre and no spread: the issuer's own empirical distribution,
        # quoted directly. Deliberately blind to the present.
        return {q: float(np.exp(np.quantile(log_vol, q))) for q in QUANTILES}

    if name == "random_walk":
        # Carry today forward; the spread is how much this issuer's volatility
        # has historically moved over one horizon.
        changes = log_vol[horizon:] - log_vol[:-horizon]
        return _log_quantiles(float(log_vol[-1]), changes)

    if name == "har":
        fitted = _fit_har(log_vol, horizon)
        if fitted is None:
            return dict.fromkeys(QUANTILES, float("nan"))
        coefficients, residuals = fitted
        row = np.array([1.0] + [float(np.mean(log_vol[-lag:])) for lag in HAR_LAGS])
        return _log_quantiles(float(row @ coefficients), residuals)

    raise ValueError(f"unknown baseline: {name!r}")


def pinball_loss(actual: np.ndarray, forecast: np.ndarray, quantile: float) -> float:
    """The scoring rule a quantile forecast is actually accountable to.

    Under-forecasting is penalised by `q` and over-forecasting by `1 - q`, so the
    loss is minimised exactly when the forecast is that quantile of the
    predictive distribution. Averaging it over several levels scores the whole
    band rather than the median alone.
    """
    error = actual - forecast
    usable = np.isfinite(error)
    if not usable.any():
        return float("nan")
    error = error[usable]
    return float(np.mean(np.maximum(quantile * error, (quantile - 1) * error)))


def coverage(actual: np.ndarray, low: np.ndarray, high: np.ndarray) -> float:
    """Share of outcomes inside the band. The number the band claims about itself."""
    usable = np.isfinite(actual) & np.isfinite(low) & np.isfinite(high)
    if not usable.any():
        return float("nan")
    return float(np.mean((actual[usable] >= low[usable])
                         & (actual[usable] <= high[usable])))


def score_forecasts(frame: pd.DataFrame, quantiles=QUANTILES) -> dict:
    """Every metric that decides whether a forecast is usable, from one frame.

    Expects `actual` and one column per quantile named `q10`, `q50` and so on.
    Interval width is reported beside coverage because they trade against each
    other: an interval from zero to infinity has perfect coverage, and reporting
    the two together is what stops that from looking like success.
    """
    actual = frame["actual"].to_numpy(float)
    columns = {q: f"q{int(q * 100)}" for q in quantiles}
    missing = [c for c in columns.values() if c not in frame.columns]
    if missing:
        raise KeyError(f"forecast frame is missing {missing}")

    losses = {q: pinball_loss(actual, frame[columns[q]].to_numpy(float), q)
              for q in quantiles}
    median = frame[columns[0.5]].to_numpy(float)
    scored = np.isfinite(actual) & np.isfinite(median)
    return {
        "n_scored": int(scored.sum()),
        "pinball_mean": float(np.mean(list(losses.values()))),
        "pinball_by_quantile": {f"q{int(q * 100)}": v for q, v in losses.items()},
        "mae_median": float(np.mean(np.abs(actual[scored] - median[scored])))
        if scored.any() else float("nan"),
        "coverage_50": coverage(actual, frame[columns[0.25]].to_numpy(float),
                                frame[columns[0.75]].to_numpy(float)),
        "coverage_80": coverage(actual, frame[columns[0.1]].to_numpy(float),
                                frame[columns[0.9]].to_numpy(float)),
        "width_80": float(np.nanmean(frame[columns[0.9]].to_numpy(float)
                                     - frame[columns[0.1]].to_numpy(float))),
        "median_actual": float(np.nanmedian(actual)),
    }


def coverage_by_regime(frame: pd.DataFrame, regimes: pd.Series,
                       quantiles=QUANTILES) -> pd.DataFrame:
    """Coverage inside each volatility regime, because the average hides the tail.

    A forecaster can hit 80% overall by being too wide in calm markets and too
    narrow in turbulent ones, which is precisely backwards for a risk card: the
    turbulent regime is the one a reader consults it about.
    """
    rows = []
    for name, index in regimes.groupby(regimes, sort=False).groups.items():
        group = frame.loc[frame.index.intersection(index)]
        if group.empty:
            continue
        scored = score_forecasts(group, quantiles)
        rows.append({"regime": name, "filings": scored["n_scored"],
                     "median_actual": scored["median_actual"],
                     "coverage_50": scored["coverage_50"],
                     "coverage_80": scored["coverage_80"],
                     "width_80": scored["width_80"],
                     "pinball_mean": scored["pinball_mean"]})
    return pd.DataFrame(rows)


def build_forecast_frame(events: pd.DataFrame, returns: pd.DataFrame,
                         horizon: int = HORIZON) -> tuple[pd.DataFrame, dict]:
    """One row per filing: the target, the regime it sits in, and its context.

    Returns the frame and a dict of context series keyed by `event_id`. The
    contexts are handed out rather than kept because the only consumer is the
    optional foundation model, and building them here keeps the point-in-time
    rule -- history ends at `anchor - 1` -- in one place instead of two.

    Rows whose target window runs past the end of the price data are kept with a
    NaN target and dropped at scoring time, so the count of filings that could
    not be scored stays visible instead of silently shrinking the sample.
    """
    panel = VolatilityPanel.build(returns)
    frame = events[["event_id", "ticker", "entry_session"]].copy()
    frame["entry_session"] = pd.to_datetime(frame["entry_session"])

    contexts: dict[str, np.ndarray] = {}
    rows = []
    for event_id, ticker, session in frame.itertuples(index=False):
        anchor = panel.position.get(session)
        if anchor is None or anchor < 1:
            continue
        # History stops here. Everything downstream reads this series, so there
        # is exactly one line in this module that decides what the forecaster is
        # allowed to know, and this is it.
        history = panel.trailing_series(ticker, anchor - 1, horizon)
        if history.size < MIN_HISTORY // 2:
            continue
        contexts[event_id] = history
        rows.append({
            "event_id": event_id,
            "ticker": ticker,
            "entry_session": session,
            "trailing_vol": float(history[-1]),
            "actual": panel.forward_volatility(ticker, anchor, horizon),
        })

    out = pd.DataFrame(rows).set_index("event_id") if rows else pd.DataFrame(
        columns=["ticker", "entry_session", "trailing_vol", "actual"])
    return out, contexts


def volatility_regime(frame: pd.DataFrame) -> pd.Series:
    """Which third of the sample's trailing volatility each filing sits in.

    Cut on the whole sample rather than expanding, because this labels rows for
    *reporting* and never feeds a forecast. Using a point-in-time cut here would
    make the three groups mean different things at different dates, which is
    worse for a table whose job is to be read across.
    """
    trailing = frame["trailing_vol"]
    try:
        bands = pd.qcut(trailing, 3, labels=["calm", "ordinary", "turbulent"])
    except ValueError:  # too few distinct values to cut
        return pd.Series("all", index=frame.index)
    return bands.astype(str)


def baseline_frame(frame: pd.DataFrame, contexts: dict[str, np.ndarray],
                   name: str, horizon: int = HORIZON) -> pd.DataFrame:
    """Quantile forecasts from one baseline, aligned to `frame`."""
    rows = []
    for event_id in frame.index:
        context = contexts.get(event_id)
        quantiles = (baseline_forecast(name, context, horizon)
                     if context is not None
                     else dict.fromkeys(QUANTILES, float("nan")))
        rows.append({f"q{int(q * 100)}": v for q, v in quantiles.items()})
    out = pd.DataFrame(rows, index=frame.index)
    out["actual"] = frame["actual"]
    return out


def compare(frame: pd.DataFrame, forecasts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Every forecaster on the same filings, scored the same way.

    Restricted to rows every forecaster produced, so the comparison cannot be won
    by declining to answer on the hard ones.
    """
    if not forecasts:
        return pd.DataFrame()
    common = frame.index[frame["actual"].notna()]
    for table in forecasts.values():
        common = common.intersection(table.index[table["q50"].notna()])

    rows = []
    for name, table in forecasts.items():
        scored = score_forecasts(table.loc[common])
        rows.append({
            "forecaster": name,
            "filings": scored["n_scored"],
            "pinball_mean": scored["pinball_mean"],
            "mae_median": scored["mae_median"],
            "coverage_50": scored["coverage_50"],
            "coverage_80": scored["coverage_80"],
            "width_80": scored["width_80"],
        })
    return pd.DataFrame(rows)
