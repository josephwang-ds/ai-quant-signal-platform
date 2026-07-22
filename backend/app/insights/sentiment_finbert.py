"""Optional FinBERT sentiment — gated, offline / explicit opt-in only.

Never imported on the default Render path. Requires ``torch`` + ``transformers``
from ``requirements-dev.txt`` (or a local ML env). Enable with
``use_finbert=True`` / ``INSIGHTS_ALLOW_FINBERT=1``.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from app.insights.sentiment import polarity_to_score_1_5, score_to_stance

_FINBERT_MODEL_ID = "ProsusAI/finbert"
_pipeline = None


class FinBertNotEnabled(Exception):
    def __init__(
        self,
        message: str = (
            "FinBERT is disabled. Pass use_finbert=True and set "
            "INSIGHTS_ALLOW_FINBERT=1; install torch+transformers via requirements-dev."
        ),
    ) -> None:
        super().__init__(message)
        self.message = message


class FinBertUnavailable(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def finbert_allowed(*, environ: Optional[dict[str, str]] = None) -> bool:
    env = environ if environ is not None else dict(os.environ)
    flag = (env.get("INSIGHTS_ALLOW_FINBERT") or "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _label_to_polarity(label: str, score: float) -> float:
    cleaned = label.strip().lower()
    magnitude = max(0.0, min(1.0, float(score)))
    if cleaned in {"positive", "pos", "favourable", "favorable"}:
        return magnitude
    if cleaned in {"negative", "neg", "not_favourable", "unfavourable", "unfavorable"}:
        return -magnitude
    return 0.0


def _get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        import torch  # noqa: F401
        from transformers import pipeline
    except ImportError as exc:  # pragma: no cover - optional heavy deps
        raise FinBertUnavailable(
            "FinBERT requires torch and transformers "
            "(pip install -r requirements-dev.txt && pip install transformers)."
        ) from exc
    try:
        _pipeline = pipeline(
            "sentiment-analysis",
            model=_FINBERT_MODEL_ID,
            tokenizer=_FINBERT_MODEL_ID,
        )
    except Exception as exc:  # pragma: no cover - model download / runtime
        raise FinBertUnavailable(f"Failed to load FinBERT: {exc}") from exc
    return _pipeline


def classify_item_finbert(
    text: str,
    *,
    use_finbert: bool = False,
    environ: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """
    Gated FinBERT classifier. Default path must not call this without opt-in.

    Returns the same shape as ``sentiment.classify_item`` plus ``classifier=finbert``.
    """
    if not use_finbert or not finbert_allowed(environ=environ):
        raise FinBertNotEnabled()

    pipe = _get_pipeline()
    raw = pipe(text[:512] if text else "")
    if isinstance(raw, list) and raw:
        row = raw[0]
    else:
        row = raw if isinstance(raw, dict) else {}
    label = str(row.get("label") or "neutral")
    conf = float(row.get("score") or 0.0)
    polarity = _label_to_polarity(label, conf)
    score = polarity_to_score_1_5(polarity)
    return {
        "stance": score_to_stance(score),
        "score_1_5": score,
        "polarity": float(polarity),
        "positive_hits": None,
        "negative_hits": None,
        "classifier": "finbert",
        "finbert_label": label,
        "finbert_confidence": conf,
    }
