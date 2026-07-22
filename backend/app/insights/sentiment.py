"""Deterministic financial-news sentiment classifier (no LLM).

Default path: compact Loughran–McDonald–style positive/negative lexicon.
Polarity ∈ [-1, 1] → score_1_5 ∈ {1..5} → stance.

This is the authoritative classification step for AI Insights. LLM may only
explain already-classified items — never invent the score.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

Stance = str  # favourable | neutral | not_favourable

# Compact LM-inspired finance lexicon (subset; no pysentiment2 / heavy deps).
# Tokens are lowercase lemmas / surface forms matched after simple tokenization.
_POSITIVE: frozenset[str] = frozenset(
    {
        "able",
        "achieve",
        "achieved",
        "advantage",
        "attain",
        "attractive",
        "beat",
        "beats",
        "boost",
        "boosted",
        "breakthrough",
        "collaborate",
        "collaboration",
        "confidence",
        "dividend",
        "earn",
        "earnings",
        "efficient",
        "exceed",
        "exceeded",
        "expand",
        "expansion",
        "favorable",
        "favourable",
        "gain",
        "gains",
        "grow",
        "growth",
        "improve",
        "improved",
        "improvement",
        "innovation",
        "opportunity",
        "optimistic",
        "outperform",
        "outperformed",
        "positive",
        "profit",
        "profitable",
        "progress",
        "raise",
        "raised",
        "rally",
        "record",
        "recover",
        "recovery",
        "rise",
        "rose",
        "solid",
        "strength",
        "strong",
        "success",
        "successful",
        "surge",
        "surpass",
        "surpassed",
        "upgrade",
        "upgraded",
        "upside",
        "win",
        "winner",
    }
)

_NEGATIVE: frozenset[str] = frozenset(
    {
        "allegation",
        "bankrupt",
        "bankruptcy",
        "breach",
        "collapse",
        "cut",
        "cuts",
        "decline",
        "declined",
        "default",
        "delay",
        "delayed",
        "disappoint",
        "disappointed",
        "downgrade",
        "downgraded",
        "fail",
        "failed",
        "failure",
        "fraud",
        "impair",
        "impairment",
        "investigation",
        "lawsuit",
        "litigation",
        "loss",
        "losses",
        "miss",
        "missed",
        "negative",
        "penalty",
        "plunge",
        "probe",
        "recall",
        "recession",
        "resign",
        "resignation",
        "risk",
        "risky",
        "sanction",
        "scandal",
        "shortfall",
        "slash",
        "slashed",
        "slowdown",
        "sue",
        "sued",
        "threat",
        "turbulence",
        "uncertain",
        "uncertainty",
        "unfavorable",
        "unfavourable",
        "volatility",
        "warn",
        "warning",
        "weak",
        "weakness",
        "writedown",
        "writeoff",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9']+")

# Polarity → score_1_5 boundaries (inclusive on the upper side of each band except 5).
# Tested explicitly in test_sentiment.py.
_SCORE_BOUNDS: tuple[tuple[float, int], ...] = (
    (-1.0, 1),
    (-0.60, 1),
    (-0.20, 2),
    (0.20, 3),
    (0.60, 4),
    (1.0, 5),
)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def polarity_to_score_1_5(polarity: float) -> int:
    """Map polarity ∈ [-1, 1] to an integer score in 1..5."""
    p = max(-1.0, min(1.0, float(polarity)))
    if p <= -0.60:
        return 1
    if p <= -0.20:
        return 2
    if p < 0.20:
        return 3
    if p < 0.60:
        return 4
    return 5


def score_to_stance(score_1_5: int) -> Stance:
    if score_1_5 <= 2:
        return "not_favourable"
    if score_1_5 >= 4:
        return "favourable"
    return "neutral"


def stance_from_polarity(polarity: float) -> Stance:
    return score_to_stance(polarity_to_score_1_5(polarity))


def classify_item(text: str) -> dict[str, Any]:
    """
    Lexicon classifier for one headline/snippet.

    Returns ``{stance, score_1_5, polarity, positive_hits, negative_hits, classifier}``.
    """
    tokens = tokenize(text)
    pos = sum(1 for tok in tokens if tok in _POSITIVE)
    neg = sum(1 for tok in tokens if tok in _NEGATIVE)
    total = pos + neg
    if total == 0:
        polarity = 0.0
    else:
        polarity = (pos - neg) / float(total)
        polarity = max(-1.0, min(1.0, polarity))

    score = polarity_to_score_1_5(polarity)
    return {
        "stance": score_to_stance(score),
        "score_1_5": score,
        "polarity": float(polarity),
        "positive_hits": int(pos),
        "negative_hits": int(neg),
        "classifier": "loughran_mcdonald_lite",
    }


def _parse_published_at(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)) and value > 0:
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            return None
    return None


def _item_polarity(item: Mapping[str, Any]) -> float:
    if "polarity" in item and item["polarity"] is not None:
        return float(item["polarity"])
    if "score_1_5" in item and item["score_1_5"] is not None:
        # Midpoints of score bands → approximate polarity for weighting.
        score = int(item["score_1_5"])
        return {1: -0.80, 2: -0.40, 3: 0.0, 4: 0.40, 5: 0.80}.get(score, 0.0)
    text = " ".join(
        str(item.get(key) or "") for key in ("headline", "summary", "text")
    ).strip()
    return float(classify_item(text)["polarity"])


def _item_stance(item: Mapping[str, Any], polarity: float) -> Stance:
    raw = item.get("stance")
    if isinstance(raw, str) and raw in {"favourable", "neutral", "not_favourable"}:
        return raw
    return stance_from_polarity(polarity)


def time_decay_weight(
    published_at: Optional[datetime],
    *,
    now: datetime,
    half_life_hours: float,
) -> float:
    """Exponential decay: weight = 0.5 ** (age_hours / half_life). Missing time → 1.0."""
    if published_at is None:
        return 1.0
    age_seconds = max(0.0, (now - published_at).total_seconds())
    age_hours = age_seconds / 3600.0
    hl = max(1e-6, float(half_life_hours))
    return float(0.5 ** (age_hours / hl))


def aggregate(
    items: Sequence[Mapping[str, Any]],
    *,
    now: Optional[datetime] = None,
    half_life_hours: float = 48.0,
) -> dict[str, Any]:
    """
    Aggregate classified items with recency-weighted polarity.

    Counts (positive / neutral / negative) are unweighted stance tallies.
    ``overall_score_1_5`` / ``overall_stance`` come from the weighted polarity.
    """
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)

    if not items:
        return {
            "overall_stance": "neutral",
            "overall_score_1_5": 3,
            "overall_polarity": 0.0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "n_items": 0,
            "weight_sum": 0.0,
            "classifier": "loughran_mcdonald_lite",
        }

    weight_sum = 0.0
    weighted_polarity = 0.0
    positive = neutral = negative = 0

    for item in items:
        polarity = _item_polarity(item)
        stance = _item_stance(item, polarity)
        if stance == "favourable":
            positive += 1
        elif stance == "not_favourable":
            negative += 1
        else:
            neutral += 1

        published = _parse_published_at(
            item.get("published_at") or item.get("publishedAt")
        )
        weight = time_decay_weight(
            published, now=clock, half_life_hours=half_life_hours
        )
        weight_sum += weight
        weighted_polarity += weight * polarity

    if weight_sum <= 0 or not math.isfinite(weight_sum):
        overall_polarity = 0.0
    else:
        overall_polarity = weighted_polarity / weight_sum
        overall_polarity = max(-1.0, min(1.0, overall_polarity))

    overall_score = polarity_to_score_1_5(overall_polarity)
    return {
        "overall_stance": score_to_stance(overall_score),
        "overall_score_1_5": overall_score,
        "overall_polarity": float(overall_polarity),
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "n_items": len(items),
        "weight_sum": float(weight_sum),
        "classifier": "loughran_mcdonald_lite",
    }


def classify_news_texts(
    texts: Sequence[str],
) -> list[dict[str, Any]]:
    """Convenience: classify a list of raw strings."""
    return [classify_item(text) for text in texts]
