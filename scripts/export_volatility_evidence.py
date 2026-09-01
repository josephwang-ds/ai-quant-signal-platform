"""The volatility-forecast experiment, exported as evidence rather than a claim.

Plan §5.5 proposes a card: a median forecast and an 80% band for the issuer's
next twenty sessions, shown after its latest filing. It also sets the gate --
*do not ship the card unless the out-of-sample intervals are calibrated enough to
be useful* -- and this script is what decides that, by scoring the foundation
model against three baselines on the same filings, the same horizon, and the same
scoring rules.

The comparison is only worth reporting if the challenger was given its best shot,
so Chronos forecasts in log space, the same space the baselines work in, which is
also the better of its two configurations when measured.

Everything here is a single pass over cached forecasts. The model runs in
`scripts/build_volatility_cache.py`; nothing in this file loads one.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from filing_triage import chronos_model
from filing_triage.fingerprint import environment
from filing_triage.ingest.prices import load_prices, to_returns
from filing_triage.pit import TradingClock
from filing_triage.uncertainty import paired_pinball_difference
from filing_triage.volatility import (
    BASELINES,
    HORIZON,
    QUANTILES,
    baseline_frame,
    build_forecast_frame,
    compare,
    coverage_by_regime,
    score_forecasts,
    volatility_regime,
)

# The baseline every other forecaster is measured against. HAR is the standard
# workhorse of the volatility literature and, on this sample, the one to beat.
REFERENCE = "har"

# What "calibrated enough to be useful" is allowed to mean, fixed before the
# numbers are read. A nominal 80% band holding 75% of outcomes is a band that
# will be wrong one time in four while claiming one in five.
COVERAGE_TOLERANCE = 0.03


def _forecasts(frame, contexts, cache) -> dict[str, pd.DataFrame]:
    forecasts = {name: baseline_frame(frame, contexts, name) for name in BASELINES}
    if not cache.index["keys"]:
        return forecasts
    rows = [{f"q{int(q * 100)}": v for q, v in
             chronos_model.cached_forecast(contexts[event_id], cache).items()}
            for event_id in frame.index]
    table = pd.DataFrame(rows, index=frame.index)
    table["actual"] = frame["actual"]
    forecasts["chronos"] = table
    return forecasts


def _gate(scored: dict) -> dict:
    """Whether a forecaster's own bands mean what they say.

    Two separate questions, kept separate: does the interval cover what it claims
    (a property of the forecaster alone), and does it beat the reference (a
    comparison). A forecaster can pass one and fail the other, and collapsing
    them into a single verdict would hide which.
    """
    return {
        "coverage_50_error": abs(scored["coverage_50"] - 0.50),
        "coverage_80_error": abs(scored["coverage_80"] - 0.80),
        "calibrated": bool(abs(scored["coverage_50"] - 0.50) <= COVERAGE_TOLERANCE
                           and abs(scored["coverage_80"] - 0.80) <= COVERAGE_TOLERANCE),
    }


def _write_cards(path: Path, frame, forecasts, shipped, gates) -> int:
    """One card per issuer, from its most recent filing, or no file at all.

    Written only for the forecaster that passed the calibration gate. If none
    did, the file is removed rather than left stale: a card whose evidence stopped
    supporting it is worse than a missing card, because the page around it still
    looks finished.

    The card carries the issuer's own historical median beside the forecast,
    because "28%" means nothing without knowing that this issuer usually runs at
    22%. That comparison is the entire point of the card, and it is the same
    issuer-relative argument the rest of the project makes.
    """
    if shipped is None:
        path.unlink(missing_ok=True)
        return 0

    forecast = forecasts[shipped]
    cards = {}
    for ticker, group in frame.groupby("ticker", sort=False):
        latest = group["entry_session"].idxmax()
        row = forecast.loc[latest] if latest in forecast.index else None
        if row is None or not pd.notna(row.get("q50")):
            continue
        history = group["trailing_vol"].dropna()
        if history.empty:
            continue
        issuer_median = float(history.median())
        median = float(row["q50"])
        cards[ticker] = {
            "as_of": str(group.loc[latest, "entry_session"].date()),
            "horizon_sessions": HORIZON,
            "median": median,
            "band_low": float(row["q10"]),
            "band_high": float(row["q90"]),
            "issuer_median": issuer_median,
            # A ratio, not a difference: 6 points on a 15% stock and on a 60%
            # stock are not the same news.
            "vs_issuer": median / issuer_median if issuer_median > 0 else None,
            "state": _risk_state(median, issuer_median),
            "forecaster": shipped,
        }
    payload = {
        "schema_version": "volatility-cards.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "forecaster": shipped,
        # The bands' measured coverage, not the gap from nominal. The page states
        # this next to the card, and a card that quoted its own error as its
        # coverage would claim 2% where it means 77%.
        "coverage_50": gates[shipped]["coverage_50"],
        "coverage_80": gates[shipped]["coverage_80"],
        "cards": cards,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    return len(cards)


def _risk_state(median: float, issuer_median: float) -> str:
    """Plain words for the ratio, with a band around 1.0 that means 'no news'.

    The thresholds are deliberately wide. A forecast 5% above an issuer's usual
    level is not a finding, and a card that said "elevated" on that would be
    crying wolf every quarter.
    """
    if issuer_median <= 0:
        return "unknown"
    ratio = median / issuer_median
    if ratio >= 1.35:
        return "elevated"
    if ratio >= 1.15:
        return "slightly elevated"
    if ratio <= 0.75:
        return "unusually calm"
    return "typical for this issuer"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=Path("data/build"))
    parser.add_argument("--out", type=Path, default=Path("evidence/real_run"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    events = pd.read_parquet(args.build / "events.parquet")
    events["entry_session"] = events["acceptance_time"].map(
        TradingClock().entry_session)
    returns = to_returns(load_prices(args.build / "prices.parquet"))

    frame, contexts = build_forecast_frame(events, returns)
    cache = chronos_model.ForecastCache(args.build / "volatility_cache")
    forecasts = _forecasts(frame, contexts, cache)

    table = compare(frame, forecasts)
    table.to_csv(args.out / "volatility_forecasters.csv", index=False)

    regimes = volatility_regime(frame)
    regime_rows = []
    for name, forecast in forecasts.items():
        rows = coverage_by_regime(forecast, regimes)
        rows.insert(0, "forecaster", name)
        regime_rows.append(rows)
    pd.concat(regime_rows, ignore_index=True).to_csv(
        args.out / "volatility_by_regime.csv", index=False)

    # Paired and session-clustered, like every other comparison in this project.
    # Negative means the challenger loses less than HAR, which is the only way a
    # difference of 0.0014 in pinball loss can be read at all.
    reference = forecasts[REFERENCE]
    differences = []
    for name, forecast in forecasts.items():
        if name == REFERENCE:
            continue
        interval = paired_pinball_difference(
            reference, forecast, frame["entry_session"], QUANTILES)
        differences.append({"forecaster": name, "against": REFERENCE, **interval,
                            "beats_reference": bool(interval["high"] < 0)})
    pd.DataFrame(differences).to_csv(
        args.out / "volatility_paired.csv", index=False)

    gates = {name: _gate(score_forecasts(
        forecast.loc[forecast["actual"].notna() & forecast["q50"].notna()]))
        for name, forecast in forecasts.items()}
    shipped = max(
        (name for name, gate in gates.items() if gate["calibrated"]),
        key=lambda name: -float(
            table.loc[table["forecaster"] == name, "pinball_mean"].iloc[0]),
        default=None)

    payload = {
        "schema_version": "volatility.v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "task": {
            "target": "annualised realized volatility over the next "
                      f"{HORIZON} sessions, starting at the entry session",
            "horizon": HORIZON,
            "quantiles": list(QUANTILES),
            "filings": len(frame),
            "scored": int(frame["actual"].notna().sum()),
            "median_actual": float(frame["actual"].median()),
        },
        "reference": REFERENCE,
        "coverage_tolerance": COVERAGE_TOLERANCE,
        "gates": gates,
        "shipped": shipped,
        "foundation_model": cache.fingerprint() if cache.index["keys"] else None,
        "environment": environment(),
    }
    (args.out / "volatility_metrics.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n")

    cards = _write_cards(args.build / "volatility_cards.json", frame, forecasts,
                         shipped, {n: {**g, **score_forecasts(
                             forecasts[n].loc[forecasts[n]["actual"].notna()
                                              & forecasts[n]["q50"].notna()])}
                             for n, g in gates.items()})

    print(f"volatility evidence written to {args.out}")
    print(table.round(4).to_string(index=False))
    print(f"  calibrated: {[n for n, g in gates.items() if g['calibrated']] or 'none'}")
    print(f"  card would use: {shipped or 'nothing -- no forecaster passed the gate'}")
    print(f"  {cards:,} company cards written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
