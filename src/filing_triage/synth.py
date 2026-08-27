"""A synthetic corpus that behaves like the real one.

The pipeline should be runnable by anyone who clones the repository, with no SEC
credentials, no vendor account and no network. So the demo path generates its own
world -- and generates it with the specific properties the project is about:

  * filings land on the real NYSE calendar, and about 80% of them arrive outside
    market hours, as 8-Ks actually do
  * the price reaction happens on the first session that OPENS after the
    acceptance time, never before -- so any pipeline that enters earlier is
    reaching for a move that had not happened yet
  * most of that reaction arrives as an overnight gap rather than intraday,
    because the filing is public before the session opens. A close-to-close
    label collects that gap; an open-anchored one cannot. Without this the
    synthetic world cannot express the difference at all, and the two
    conventions score identically on it
  * materiality is driven by the item code and by how unusual the language is,
    buried under enough noise that the achievable ranking performance is modest,
    which is the honest outcome
  * the index gains and loses members, so survivorship bias has something to bite

Numbers produced here are illustrative. `make ingest` replaces all of it with
real EDGAR filings and real prices; the pipeline code does not change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from filing_triage.pit import CALENDAR, ET

# Item codes with their share of 8-K filings and how much they typically move a
# stock, in units of the issuer's own daily noise. Roughly matches the real
# distribution: earnings and "other events" dominate, bankruptcies are rare and loud.
ITEM_PROFILE = {
    "2.02": (0.24, 2.6),   # earnings
    "8.01": (0.20, 0.7),   # other events
    "5.02": (0.14, 1.3),   # officer/director change
    "7.01": (0.11, 0.9),   # Reg FD
    "1.01": (0.09, 1.1),   # material agreement
    "5.07": (0.07, 0.3),   # shareholder vote results
    "2.01": (0.05, 1.6),   # acquisition or disposal
    "3.02": (0.04, 0.8),   # unregistered equity sale
    "2.05": (0.03, 1.4),   # exit/disposal costs
    "4.02": (0.02, 2.9),   # prior statements not reliable
    "1.03": (0.01, 4.0),   # bankruptcy
}

BOILERPLATE = [
    "the registrant furnished the following information pursuant to item {item} of form 8-K",
    ("this current report contains forward looking statements within the meaning of the "
     "private securities litigation reform act of 1995"),
    ("the information in this report shall not be deemed filed for purposes of section 18 "
     "of the securities exchange act of 1934"),
    ("a copy of the press release is attached hereto as exhibit 99.1 and incorporated "
     "herein by reference"),
]

NOVEL_PHRASES = [
    "the board initiated a review of strategic alternatives including a possible sale",
    "the company identified a material weakness in internal control over financial reporting",
    "the chief financial officer notified the board of an intention to resign",
    "the registrant received a subpoena from the enforcement division",
    "manufacturing at the facility was suspended following an incident",
    "the previously announced transaction was terminated by mutual agreement",
    "full year guidance was withdrawn pending completion of the review",
    "a definitive agreement was executed to acquire the outstanding equity interests",
    "the credit agreement was amended to waive compliance with the leverage covenant",
    "an impairment charge was recorded against goodwill in the reporting unit",
]


@dataclass
class SyntheticWorld:
    events: pd.DataFrame
    prices: pd.DataFrame
    membership: pd.DataFrame


def generate(n_issuers: int = 120, start: date = date(2022, 1, 3),
             end: date = date(2024, 12, 31), seed: int = 20240719) -> SyntheticWorld:
    rng = np.random.default_rng(seed)
    sessions = CALENDAR.sessions_between(start, end)
    issuers = _make_issuers(n_issuers, rng)

    membership = _make_membership(issuers, sessions, rng)
    events = _make_events(issuers, sessions, membership, rng)
    prices = _make_prices(issuers, sessions, events, rng)
    return SyntheticWorld(events=events, prices=prices, membership=membership)


# --------------------------------------------------------------------------- #
def _make_issuers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    return pd.DataFrame({
        "ticker": [f"SYN{i:03d}" for i in range(n)],
        "cik": 1_000_000 + np.arange(n),
        "name": [f"Synthetic Issuer {i:03d} Inc." for i in range(n)],
        "beta": rng.normal(1.0, 0.35, n).clip(0.2, 2.2),
        "idio_vol": rng.uniform(0.010, 0.032, n),
        # 8-Ks per session per issuer. Calibrated so the daily queue is as
        # crowded as a real one: large caps file roughly 10-14 8-Ks a year, so
        # a 300-issuer universe puts ~14 filings a session in front of the
        # analyst. Too few and "read the top 5" is just "read everything",
        # which makes the product metric meaningless.
        "filing_rate": rng.uniform(0.020, 0.075, n),
        "price0": rng.uniform(18, 320, n),
    })


def _make_membership(issuers: pd.DataFrame, sessions: list[date],
                     rng: np.random.Generator) -> pd.DataFrame:
    """Most issuers are in the index throughout; some join late, some drop out.

    Without the leavers there is no survivorship bias to detect, and the guard
    that catches it would never have anything to catch.
    """
    first = sessions[0]
    rows = []
    for issuer in issuers.itertuples():
        start, end = first, None
        roll = rng.random()
        if roll < 0.10:                                  # joined partway through
            start = sessions[rng.integers(60, len(sessions) // 2)]
        elif roll < 0.20:                                # dropped out partway through
            end = sessions[rng.integers(len(sessions) // 2, len(sessions) - 30)]
        rows.append({"ticker": issuer.ticker, "cik": issuer.cik, "name": issuer.name,
                     "start_date": start, "end_date": end})
    membership = pd.DataFrame(rows)
    membership.loc[len(membership)] = {
        "ticker": "SPY", "cik": 884394, "name": "SPDR S&P 500 ETF Trust",
        "start_date": first, "end_date": None,
    }
    return membership


def _make_events(issuers: pd.DataFrame, sessions: list[date], membership: pd.DataFrame,
                 rng: np.random.Generator) -> pd.DataFrame:
    codes = list(ITEM_PROFILE)
    weights = np.array([ITEM_PROFILE[c][0] for c in codes])
    weights = weights / weights.sum()

    spans = membership.set_index("ticker")[["start_date", "end_date"]]
    rows = []
    for issuer in issuers.itertuples():
        n = rng.poisson(issuer.filing_rate * len(sessions))
        picks = rng.choice(len(sessions), size=min(n, len(sessions)), replace=False)
        for position in sorted(picks):
            day = sessions[position]
            acceptance = _acceptance_time(day, rng)
            item = rng.choice(codes, p=weights)
            items = f"{item},9.01" if rng.random() < 0.45 else item
            novelty_draw = float(rng.beta(1.6, 4.0))
            rows.append({
                "ticker": issuer.ticker,
                "cik": issuer.cik,
                "items": items,
                "acceptance_time": acceptance,
                "filing_date": acceptance.date(),
                "period_of_report": day - timedelta(days=int(rng.integers(1, 75))),
                "primary_document": "a8k.htm",
                "truth_item": item,
                "truth_novelty": novelty_draw,
                "text": _make_text(item, novelty_draw, rng),
                "truth_in_index": _in_index(spans, issuer.ticker, day),
            })

    events = pd.DataFrame(rows).sort_values("acceptance_time").reset_index(drop=True)
    events["accession"] = [f"{c:010d}-24-{i:06d}"
                           for i, c in enumerate(events["cik"], start=1)]
    events["event_id"] = events["accession"]
    events["form"] = "8-K"
    return events


def _in_index(spans: pd.DataFrame, ticker: str, day: date) -> bool:
    start, end = spans.loc[ticker, "start_date"], spans.loc[ticker, "end_date"]
    return bool(day >= start and (end is None or pd.isna(end) or day <= end))


def _acceptance_time(day: date, rng: np.random.Generator) -> datetime:
    """8-Ks cluster after the close and before the open, not during the session."""
    roll = rng.random()
    if roll < 0.55:                                     # after the close
        hour, minute = 16 + int(rng.integers(0, 5)), int(rng.integers(0, 60))
    elif roll < 0.80:                                   # before the open
        hour, minute = 6 + int(rng.integers(0, 3)), int(rng.integers(0, 60))
    else:                                               # during the session
        hour, minute = 9 + int(rng.integers(1, 7)), int(rng.integers(0, 60))
    return datetime(day.year, day.month, day.day, min(hour, 23), minute, tzinfo=ET)


def _make_text(item: str, novelty: float, rng: np.random.Generator) -> str:
    """Boilerplate plus, occasionally, something actually new to say."""
    parts = [line.format(item=item) for line in BOILERPLATE]
    n_novel = round(novelty * 5)
    if n_novel:
        parts += list(rng.choice(NOVEL_PHRASES, size=min(n_novel, len(NOVEL_PHRASES)),
                                 replace=False))
    rng.shuffle(parts)
    return " ".join(parts)


# What share of a day's move has already happened by the time the market opens.
#
# ORDINARY_GAP_SHARE is roughly right for large-cap US equities. EVENT_GAP_SHARE
# is higher on purpose and is the honest consequence of the entry rule: the
# filing is public before the entry session opens, so the market prices most of
# it into the opening print. That is precisely the part a reader who enters at
# the open cannot capture -- and precisely the part a close-to-close event
# window hands back to them for free.
ORDINARY_GAP_SHARE = 0.35
EVENT_GAP_SHARE = 0.75


def _make_prices(issuers: pd.DataFrame, sessions: list[date], events: pd.DataFrame,
                 rng: np.random.Generator) -> pd.DataFrame:
    index = {day: i for i, day in enumerate(sessions)}
    n_days = len(sessions)
    market = rng.normal(0.0003, 0.010, n_days)

    # Where each event's move lands: the first session that OPENS after the
    # acceptance time. This single line is the ground truth the whole project is
    # organised around -- a pipeline that enters earlier is reaching into the future.
    shocks: dict[tuple[str, int], float] = {}
    volume_shocks: dict[tuple[str, int], float] = {}
    for event in events.itertuples():
        entry = _first_open_after(event.acceptance_time, sessions)
        if entry is None:
            continue
        base = ITEM_PROFILE[event.truth_item][1]
        magnitude = base * (0.55 + 1.5 * event.truth_novelty) * abs(rng.normal(1.0, 0.55))
        direction = 1.0 if rng.random() < 0.5 else -1.0
        shocks[(event.ticker, index[entry])] = direction * magnitude
        volume_shocks[(event.ticker, index[entry])] = 0.5 + 1.4 * magnitude

    frames = [_market_frame(sessions, market, rng)]
    for issuer in issuers.itertuples():
        idio = rng.normal(0, issuer.idio_vol, n_days)
        returns = 0.0002 + issuer.beta * market + idio
        volume = rng.lognormal(np.log(1.4e6), 0.42, n_days)
        shock_component = np.zeros(n_days)
        for day_index in range(n_days):
            shock = shocks.get((issuer.ticker, day_index))
            if shock is not None:
                shock_component[day_index] = shock * issuer.idio_vol
                returns[day_index] += shock_component[day_index]
                volume[day_index] *= 1.0 + volume_shocks[(issuer.ticker, day_index)]
        close = issuer.price0 * np.cumprod(1.0 + returns)
        frames.append(_price_frame(issuer.ticker, sessions, close, volume, rng,
                                   returns=returns, shock=shock_component))

    return pd.concat(frames, ignore_index=True)


def _first_open_after(acceptance: datetime, sessions: list[date]) -> date | None:
    """The synthetic world's own copy of the entry rule, kept independent of
    `TradingClock` so the tests are not checking the clock against itself."""
    for day in sessions:
        if datetime.combine(day, datetime.min.time(), tzinfo=ET).replace(
                hour=9, minute=30) >= acceptance:
            return day
    return None


def _market_frame(sessions: list[date], market: np.ndarray,
                  rng: np.random.Generator) -> pd.DataFrame:
    close = 450.0 * np.cumprod(1.0 + market)
    volume = rng.lognormal(np.log(7.5e7), 0.28, len(sessions))
    return _price_frame("SPY", sessions, close, volume, rng,
                        returns=market, shock=np.zeros(len(sessions)))


def _price_frame(ticker: str, sessions: list[date], close: np.ndarray,
                 volume: np.ndarray, rng: np.random.Generator, *,
                 returns: np.ndarray, shock: np.ndarray) -> pd.DataFrame:
    """Build the OHLC frame, splitting each day's move across the opening bell.

    The open used to be the day's close plus a rounding wobble, which made
    open-to-close returns pure noise and left the corpus unable to distinguish
    the two event-window conventions. Here the open is the *previous* close
    carried forward by that day's overnight share, so the remaining move is
    genuinely intraday and `close / open - 1` carries real information.

    The filing's shock and the day's ordinary return are split *separately*, and
    that separation is load-bearing rather than fussy. Give the whole event-day
    return the high event share and the issuer's systematic move gets split
    differently from the benchmark's on exactly those days -- so the market model
    subtracts a beta fitted on close-to-close returns from an intraday market
    return on a different scale, and the residual picks up a large spurious
    market term. The measured "reaction" then tracks whatever the index did that
    morning instead of the filing. Only the shock is unusually front-loaded.
    """
    ordinary = returns - shock
    open_ = np.empty(len(close))
    overnight = (ORDINARY_GAP_SHARE * ordinary + EVENT_GAP_SHARE * shock
                 + rng.normal(0, 0.0015, len(close)))
    open_[1:] = close[:-1] * (1.0 + overnight[1:])
    # No prior close for the first session; there is no gap to model.
    open_[0] = close[0] * (1.0 - (1.0 - ORDINARY_GAP_SHARE) * ordinary[0])
    # A synthetic price must stay a price. Magnitudes here never approach zero,
    # but a non-positive open would silently become a NaN return downstream.
    open_ = np.maximum(open_, 0.01)
    spread = np.abs(rng.normal(0, 0.004, len(close)))
    return pd.DataFrame({
        "ticker": ticker,
        "date": sessions,
        "open": open_,
        "high": np.maximum(open_, close) * (1 + spread),
        "low": np.minimum(open_, close) * (1 - spread),
        "close": close,
        "volume": volume,
    })
