"""Orchestrate news fetch → classify → aggregate → optional LLM summary."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from app.insights.news_config import active_news_provider_name, resolve_news_provider
from app.insights.news_port import NewsItem, NewsProvider, NewsProviderError
from app.insights.sentiment import aggregate, classify_item
from app.insights.sentiment_finbert import (
    FinBertNotEnabled,
    FinBertUnavailable,
    classify_item_finbert,
)
from app.insights.summary import (
    SUMMARY_UNAVAILABLE_NOTICE,
    summarize_classified_news,
)
from app.research_copilot.llm_port import LlmPort

NOTICE = (
    "Live snapshot; not a backtest feature; AI interpretation, not advice."
)


def _parse_paste_text(paste_text: Optional[str]) -> list[NewsItem]:
    if not paste_text or not paste_text.strip():
        return []
    chunks = re.split(r"\n\s*\n|^\s*[-*•]\s+", paste_text.strip(), flags=re.MULTILINE)
    items: list[NewsItem] = []
    for i, chunk in enumerate(chunks):
        line = " ".join(chunk.strip().split())
        if len(line) < 8:
            continue
        items.append(
            NewsItem(
                id=f"paste-{i+1}",
                headline=line[:400],
                summary="",
                url="",
                source="paste",
                published_at=datetime.now(timezone.utc),
            )
        )
    if not items and paste_text.strip():
        items.append(
            NewsItem(
                id="paste-1",
                headline=paste_text.strip()[:400],
                summary="",
                url="",
                source="paste",
                published_at=datetime.now(timezone.utc),
            )
        )
    return items[:20]


def _classify_text(text: str, *, use_finbert: bool) -> dict[str, Any]:
    if use_finbert:
        try:
            return classify_item_finbert(text, use_finbert=True)
        except (FinBertNotEnabled, FinBertUnavailable):
            pass
    return classify_item(text)


def _reason_from_classification(result: dict[str, Any]) -> str:
    if result.get("classifier") == "finbert":
        label = result.get("finbert_label") or result.get("stance")
        return f"FinBERT label={label}; score_1_5={result.get('score_1_5')}."
    pos = result.get("positive_hits") or 0
    neg = result.get("negative_hits") or 0
    return (
        f"Lexicon polarity={float(result.get('polarity') or 0):+.2f} "
        f"(positive_hits={pos}, negative_hits={neg})."
    )


def _merge_news(
    pasted: Sequence[NewsItem],
    fetched: Sequence[NewsItem],
    *,
    limit: int,
) -> list[NewsItem]:
    combined: list[NewsItem] = []
    seen: set[str] = set()
    for item in list(pasted) + list(fetched):
        key = item.headline.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        combined.append(item)
        if len(combined) >= limit:
            break
    return combined


def run_news_sentiment_insight(
    *,
    ticker: str,
    limit: int = 10,
    use_finbert: bool = False,
    paste_text: Optional[str] = None,
    fetch_latest: bool = True,
    llm: Optional[LlmPort] = None,
    news_provider: Optional[NewsProvider] = None,
) -> dict[str, Any]:
    """
    AIN-3 pipeline: provider → lexicon(/FinBERT) classify → aggregate → optional summary.

    Classification always runs. Summary is optional and never fails the request.
    """
    ticker_clean = ticker.upper().strip()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    pasted = _parse_paste_text(paste_text)
    fetched: list[NewsItem] = []
    provider_name = "none"
    provider_warning: Optional[str] = None

    if fetch_latest:
        provider = news_provider if news_provider is not None else resolve_news_provider()
        provider_name = active_news_provider_name()
        if hasattr(provider, "provider_name"):
            provider_name = str(getattr(provider, "provider_name") or provider_name)
        try:
            fetched = provider.fetch_recent(ticker_clean, limit=limit)
        except NewsProviderError as exc:
            provider_warning = exc.message
            fetched = []
        except Exception as exc:  # noqa: BLE001
            provider_warning = f"News provider failed: {exc}"
            fetched = []

    news_items = _merge_news(pasted, fetched, limit=limit)

    classified_rows: list[dict[str, Any]] = []
    classifier_name = "loughran_mcdonald_lite"
    for item in news_items:
        text = f"{item.headline}\n{item.summary}".strip()
        result = _classify_text(text, use_finbert=use_finbert)
        classifier_name = str(result.get("classifier") or classifier_name)
        classified_rows.append(
            {
                "id": item.id,
                "headline": item.headline,
                "summary": item.summary,
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at.isoformat()
                if item.published_at
                else None,
                "stance": result["stance"],
                "score_1_5": int(result["score_1_5"]),
                "polarity": float(result["polarity"]),
                "reason": _reason_from_classification(result),
            }
        )

    overall_agg = aggregate(classified_rows)
    overall = {
        "stance": overall_agg["overall_stance"],
        "score_1_5": overall_agg["overall_score_1_5"],
        "counts": {
            "positive": overall_agg["positive"],
            "neutral": overall_agg["neutral"],
            "negative": overall_agg["negative"],
        },
        "polarity": overall_agg["overall_polarity"],
    }

    summary = summarize_classified_news(
        ticker=ticker_clean,
        overall=overall,
        items=classified_rows,
        llm=llm,
    )

    # Merge LLM shadow labels onto items when present (classifier remains primary).
    if summary and isinstance(summary.get("bullets"), list):
        by_id = {
            str(b.get("citation_id") or ""): b
            for b in summary["bullets"]
            if b.get("citation_id")
        }
        by_headline = {
            str(b.get("headline") or "").strip().lower(): b
            for b in summary["bullets"]
            if str(b.get("headline") or "").strip()
        }
        for row in classified_rows:
            bullet = by_id.get(str(row.get("id") or "")) or by_headline.get(
                str(row.get("headline") or "").strip().lower()
            )
            if not bullet:
                continue
            if bullet.get("llm_stance") is not None:
                row["llm_stance"] = bullet["llm_stance"]
            if bullet.get("llm_score_1_5") is not None:
                row["llm_score_1_5"] = bullet["llm_score_1_5"]

    notices = [NOTICE]
    if llm is None:
        notices.append(SUMMARY_UNAVAILABLE_NOTICE)
    if provider_warning:
        notices.append(provider_warning)
    if not classified_rows:
        notices.append("No headlines available for this request.")
    if summary and summary.get("agreement"):
        notices.append(
            "LLM–classifier agreement is reported for evaluation; "
            "classifier scores remain authoritative."
        )

    agreement = summary.get("agreement") if isinstance(summary, dict) else None

    return {
        "ticker": ticker_clean,
        "generated_at": generated_at,
        "overall": overall,
        "items": [
            {
                "headline": row["headline"],
                "url": row["url"],
                "source": row["source"],
                "published_at": row["published_at"],
                "stance": row["stance"],
                "score_1_5": row["score_1_5"],
                "reason": row["reason"],
                **(
                    {"llm_stance": row["llm_stance"]}
                    if row.get("llm_stance") is not None
                    else {}
                ),
                **(
                    {"llm_score_1_5": row["llm_score_1_5"]}
                    if row.get("llm_score_1_5") is not None
                    else {}
                ),
            }
            for row in classified_rows
        ],
        "summary": summary,
        "agreement": agreement,
        "provider": provider_name,
        "classifier": classifier_name,
        "notice": " ".join(notices),
        "backtest_feature": False,
        "scope": "current_qualitative_panel",
    }
