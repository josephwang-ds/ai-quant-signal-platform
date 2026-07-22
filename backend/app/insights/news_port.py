"""News provider port — Application-owned; no vendor SDK imports here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass(frozen=True)
class NewsItem:
    id: str
    headline: str
    summary: str
    url: str
    source: str
    published_at: Optional[datetime]


class NewsProvider(Protocol):
    """Fetch recent company headlines for a qualitative insights panel."""

    def fetch_recent(self, ticker: str, limit: int = 10) -> list[NewsItem]:
        ...


class NewsProviderNotConfigured(Exception):
    """Raised when a required news API key / setting is missing."""

    def __init__(self, message: str = "News provider is not configured.") -> None:
        super().__init__(message)
        self.message = message


class NewsProviderError(Exception):
    """Upstream news fetch failed (network / malformed)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
