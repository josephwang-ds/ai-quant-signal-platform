"""Offline fixture news provider — deterministic headlines for CI."""

from __future__ import annotations

from datetime import datetime, timezone

from app.insights.news_port import NewsItem


class FixtureNewsProvider:
    """Fixed headlines; no network. Inject in tests via ``resolve_news_provider`` override."""

    def __init__(self, items: list[NewsItem] | None = None) -> None:
        self._items = items if items is not None else _default_fixtures()

    def fetch_recent(self, ticker: str, limit: int = 10) -> list[NewsItem]:
        symbol = ticker.upper().strip() or "TICKER"
        # Re-tag ids with the requested ticker so tests can assert symbol binding.
        tagged = [
            NewsItem(
                id=f"{symbol}-{item.id}",
                headline=item.headline.replace("{TICKER}", symbol),
                summary=item.summary.replace("{TICKER}", symbol),
                url=item.url,
                source=item.source,
                published_at=item.published_at,
            )
            for item in self._items
        ]
        return tagged[: max(limit, 0)]


def _default_fixtures() -> list[NewsItem]:
    base = datetime(2026, 7, 20, 14, 30, tzinfo=timezone.utc)
    return [
        NewsItem(
            id="fx-1",
            headline="{TICKER} shares surge after earnings beat estimates",
            summary="Quarterly results topped consensus; management raised guidance.",
            url="https://example.test/news/earnings-beat",
            source="FixtureWire",
            published_at=base,
        ),
        NewsItem(
            id="fx-2",
            headline="Regulators open probe into {TICKER} disclosure practices",
            summary="An inquiry was announced; the company said it would cooperate.",
            url="https://example.test/news/probe",
            source="FixtureWire",
            published_at=base.replace(hour=12),
        ),
        NewsItem(
            id="fx-3",
            headline="Analysts remain neutral on {TICKER} ahead of product event",
            summary="Street commentary was mixed with no change to consensus rating.",
            url="https://example.test/news/neutral",
            source="FixtureWire",
            published_at=base.replace(hour=10),
        ),
        NewsItem(
            id="fx-4",
            headline="{TICKER} expands partnership with cloud vendor",
            summary="A multi-year collaboration was announced without financial terms.",
            url="https://example.test/news/partnership",
            source="FixtureWire",
            published_at=base.replace(day=19),
        ),
    ]
