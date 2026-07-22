"""Legacy news_sentiment helpers — keep paste-only LLM path covered lightly."""

from __future__ import annotations

from app.insights.news_sentiment import FakeNewsSentimentLlm, analyze_news_sentiment


def test_legacy_analyze_with_paste_still_works() -> None:
    out = analyze_news_sentiment(
        ticker="SPY",
        pasted_news="Markets surge to record high\nGrowth beats estimates",
        llm=FakeNewsSentimentLlm(),
        news_provider=None,
    )
    assert out["ticker"] == "SPY"
    assert out["backtest_feature"] is False
    assert out["score_1_5"] in range(1, 6)
