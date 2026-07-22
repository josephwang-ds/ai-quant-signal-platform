"""Current-time news sentiment insights — qualitative only, never backtest features.

Honest boundary: without point-in-time timestamped historical news, sentiment must
NOT enter the historical ML feature frame (would be look-ahead). This module only
labels recently provided or fetched headlines for a qualitative panel.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.insights.news_port import NewsItem, NewsProvider
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult

NEWS_SENTIMENT_SYSTEM_POLICY = """You are an AI Insights layer for a research operating system.

You interpret provided news headlines/snippets only. You do NOT predict prices,
returns, or recommend trades.

Rules:
1. Base every stance only on the supplied headlines/snippets.
2. overall must be one of: favourable | neutral | not_favourable
3. score_1_5 is an integer 1..5 (1=very unfavourable, 3=neutral, 5=very favourable)
4. For each item: stance in favourable|neutral|not_favourable, short reason, citation
   (quote or paraphrase a short phrase from that headline).
5. NEVER predict future prices, returns, or market direction.
6. NEVER recommend buy/sell/hold or position sizing.
7. NEVER claim this is investment advice or a trading signal.
8. If texts are empty or uninformative, overall=neutral and score_1_5=3.

Return ONLY valid JSON:
{
  "overall": "favourable"|"neutral"|"not_favourable",
  "score_1_5": <int 1-5>,
  "items": [
    {"headline": "...", "stance": "favourable"|"neutral"|"not_favourable",
     "reason": "...", "citation": "..."}
  ],
  "disclaimer": "AI interpretation of provided text; not investment advice."
}
"""

ALLOWED_OVERALL = frozenset({"favourable", "neutral", "not_favourable"})
ALLOWED_STANCE = ALLOWED_OVERALL


class NewsSentimentError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FakeNewsSentimentLlm(LlmPort):
    """Deterministic offline LLM for CI — no network."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        headlines = []
        for item in context:
            line = item.content.strip().split("\n", 1)[0]
            if line:
                headlines.append(line[:120])
        if not headlines:
            payload = {
                "overall": "neutral",
                "score_1_5": 3,
                "items": [],
                "disclaimer": "AI interpretation of provided text; not investment advice.",
            }
        else:
            items = []
            for h in headlines[:6]:
                lower = h.lower()
                if any(w in lower for w in ("surge", "beat", "record", "upgrade", "growth")):
                    stance, score = "favourable", 4
                elif any(w in lower for w in ("cut", "miss", "probe", "lawsuit", "downgrade")):
                    stance, score = "not_favourable", 2
                else:
                    stance, score = "neutral", 3
                items.append(
                    {
                        "headline": h,
                        "stance": stance,
                        "reason": "Keyword cue from the supplied headline only.",
                        "citation": h[:80],
                    }
                )
            scores = [4 if i["stance"] == "favourable" else 2 if i["stance"] == "not_favourable" else 3 for i in items]
            avg = int(round(sum(scores) / len(scores))) if scores else 3
            overall = (
                "favourable"
                if avg >= 4
                else "not_favourable"
                if avg <= 2
                else "neutral"
            )
            payload = {
                "overall": overall,
                "score_1_5": avg,
                "items": items,
                "disclaimer": "AI interpretation of provided text; not investment advice.",
            }
        return LlmResult(
            text=json.dumps(payload),
            model="fake-news-sentiment",
            latency_ms=1,
        )


def _parse_pasted_news(pasted: Optional[str]) -> list[dict[str, str]]:
    if not pasted or not pasted.strip():
        return []
    chunks = re.split(r"\n\s*\n|^\s*[-*•]\s+", pasted.strip(), flags=re.MULTILINE)
    items: list[dict[str, str]] = []
    for chunk in chunks:
        line = " ".join(chunk.strip().split())
        if len(line) < 8:
            continue
        items.append({"headline": line[:200], "summary": ""})
    if not items and pasted.strip():
        items.append({"headline": pasted.strip()[:200], "summary": ""})
    return items[:12]


def _normalize_payload(raw: dict[str, Any]) -> dict[str, Any]:
    overall = str(raw.get("overall") or "neutral").strip().lower()
    if overall not in ALLOWED_OVERALL:
        overall = "neutral"
    try:
        score = int(raw.get("score_1_5", 3))
    except (TypeError, ValueError):
        score = 3
    score = max(1, min(5, score))

    items_out: list[dict[str, str]] = []
    for item in raw.get("items") or []:
        if not isinstance(item, dict):
            continue
        stance = str(item.get("stance") or "neutral").strip().lower()
        if stance not in ALLOWED_STANCE:
            stance = "neutral"
        headline = str(item.get("headline") or "").strip()
        if not headline:
            continue
        items_out.append(
            {
                "headline": headline[:280],
                "stance": stance,
                "reason": str(item.get("reason") or "").strip()[:400],
                "citation": str(item.get("citation") or "").strip()[:200],
            }
        )

    return {
        "overall": overall,
        "score_1_5": score,
        "items": items_out,
        "disclaimer": str(
            raw.get("disclaimer")
            or "AI interpretation of provided text; not investment advice."
        ),
        "scope": "current_qualitative_panel",
        "backtest_feature": False,
        "pit_note": (
            "No point-in-time historical news feed is configured. "
            "This panel is current-time qualitative only and is not used as a "
            "backtest feature (doing so without timestamps would be look-ahead)."
        ),
    }


def analyze_news_sentiment(
    *,
    ticker: str,
    pasted_news: Optional[str] = None,
    llm: LlmPort,
    news_provider: Optional[NewsProvider] = None,
    max_headlines: int = 8,
) -> dict[str, Any]:
    ticker_clean = ticker.upper().strip()
    if not ticker_clean:
        raise NewsSentimentError("ticker must not be empty")

    pasted_items = _parse_pasted_news(pasted_news)
    fetched_rows: list[dict[str, str]] = []
    provider_name: Optional[str] = None
    if news_provider is not None and len(pasted_items) < max_headlines:
        try:
            news_items = news_provider.fetch_recent(
                ticker_clean, limit=max_headlines
            )
        except Exception as exc:  # pragma: no cover - soft-fail fetch
            raise NewsSentimentError(
                f"News provider failed: {exc}", status_code=502
            ) from exc
        provider_name = type(news_provider).__name__
        if hasattr(news_provider, "provider_name"):
            provider_name = str(getattr(news_provider, "provider_name"))
        fetched_rows = [_news_item_to_row(item) for item in news_items]

    combined: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in pasted_items + fetched_rows:
        key = item["headline"].lower()
        if key in seen:
            continue
        seen.add(key)
        combined.append(item)
        if len(combined) >= max_headlines:
            break

    context = [
        ContextItem(
            citation_id=f"news-{i+1}",
            source_type="news_headline",
            source_id=ticker_clean,
            label=f"Headline {i+1}",
            content=f"{row['headline']}\n{row.get('summary') or ''}".strip(),
        )
        for i, row in enumerate(combined)
    ]

    user_prompt = (
        f"Ticker: {ticker_clean}\n"
        "Classify sentiment of the supplied headlines only. "
        "Do not predict price. Do not give investment advice."
    )
    result = llm.generate(
        system_prompt=NEWS_SENTIMENT_SYSTEM_POLICY,
        user_prompt=user_prompt,
        context=context,
    )
    try:
        parsed = json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise NewsSentimentError(
            "Sentiment model returned non-JSON output.", status_code=502
        ) from exc
    if not isinstance(parsed, dict):
        raise NewsSentimentError(
            "Sentiment model returned an unexpected payload.", status_code=502
        )

    payload = _normalize_payload(parsed)
    payload["ticker"] = ticker_clean
    payload["headline_count"] = len(combined)
    payload["model"] = result.model
    if provider_name:
        payload["news_provider"] = provider_name
    return payload


def _news_item_to_row(item: NewsItem) -> dict[str, str]:
    return {
        "headline": item.headline,
        "summary": (item.summary or "")[:280],
        "url": item.url or "",
        "source": item.source or "",
    }
