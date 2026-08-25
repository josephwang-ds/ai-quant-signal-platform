from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from company_lens.reactions import build_filing_reactions


def _event(accession: str, accepted_at: str) -> dict:
    return {
        "ticker": "ABC",
        "accession": accession,
        "acceptance_time": pd.Timestamp(accepted_at, tz="America/New_York"),
    }


def _bar(ticker: str, session: date, move: float) -> dict:
    return {
        "ticker": ticker,
        "date": session,
        "open": 100.0,
        "close": 100.0 * (1.0 + move),
    }


def test_reaction_uses_first_not_yet_open_session() -> None:
    events = pd.DataFrame([_event("after-close", "2024-01-05 17:00")])
    session = date(2024, 1, 8)
    prices = pd.DataFrame(
        [_bar("ABC", session, 0.03), _bar("SPY", session, 0.01)]
    )

    reaction = build_filing_reactions(events, prices, "ABC")["after-close"]

    assert reaction.session == "2024-01-08"
    assert reaction.asset_open_to_close == pytest.approx(0.03)
    assert reaction.benchmark_open_to_close == pytest.approx(0.01)
    assert reaction.benchmark_adjusted_move == pytest.approx(0.02)
    assert reaction.magnitude_percentile is None
    assert reaction.prior_sample_size == 0


def test_reaction_percentile_uses_only_prior_measurable_filings() -> None:
    sessions = [
        date(2024, 1, 8),
        date(2024, 1, 9),
        date(2024, 1, 10),
        date(2024, 1, 11),
        date(2024, 1, 12),
        date(2024, 1, 16),
    ]
    moves = [0.01, -0.02, 0.03, -0.04, 0.05, 0.035]
    events = pd.DataFrame(
        [
            _event(f"filing-{index}", f"{session.isoformat()} 08:00")
            for index, session in enumerate(sessions)
        ]
    )
    prices = pd.DataFrame(
        [
            bar
            for session, move in zip(sessions, moves, strict=True)
            for bar in (_bar("ABC", session, move), _bar("SPY", session, 0.0))
        ]
    )

    before_future = build_filing_reactions(events, prices, "ABC")
    sixth = before_future["filing-5"]

    assert sixth.prior_sample_size == 5
    assert sixth.magnitude_percentile == pytest.approx(0.6)

    future_session = date(2024, 1, 17)
    extended_events = pd.concat(
        [events, pd.DataFrame([_event("filing-6", "2024-01-17 08:00")])],
        ignore_index=True,
    )
    extended_prices = pd.concat(
        [
            prices,
            pd.DataFrame(
                [
                    _bar("ABC", future_session, 0.5),
                    _bar("SPY", future_session, 0.0),
                ]
            ),
        ],
        ignore_index=True,
    )

    after_future = build_filing_reactions(extended_events, extended_prices, "ABC")

    assert after_future["filing-5"] == sixth


def test_reaction_is_omitted_when_same_session_benchmark_bar_is_missing() -> None:
    events = pd.DataFrame([_event("missing", "2024-01-08 08:00")])
    prices = pd.DataFrame([_bar("ABC", date(2024, 1, 8), 0.02)])

    assert build_filing_reactions(events, prices, "ABC") == {}
