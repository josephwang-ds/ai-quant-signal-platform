from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from filing_triage.config import PipelineConfig
from filing_triage.labels import Panel, SessionGrid, _measure


def test_estimation_window_contains_exact_configured_sessions(monkeypatch) -> None:
    observed_lengths = []

    def capture_window(stock, market):
        observed_lengths.append((len(stock), len(market)))
        return 1.0, 0.0, 0.02

    monkeypatch.setattr("filing_triage.labels._market_model", capture_window)
    sessions = [date(2023, 1, 1) + timedelta(days=index) for index in range(200)]
    market = np.full(200, 0.01)
    panel = Panel(
        ret=np.full(200, 0.012),
        ret_open_to_close=np.full(200, 0.007),
        volume=np.full(200, 1_000.0),
        volume_baseline=np.full(200, 900.0),
    )
    grid = SessionGrid(
        sessions=sessions,
        position={session: index for index, session in enumerate(sessions)},
        market=market,
        market_open_to_close=np.full(200, 0.006),
        panels={},
    )

    measured = _measure(panel, grid, entry=150, config=PipelineConfig())

    assert not isinstance(measured, str)
    assert observed_lengths == [(120, 120)]


def test_default_materiality_cutoff_is_fixed_ex_ante() -> None:
    assert PipelineConfig().reaction_threshold == 2.0
