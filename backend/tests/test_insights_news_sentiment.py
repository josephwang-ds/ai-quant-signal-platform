"""AIN-3 news-sentiment route + pipeline (fixture provider + fake LLM)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import insights as insights_route
from app.insights.fixture_provider import FixtureNewsProvider
from app.insights.news_config import set_news_provider_override
from app.insights.pipeline import run_news_sentiment_insight
from app.insights.summary import FakeInsightsSummaryLlm
from app.main import app


from app.research_copilot.llm_port import LlmPort, LlmResult


class _BoomLlm(LlmPort):
    def generate(self, *, system_prompt, user_prompt, context):
        raise RuntimeError("provider down")


def _client() -> TestClient:
    return TestClient(app)


def teardown_function() -> None:
    insights_route.clear_insights_llm_override()
    set_news_provider_override(None)


def test_endpoint_returns_overall_and_item_stances() -> None:
    set_news_provider_override(FixtureNewsProvider())
    insights_route.set_insights_llm_override(FakeInsightsSummaryLlm())
    response = _client().post(
        "/api/v1/insights/news-sentiment",
        json={"ticker": "aapl", "limit": 4, "use_finbert": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert "generated_at" in payload
    assert payload["overall"]["score_1_5"] in range(1, 6)
    assert payload["overall"]["stance"] in {
        "favourable",
        "neutral",
        "not_favourable",
    }
    assert "counts" in payload["overall"]
    assert payload["items"]
    assert all("stance" in item and "score_1_5" in item for item in payload["items"])
    assert payload["summary"] is not None
    assert payload["summary"]["text"]
    assert payload["agreement"] is not None
    assert payload["agreement"]["n_compared"] >= 1
    assert 0.0 <= payload["agreement"]["stance_agreement"] <= 1.0
    assert 0.0 <= payload["agreement"]["score_agreement"] <= 1.0
    assert "authoritative" in (payload["agreement"].get("note") or "").lower()
    assert any(item.get("llm_stance") for item in payload["items"])
    assert "not a backtest feature" in payload["notice"].lower()
    assert "agreement" in payload["notice"].lower()
    assert payload["backtest_feature"] is False
    assert payload["classifier"]


def test_no_llm_summary_null_but_classification_remains() -> None:
    set_news_provider_override(FixtureNewsProvider())
    insights_route.set_insights_llm_override(None)
    response = _client().post(
        "/api/v1/insights/news-sentiment",
        json={"ticker": "MSFT", "limit": 3},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] is None
    assert payload.get("agreement") is None
    assert payload["items"]
    assert payload["overall"]["score_1_5"] in range(1, 6)
    assert "summary 不可用" in payload["notice"] or "未配置" in payload["notice"]


def test_compute_agreement_rates() -> None:
    from app.insights.summary import compute_agreement

    classified = [
        {"id": "1", "headline": "A surge beat", "stance": "favourable", "score_1_5": 5},
        {"id": "2", "headline": "A probe", "stance": "not_favourable", "score_1_5": 1},
        {"id": "3", "headline": "Mixed", "stance": "neutral", "score_1_5": 3},
    ]
    bullets = [
        {
            "citation_id": "1",
            "headline": "A surge beat",
            "llm_stance": "favourable",
            "llm_score_1_5": 5,
        },
        {
            "citation_id": "2",
            "headline": "A probe",
            "llm_stance": "favourable",
            "llm_score_1_5": 4,
        },
        {
            "citation_id": "3",
            "headline": "Mixed",
            "llm_stance": "neutral",
            "llm_score_1_5": 3,
        },
    ]
    out = compute_agreement(classified, bullets)
    assert out is not None
    assert out["n_compared"] == 3
    assert out["n_agree_stance"] == 2
    assert out["n_agree_score"] == 2
    assert out["stance_agreement"] == round(2 / 3, 4)
    assert out["score_agreement"] == round(2 / 3, 4)


def test_empty_news_graceful() -> None:
    class _Empty:
        def fetch_recent(self, ticker: str, limit: int = 10):
            return []

    set_news_provider_override(_Empty())
    insights_route.set_insights_llm_override(None)
    response = _client().post(
        "/api/v1/insights/news-sentiment",
        json={"ticker": "ZZZZ", "limit": 5, "paste_text": ""},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["overall"]["stance"] == "neutral"
    assert payload["overall"]["score_1_5"] == 3
    assert payload["summary"] is None


def test_llm_failure_does_not_500() -> None:
    set_news_provider_override(FixtureNewsProvider())
    insights_route.set_insights_llm_override(_BoomLlm())
    response = _client().post(
        "/api/v1/insights/news-sentiment",
        json={"ticker": "SPY", "limit": 3},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] is None
    assert payload["items"]
    assert payload["overall"]["score_1_5"] in range(1, 6)


def test_paste_text_classified_without_fetch() -> None:
    out = run_news_sentiment_insight(
        ticker="IBM",
        paste_text="IBM shares surge after earnings beat estimates",
        fetch_latest=False,
        llm=FakeInsightsSummaryLlm(),
    )
    assert out["items"]
    assert out["items"][0]["stance"] == "favourable"
    assert out["summary"] is not None


def test_render_yaml_has_finnhub_key() -> None:
    from pathlib import Path

    text = Path(__file__).resolve().parents[2].joinpath("render.yaml").read_text(
        encoding="utf-8"
    )
    assert "FINNHUB_API_KEY" in text
    assert "NEXT_PUBLIC_FINNHUB" not in text
