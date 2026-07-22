"""In-memory TTL cache for news fetches — protects free Finnhub quotas."""

from __future__ import annotations

import threading
import time
from typing import Optional

from app.insights.news_port import NewsItem, NewsProvider

DEFAULT_TTL_SECONDS = 10 * 60  # ~10 minutes


class CachedNewsProvider:
    """Wrap any ``NewsProvider`` with a per-ticker TTL cache."""

    def __init__(
        self,
        inner: NewsProvider,
        *,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        provider_name: str = "cached",
    ) -> None:
        self._inner = inner
        self._ttl = max(1.0, float(ttl_seconds))
        self.provider_name = provider_name
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, list[NewsItem]]] = {}

    def fetch_recent(self, ticker: str, limit: int = 10) -> list[NewsItem]:
        key = ticker.upper().strip()
        now = time.monotonic()
        with self._lock:
            hit = self._store.get(key)
            if hit is not None:
                expires_at, items = hit
                if now < expires_at:
                    return list(items[: max(limit, 0)])

        fresh = self._inner.fetch_recent(key, limit=max(limit, 10))
        with self._lock:
            self._store[key] = (now + self._ttl, list(fresh))
            return list(fresh[: max(limit, 0)])

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def cache_get_age_seconds(provider: CachedNewsProvider, ticker: str) -> Optional[float]:
    """Test helper: seconds since cache write, or None on miss."""
    key = ticker.upper().strip()
    with provider._lock:
        hit = provider._store.get(key)
        if hit is None:
            return None
        expires_at, _ = hit
        remaining = expires_at - time.monotonic()
        return max(0.0, provider._ttl - remaining)
