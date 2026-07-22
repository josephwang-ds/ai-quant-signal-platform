"""yfinance ticker.news fallback — zero-cost, no Finnhub key required."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.insights.news_port import NewsItem


class YFinanceNewsProvider:
    """
    Best-effort latest headlines via ``yfinance.Ticker(...).news``.

    Current-time only — not a point-in-time historical feed. No sentiment scoring.
    """

    def fetch_recent(self, ticker: str, limit: int = 10) -> list[NewsItem]:
        symbol = ticker.upper().strip()
        if not symbol:
            return []
        try:
            import yfinance as yf
        except ImportError:
            return []
        try:
            raw = getattr(yf.Ticker(symbol), "news", None) or []
        except Exception:
            return []

        items: list[NewsItem] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            parsed = _parse_yfinance_entry(entry, symbol=symbol)
            if parsed is None:
                continue
            items.append(parsed)
            if len(items) >= max(limit, 0):
                break
        return items


def _parse_yfinance_entry(entry: dict[str, Any], *, symbol: str) -> Optional[NewsItem]:
    content = entry.get("content") if isinstance(entry.get("content"), dict) else {}
    headline = str(entry.get("title") or content.get("title") or "").strip()
    if not headline:
        return None

    summary = str(
        entry.get("summary")
        or content.get("summary")
        or entry.get("publisher")
        or ""
    ).strip()
    provider = content.get("provider")
    if isinstance(provider, dict) and not summary:
        summary = str(provider.get("displayName") or "").strip()

    url = str(entry.get("link") or entry.get("url") or "").strip()
    click = content.get("clickThroughUrl")
    if not url and isinstance(click, dict):
        url = str(click.get("url") or "").strip()
    canonical = content.get("canonicalUrl")
    if not url and isinstance(canonical, dict):
        url = str(canonical.get("url") or "").strip()

    source = str(entry.get("publisher") or "").strip()
    if not source and isinstance(provider, dict):
        source = str(provider.get("displayName") or "").strip()
    if not source:
        source = "Yahoo"

    published_at: Optional[datetime] = None
    for key in ("providerPublishTime", "pubDate"):
        ts = entry.get(key)
        if ts is None:
            ts = content.get(key)
        if isinstance(ts, (int, float)) and ts > 0:
            # yfinance may emit seconds or ms
            value = float(ts)
            if value > 1e12:
                value = value / 1000.0
            published_at = datetime.fromtimestamp(value, tz=timezone.utc)
            break
        if isinstance(ts, str) and ts.strip():
            try:
                published_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass

    raw_id = entry.get("uuid") or entry.get("id") or content.get("id")
    item_id = (
        str(raw_id).strip()
        if raw_id
        else f"yf-{symbol}-{abs(hash(headline)) % 10_000_000}"
    )

    return NewsItem(
        id=item_id,
        headline=headline[:400],
        summary=summary[:800],
        url=url,
        source=source,
        published_at=published_at,
    )
