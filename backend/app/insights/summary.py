"""LLM summary + shadow sentiment labels for agreement evaluation.

Classifier scores (lexicon / FinBERT) remain authoritative. The LLM may emit
its own stance/score_1_5 on the same headlines so the product can report
agreement — evaluating the model, not trusting it blindly.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Mapping, Optional, Sequence

from app.insights.sentiment import score_to_stance
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.research_copilot.system_policy import COPILOT_SYSTEM_POLICY

logger = logging.getLogger(__name__)

INSIGHTS_SUMMARY_DISCLAIMER = (
    "AI interpretation of provided headlines only — not investment advice. "
    "Authoritative scores come from the deterministic classifier; LLM labels "
    "are a shadow evaluation for agreement only."
)

SUMMARY_UNAVAILABLE_NOTICE = "summary 不可用(未配置)"

AGREEMENT_NOTE = (
    "Classifier remains authoritative. LLM labels are a shadow score used only "
    "to measure agreement — do not treat LLM as ground truth."
)

NEWS_SUMMARY_POLICY = (
    COPILOT_SYSTEM_POLICY
    + """

Additional rules for AI Insights news summary:
11. Classifier scores are NOT provided in the context. Assign your OWN independent
    score_1_5 (1..5) and stance (favourable|neutral|not_favourable) for each item
    from the headline/summary text alone. These are evaluation labels only.
12. Also produce a short natural-language summary grounded only in the supplied items.
13. For each item: reason + cite url/source from context. Include citation_id.
14. NEVER predict prices, returns, or recommend trades.
15. NEVER claim your score overrides a research classifier.

Return ONLY valid JSON:
{
  "text": "<short grounded summary paragraph>",
  "bullets": [
    {
      "citation_id": "<id from context>",
      "headline": "...",
      "reason": "...",
      "citation_url": "...",
      "citation_source": "...",
      "llm_stance": "favourable"|"neutral"|"not_favourable",
      "llm_score_1_5": <int 1-5>
    }
  ]
}
"""
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class FakeInsightsSummaryLlm(LlmPort):
    """Deterministic offline summary + shadow labels for CI."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        bullets = []
        for item in context[:8]:
            lines = [ln.strip() for ln in item.content.splitlines() if ln.strip()]
            headline = lines[0] if lines else item.label
            source = ""
            url = ""
            for ln in lines:
                if ln.startswith("source="):
                    source = ln.split("=", 1)[1]
                if ln.startswith("url="):
                    url = ln.split("=", 1)[1]
            lower = headline.lower()
            if any(w in lower for w in ("surge", "beat", "upgrade", "growth", "record")):
                llm_stance, llm_score = "favourable", 5
            elif any(
                w in lower for w in ("probe", "lawsuit", "downgrade", "miss", "cut")
            ):
                llm_stance, llm_score = "not_favourable", 1
            else:
                llm_stance, llm_score = "neutral", 3
            bullets.append(
                {
                    "citation_id": item.citation_id,
                    "headline": headline[:200],
                    "reason": "Shadow LLM label from headline cues only.",
                    "citation_url": url,
                    "citation_source": source or "fixture",
                    "llm_stance": llm_stance,
                    "llm_score_1_5": llm_score,
                }
            )
        payload = {
            "text": (
                "Based only on the supplied headlines, tone varies across items. "
                "Classifier scores remain authoritative; LLM labels are for agreement."
            ),
            "bullets": bullets,
        }
        return LlmResult(text=json.dumps(payload), model="fake-insights-summary", latency_ms=1)


def _context_for_llm_shadow(items: Sequence[Mapping[str, Any]]) -> list[ContextItem]:
    """Context without classifier scores — so LLM labels stay independent."""
    context: list[ContextItem] = []
    for i, item in enumerate(items):
        headline = str(item.get("headline") or "").strip()
        if not headline:
            continue
        cid = str(item.get("id") or f"item-{i+1}")
        published = item.get("published_at")
        published_s = (
            published.isoformat()
            if hasattr(published, "isoformat")
            else str(published or "")
        )
        content = "\n".join(
            [
                headline,
                f"source={item.get('source') or ''}",
                f"url={item.get('url') or ''}",
                f"published_at={published_s}",
                f"summary={str(item.get('summary') or '')[:400]}",
            ]
        )
        context.append(
            ContextItem(
                citation_id=cid,
                source_type="news_headline",
                source_id=cid,
                label=f"News {i+1}",
                content=content,
            )
        )
    return context


def _normalize_llm_score(value: Any) -> Optional[int]:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    if score < 1 or score > 5:
        return None
    return score


def _normalize_llm_stance(value: Any, score: Optional[int]) -> Optional[str]:
    raw = str(value or "").strip().lower()
    if raw in {"favourable", "favorable", "positive"}:
        return "favourable"
    if raw in {"not_favourable", "unfavourable", "unfavorable", "negative"}:
        return "not_favourable"
    if raw in {"neutral"}:
        return "neutral"
    if score is not None:
        return score_to_stance(score)
    return None


def _norm_headline(text: str) -> str:
    return " ".join(_TOKEN_RE.findall((text or "").lower()))


def match_llm_labels(
    classified: Sequence[Mapping[str, Any]],
    bullets: Sequence[Mapping[str, Any]],
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Pair classifier rows with LLM bullets by citation_id, then headline."""
    by_id = {
        str(b.get("citation_id") or "").strip(): b
        for b in bullets
        if str(b.get("citation_id") or "").strip()
    }
    by_headline = {
        _norm_headline(str(b.get("headline") or "")): b
        for b in bullets
        if _norm_headline(str(b.get("headline") or ""))
    }
    pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    used: set[int] = set()
    for row in classified:
        cid = str(row.get("id") or "").strip()
        bullet = by_id.get(cid)
        if bullet is None:
            bullet = by_headline.get(_norm_headline(str(row.get("headline") or "")))
        if bullet is None:
            continue
        bid = id(bullet)
        if bid in used:
            continue
        used.add(bid)
        pairs.append((row, bullet))
    return pairs


def compute_agreement(
    classified: Sequence[Mapping[str, Any]],
    bullets: Sequence[Mapping[str, Any]],
) -> Optional[dict[str, Any]]:
    """
    Agreement between classifier labels and LLM shadow labels.

    ``stance_agreement`` / ``score_agreement`` ∈ [0, 1].
    """
    pairs = match_llm_labels(classified, bullets)
    comparable: list[tuple[Mapping[str, Any], int, str]] = []
    for row, bullet in pairs:
        llm_score = _normalize_llm_score(bullet.get("llm_score_1_5"))
        llm_stance = _normalize_llm_stance(bullet.get("llm_stance"), llm_score)
        if llm_score is None or llm_stance is None:
            continue
        comparable.append((row, llm_score, llm_stance))

    n = len(comparable)
    if n == 0:
        return None

    n_stance = sum(
        1 for row, _, llm_stance in comparable if str(row.get("stance")) == llm_stance
    )
    n_score = sum(
        1
        for row, llm_score, _ in comparable
        if int(row.get("score_1_5") or 0) == llm_score
    )
    return {
        "n_compared": n,
        "n_agree_stance": n_stance,
        "n_agree_score": n_score,
        "stance_agreement": round(n_stance / n, 4),
        "score_agreement": round(n_score / n, 4),
        "note": AGREEMENT_NOTE,
    }


def summarize_classified_news(
    *,
    ticker: str,
    overall: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    llm: Optional[LlmPort],
) -> Optional[dict[str, Any]]:
    """
    Optional LLM narrative + shadow labels.

    Returns ``None`` when LLM is not configured or generation fails.
    """
    if llm is None:
        return None
    if not items:
        return {
            "text": "No headlines were available to summarize.",
            "disclaimer": INSIGHTS_SUMMARY_DISCLAIMER,
            "bullets": [],
            "agreement": None,
        }

    context = _context_for_llm_shadow(items)
    user_prompt = (
        f"Ticker: {ticker}\n"
        "Assign independent llm_score_1_5 / llm_stance for each headline, "
        "then summarize. Do not predict price or recommend trades. "
        f"(Product overall from classifier — for context only, do not copy: "
        f"stance={overall.get('stance')} score={overall.get('score_1_5')})"
    )
    try:
        result = llm.generate(
            system_prompt=NEWS_SUMMARY_POLICY,
            user_prompt=user_prompt,
            context=context,
        )
    except Exception as exc:  # noqa: BLE001 — soft-fail summary
        logger.warning("Insights summary LLM failed: %s", exc)
        return None

    try:
        parsed = json.loads(result.text)
    except json.JSONDecodeError:
        text = (result.text or "").strip()
        if not text:
            return None
        return {
            "text": text[:2000],
            "disclaimer": INSIGHTS_SUMMARY_DISCLAIMER,
            "bullets": [],
            "agreement": None,
            "model": result.model,
        }

    if not isinstance(parsed, dict):
        return None
    text = str(parsed.get("text") or "").strip()
    if not text:
        return None

    bullets_out: list[dict[str, Any]] = []
    for bullet in parsed.get("bullets") or []:
        if not isinstance(bullet, dict):
            continue
        headline = str(bullet.get("headline") or "").strip()
        if not headline:
            continue
        llm_score = _normalize_llm_score(bullet.get("llm_score_1_5"))
        llm_stance = _normalize_llm_stance(bullet.get("llm_stance"), llm_score)
        row: dict[str, Any] = {
            "citation_id": str(bullet.get("citation_id") or "").strip(),
            "headline": headline[:280],
            "reason": str(bullet.get("reason") or "").strip()[:400],
            "citation_url": str(bullet.get("citation_url") or "").strip(),
            "citation_source": str(bullet.get("citation_source") or "").strip(),
        }
        if llm_score is not None:
            row["llm_score_1_5"] = llm_score
        if llm_stance is not None:
            row["llm_stance"] = llm_stance
        bullets_out.append(row)

    agreement = compute_agreement(items, bullets_out)

    return {
        "text": text[:2000],
        "disclaimer": INSIGHTS_SUMMARY_DISCLAIMER,
        "bullets": bullets_out,
        "agreement": agreement,
        "model": result.model,
    }
