"""Shared offline test guards for the legacy FastAPI backend suite."""

from __future__ import annotations

import socket
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pytest

from app.data_providers.base import REQUIRED_OHLCV_COLUMNS


def _is_live_test(request: pytest.FixtureRequest) -> bool:
    return request.node.get_closest_marker("live") is not None


def _deterministic_ohlcv(
    ticker: str,
    start_date: str = "2022-01-01",
    end_date: Optional[str] = None,
    data_source: str = "offline-fixture",
) -> pd.DataFrame:
    """Synthetic daily OHLCV long enough for legacy backtest endpoint tests."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) if end_date else pd.Timestamp("2025-06-30")
    if end < start:
        end = start + timedelta(days=120)

    dates = pd.bdate_range(start, end)
    if dates.empty:
        dates = pd.bdate_range(start, periods=120)

    close = pd.Series(100.0 + pd.Series(range(len(dates))) * 0.15, index=dates)
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close - 0.25,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1_000_000,
            "symbol": ticker.upper(),
            "ticker": ticker.upper(),
            "data_source": data_source,
        }
    )
    return frame[REQUIRED_OHLCV_COLUMNS + ["symbol", "ticker", "data_source"]]


def _fake_load_price_data(
    ticker: str,
    start_date: str = "2022-01-01",
    end_date: Optional[str] = None,
    data_source: str = "auto",
) -> pd.DataFrame:
    source = (data_source or "auto").strip().lower()
    if source in {"", "auto", "fallback"}:
        source = "offline-fixture"
    return _deterministic_ohlcv(ticker, start_date, end_date, source)


class _OfflineSocketGuard(socket.socket):
    """Fail closed when offline tests attempt outbound TCP connections."""

    def connect(self, address) -> None:  # type: ignore[override]
        host = address[0] if isinstance(address, tuple) else address
        if host in {"127.0.0.1", "localhost", "::1"}:
            return super().connect(address)
        raise OSError(
            f"Network access blocked in offline tests (attempted connect to {host!r}). "
            "Mark intentional live smoke tests with @pytest.mark.live."
        )


@pytest.fixture(autouse=True)
def offline_test_guards(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Block outbound network and inject deterministic market data unless live."""
    if _is_live_test(request):
        yield
        return

    monkeypatch.setattr(socket, "socket", _OfflineSocketGuard)
    monkeypatch.setattr(
        "app.data_providers.yahoo_provider.load_price_data",
        _fake_load_price_data,
    )
    yield


@pytest.fixture(autouse=True)
def reset_demo_protection_state(monkeypatch: pytest.MonkeyPatch):
    """
    Keep process-local rate/concurrency gates from poisoning the suite.

    Individual protection tests re-enable low limits after this fixture runs.
    """
    from app.security.concurrency import reset_llm_concurrency_for_tests
    from app.security.rate_limit import reset_rate_limiter_for_tests
    from app.security.settings import clear_demo_protection_settings_cache

    # Generous defaults so business-logic tests are not flaky under the
    # single-instance in-memory limiter. Protection tests override these.
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("AGENT_RATE_LIMIT", "10000")
    monkeypatch.setenv("EXPENSIVE_RATE_LIMIT", "10000")
    monkeypatch.setenv("WRITE_RATE_LIMIT", "10000")
    monkeypatch.setenv("READ_RATE_LIMIT", "10000")
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "8")
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()
    reset_llm_concurrency_for_tests()
    yield
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()
    reset_llm_concurrency_for_tests()
