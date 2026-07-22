"""Qualitative AI insights (current-time panels; not backtest features)."""

from app.insights.news_config import (
    resolve_news_provider,
    set_news_provider_override,
)
from app.insights.news_port import NewsItem, NewsProvider, NewsProviderNotConfigured
from app.insights.sentiment import aggregate, classify_item

__all__ = [
    "NewsItem",
    "NewsProvider",
    "NewsProviderNotConfigured",
    "aggregate",
    "classify_item",
    "resolve_news_provider",
    "set_news_provider_override",
]
