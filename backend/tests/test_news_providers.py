"""News provider port + Finnhub/yfinance/fixture/cache (AIN-1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.insights.finnhub_provider import FinnhubNewsProvider
from app.insights.fixture_provider import FixtureNewsProvider
from app.insights.news_cache import CachedNewsProvider
from app.insights.news_config import (
    has_finnhub_key,
    resolve_news_provider,
    set_news_provider_override,
)
from app.insights.news_port import NewsItem, NewsProviderNotConfigured
from app.insights.news_sentiment import FakeNewsSentimentLlm, analyze_news_sentiment


def test_fixture_provider_returns_tagged_headlines() -> None:
    provider = FixtureNewsProvider()
    items = provider.fetch_recent("aapl", limit=3)
    assert len(items) == 3
    assert all(isinstance(item, NewsItem) for item in items)
    assert items[0].id.startswith("AAPL-")
    assert "AAPL" in items[0].headline
    assert items[0].published_at is not None


def test_finnhub_not_configured_without_key(monkeypatch) -> None:
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with pytest.raises(NewsProviderNotConfigured):
        FinnhubNewsProvider(api_key="")


def test_finnhub_parses_company_news(monkeypatch) -> None:
    payload = [
        {
            "category": "company",
            "datetime": 1_720_000_000,
            "headline": "Acme beats estimates",
            "id": 42,
            "source": "Reuters",
            "summary": "Strong quarter.",
            "url": "https://example.test/a",
        },
        {
            "category": "company",
            "datetime": 1_720_000_100,
            "headline": "",
            "id": 43,
            "source": "Reuters",
            "summary": "skip",
            "url": "https://example.test/b",
        },
    ]

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "app.insights.finnhub_provider.urllib.request.urlopen",
        lambda *args, **kwargs: _Resp(),
    )
    provider = FinnhubNewsProvider(api_key="test-key")
    items = provider.fetch_recent("ACME", limit=5)
    assert len(items) == 1
    assert items[0].headline == "Acme beats estimates"
    assert items[0].source == "Reuters"
    assert items[0].published_at == datetime.fromtimestamp(
        1_720_000_000, tz=timezone.utc
    )


def test_resolve_prefers_finnhub_when_keyed(monkeypatch) -> None:
    set_news_provider_override(None)
    monkeypatch.setenv("FINNHUB_API_KEY", "secret")
    assert has_finnhub_key() is True
    provider = resolve_news_provider(use_cache=False)
    assert isinstance(provider, FinnhubNewsProvider)
    set_news_provider_override(None)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)


def test_resolve_falls_back_to_yfinance_without_key(monkeypatch) -> None:
    set_news_provider_override(None)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = resolve_news_provider(use_cache=False)
    from app.insights.yfinance_provider import YFinanceNewsProvider

    assert isinstance(provider, YFinanceNewsProvider)


def test_cached_provider_hits_ttl() -> None:
    calls = {"n": 0}

    class _Counting(FixtureNewsProvider):
        def fetch_recent(self, ticker: str, limit: int = 10):
            calls["n"] += 1
            return super().fetch_recent(ticker, limit=limit)

    cached = CachedNewsProvider(_Counting(), ttl_seconds=600, provider_name="fixture")
    first = cached.fetch_recent("SPY", limit=2)
    second = cached.fetch_recent("SPY", limit=2)
    assert calls["n"] == 1
    assert first == second


def test_sentiment_uses_injected_fixture_provider() -> None:
    set_news_provider_override(FixtureNewsProvider())
    try:
        out = analyze_news_sentiment(
            ticker="MSFT",
            pasted_news=None,
            llm=FakeNewsSentimentLlm(),
            news_provider=resolve_news_provider(),
            max_headlines=4,
        )
        assert out["ticker"] == "MSFT"
        assert out["headline_count"] >= 1
        assert out["backtest_feature"] is False
    finally:
        set_news_provider_override(None)


def test_render_yaml_lists_finnhub_backend_only() -> None:
    from pathlib import Path

    text = Path(__file__).resolve().parents[2].joinpath("render.yaml").read_text(
        encoding="utf-8"
    )
    assert "FINNHUB_API_KEY" in text
    assert "sync: false" in text
    assert "NEXT_PUBLIC_FINNHUB" not in text
