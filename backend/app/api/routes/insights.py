"""POST /api/v1/insights/* — qualitative AI panels (not backtest features)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.insights.news_config import set_news_provider_override
from app.insights.news_port import NewsProviderNotConfigured
from app.insights.pipeline import run_news_sentiment_insight
from app.research_copilot.service import resolve_llm_adapter

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

_LLM_UNSET = object()
_llm_override: Any = _LLM_UNSET


def set_insights_llm_override(llm) -> None:
    """Tests inject FakeInsightsSummaryLlm, or ``None`` to force summary=null."""
    global _llm_override
    _llm_override = llm


def clear_insights_llm_override() -> None:
    global _llm_override
    _llm_override = _LLM_UNSET


def get_insights_llm():
    """Return configured Copilot adapter, test override, or ``None`` if unconfigured."""
    if _llm_override is not _LLM_UNSET:
        return _llm_override
    try:
        return resolve_llm_adapter()
    except Exception:
        return None


# Re-export for tests that inject a fixture news provider.
set_insights_news_provider_override = set_news_provider_override


class NewsSentimentRequest(BaseModel):
    ticker: str
    limit: int = Field(default=10, ge=1, le=30)
    use_finbert: bool = False
    paste_text: Optional[str] = Field(
        default=None,
        description="Optional pasted headlines/snippets.",
    )
    # Backward-compatible aliases
    pasted_news: Optional[str] = None
    fetch_latest: bool = True

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker


@router.post("/news-sentiment")
def news_sentiment(request: NewsSentimentRequest) -> dict[str, Any]:
    """
    Live qualitative news sentiment panel.

    Flow: fetch news → deterministic classify → aggregate → optional LLM summary.
    Classification never depends on the LLM. Summary failures soft-fail to null.
    """
    paste = request.paste_text if request.paste_text is not None else request.pasted_news
    try:
        return run_news_sentiment_insight(
            ticker=request.ticker,
            limit=request.limit,
            use_finbert=request.use_finbert,
            paste_text=paste,
            fetch_latest=request.fetch_latest,
            llm=get_insights_llm(),
        )
    except NewsProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
