"""Finnhub company-news provider — stdlib urllib only (no Finnhub SDK)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from app.insights.news_port import (
    NewsItem,
    NewsProviderError,
    NewsProviderNotConfigured,
)

FINNHUB_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"
DEFAULT_LOOKBACK_DAYS = 7


class FinnhubNewsProvider:
    """
    GET /company-news?symbol=&from=&to=&token=

    API key is read from ``FINNHUB_API_KEY`` (backend env only — never NEXT_PUBLIC_*).
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        timeout_seconds: float = 20.0,
    ) -> None:
        key = (api_key if api_key is not None else os.environ.get("FINNHUB_API_KEY", "")).strip()
        if not key:
            raise NewsProviderNotConfigured(
                "FINNHUB_API_KEY is not configured for this deployment."
            )
        self.api_key = key
        self.lookback_days = max(1, int(lookback_days))
        self.timeout_seconds = timeout_seconds

    def fetch_recent(self, ticker: str, limit: int = 10) -> list[NewsItem]:
        symbol = ticker.upper().strip()
        if not symbol:
            return []
        to_day = date.today()
        from_day = to_day - timedelta(days=self.lookback_days)
        params = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "from": from_day.isoformat(),
                "to": to_day.isoformat(),
                "token": self.api_key,
            }
        )
        url = f"{FINNHUB_COMPANY_NEWS_URL}?{params}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "ai-quant-insights/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise NewsProviderError(
                f"Finnhub company-news HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            raise NewsProviderError("Finnhub company-news unreachable.") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NewsProviderError(
                "Finnhub company-news returned non-JSON."
            ) from exc

        if not isinstance(payload, list):
            raise NewsProviderError(
                "Finnhub company-news returned an unexpected payload."
            )

        items: list[NewsItem] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            parsed = _parse_finnhub_entry(entry, fallback_symbol=symbol)
            if parsed is None:
                continue
            items.append(parsed)
            if len(items) >= max(limit, 0):
                break
        return items


def _parse_finnhub_entry(
    entry: dict[str, Any], *, fallback_symbol: str
) -> Optional[NewsItem]:
    headline = str(entry.get("headline") or "").strip()
    if not headline:
        return None
    raw_id = entry.get("id")
    item_id = str(raw_id).strip() if raw_id is not None else ""
    if not item_id:
        item_id = f"finnhub-{fallback_symbol}-{abs(hash(headline)) % 10_000_000}"

    published_at: Optional[datetime] = None
    ts = entry.get("datetime")
    if isinstance(ts, (int, float)) and ts > 0:
        published_at = datetime.fromtimestamp(float(ts), tz=timezone.utc)

    return NewsItem(
        id=item_id,
        headline=headline[:400],
        summary=str(entry.get("summary") or "").strip()[:800],
        url=str(entry.get("url") or "").strip(),
        source=str(entry.get("source") or "Finnhub").strip() or "Finnhub",
        published_at=published_at,
    )
