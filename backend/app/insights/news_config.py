"""News provider configuration — backend env only (never NEXT_PUBLIC_*)."""

from __future__ import annotations

import os
from typing import Optional

from app.insights.finnhub_provider import FinnhubNewsProvider
from app.insights.news_cache import CachedNewsProvider, DEFAULT_TTL_SECONDS
from app.insights.news_port import NewsProvider, NewsProviderNotConfigured
from app.insights.yfinance_provider import YFinanceNewsProvider

_provider_override: Optional[NewsProvider] = None
_cached_singleton: Optional[CachedNewsProvider] = None


def finnhub_api_key(*, environ: dict[str, str] | None = None) -> str:
    env = environ if environ is not None else dict(os.environ)
    return (env.get("FINNHUB_API_KEY") or "").strip()


def has_finnhub_key(*, environ: dict[str, str] | None = None) -> bool:
    return bool(finnhub_api_key(environ=environ))


def set_news_provider_override(provider: Optional[NewsProvider]) -> None:
    """Tests inject FixtureNewsProvider (or any stub) here."""
    global _provider_override, _cached_singleton
    _provider_override = provider
    _cached_singleton = None


def resolve_news_provider(
    *,
    environ: dict[str, str] | None = None,
    use_cache: bool = True,
) -> NewsProvider:
    """
    Prefer Finnhub when ``FINNHUB_API_KEY`` is set; otherwise yfinance fallback.

    Results are wrapped in a ~10 minute in-memory cache by default.
    """
    global _cached_singleton

    if _provider_override is not None:
        return _provider_override

    if has_finnhub_key(environ=environ):
        try:
            inner: NewsProvider = FinnhubNewsProvider(
                api_key=finnhub_api_key(environ=environ)
            )
            name = "finnhub"
        except NewsProviderNotConfigured:
            inner = YFinanceNewsProvider()
            name = "yfinance"
    else:
        inner = YFinanceNewsProvider()
        name = "yfinance"

    if not use_cache:
        return inner

    if _cached_singleton is None or _cached_singleton.provider_name != name:
        _cached_singleton = CachedNewsProvider(
            inner,
            ttl_seconds=DEFAULT_TTL_SECONDS,
            provider_name=name,
        )
    return _cached_singleton


def active_news_provider_name(*, environ: dict[str, str] | None = None) -> str:
    if _provider_override is not None:
        return "override"
    return "finnhub" if has_finnhub_key(environ=environ) else "yfinance"
