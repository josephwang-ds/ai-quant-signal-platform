"""Deterministic lexicon sentiment classifier tests (AIN-2)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.insights.sentiment import (
    aggregate,
    classify_item,
    polarity_to_score_1_5,
    score_to_stance,
    time_decay_weight,
)
from app.insights.sentiment_finbert import (
    FinBertNotEnabled,
    classify_item_finbert,
    finbert_allowed,
)


def test_classify_item_positive_deterministic() -> None:
    a = classify_item("Company shares surge after earnings beat and growth upgrade")
    b = classify_item("Company shares surge after earnings beat and growth upgrade")
    assert a == b
    assert a["classifier"] == "loughran_mcdonald_lite"
    assert a["polarity"] > 0
    assert a["score_1_5"] >= 4
    assert a["stance"] == "favourable"
    assert a["positive_hits"] >= 2


def test_classify_item_negative_deterministic() -> None:
    out = classify_item("Regulators open probe after lawsuit and downgrade warning")
    assert out["polarity"] < 0
    assert out["score_1_5"] <= 2
    assert out["stance"] == "not_favourable"
    assert out["negative_hits"] >= 2


def test_classify_item_neutral_when_no_lexicon_hits() -> None:
    out = classify_item("The firm scheduled a routine investor calendar update")
    assert out["polarity"] == 0.0
    assert out["score_1_5"] == 3
    assert out["stance"] == "neutral"
    assert out["positive_hits"] == 0
    assert out["negative_hits"] == 0


def test_score_1_5_boundaries() -> None:
    assert polarity_to_score_1_5(-1.0) == 1
    assert polarity_to_score_1_5(-0.60) == 1
    assert polarity_to_score_1_5(-0.59) == 2
    assert polarity_to_score_1_5(-0.20) == 2
    assert polarity_to_score_1_5(-0.19) == 3
    assert polarity_to_score_1_5(0.0) == 3
    assert polarity_to_score_1_5(0.19) == 3
    assert polarity_to_score_1_5(0.20) == 4
    assert polarity_to_score_1_5(0.59) == 4
    assert polarity_to_score_1_5(0.60) == 5
    assert polarity_to_score_1_5(1.0) == 5
    assert score_to_stance(1) == "not_favourable"
    assert score_to_stance(3) == "neutral"
    assert score_to_stance(5) == "favourable"


def test_aggregate_counts_and_time_decay_weighting() -> None:
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    items = [
        {
            "stance": "favourable",
            "score_1_5": 5,
            "polarity": 1.0,
            "published_at": now - timedelta(hours=1),
        },
        {
            "stance": "not_favourable",
            "score_1_5": 1,
            "polarity": -1.0,
            "published_at": now - timedelta(hours=100),
        },
        {
            "stance": "neutral",
            "score_1_5": 3,
            "polarity": 0.0,
            "published_at": now - timedelta(hours=10),
        },
    ]
    out = aggregate(items, now=now, half_life_hours=48.0)
    assert out["positive"] == 1
    assert out["neutral"] == 1
    assert out["negative"] == 1
    assert out["n_items"] == 3
    # Recent +1.0 should dominate aged -1.0 → favourable overall.
    assert out["overall_polarity"] > 0
    assert out["overall_score_1_5"] >= 4
    assert out["overall_stance"] == "favourable"
    assert out["weight_sum"] > 0


def test_time_decay_half_life() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    published = now - timedelta(hours=48)
    w = time_decay_weight(published, now=now, half_life_hours=48.0)
    assert w == pytest.approx(0.5)


def test_aggregate_empty_is_neutral() -> None:
    out = aggregate([])
    assert out["overall_stance"] == "neutral"
    assert out["overall_score_1_5"] == 3
    assert out["positive"] == out["neutral"] == out["negative"] == 0


def test_finbert_gated_off_by_default(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTS_ALLOW_FINBERT", raising=False)
    assert finbert_allowed() is False
    with pytest.raises(FinBertNotEnabled):
        classify_item_finbert("earnings beat", use_finbert=True)
    with pytest.raises(FinBertNotEnabled):
        classify_item_finbert("earnings beat", use_finbert=False)
