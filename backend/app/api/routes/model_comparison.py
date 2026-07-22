"""POST /api/v1/models/compare — chronological ML vs rule comparison."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data_providers.yahoo_provider import load_price_data
from app.models.model_comparison import (
    attach_offline_artifacts,
    resolve_offline_strategies,
    run_model_comparison,
    run_walk_forward_comparison,
)
from app.schemas import ModelComparisonRequest

router = APIRouter(prefix="/api/v1/models", tags=["compare-models"])


@router.post("/compare")
def compare_models(request: ModelComparisonRequest) -> dict[str, Any]:
    """
    Load prices, run chronological model vs rule comparison on a shared OOS window.

    When ``n_folds`` is set, runs multi-fold walk-forward OOS instead of a single split.
    Optionally attaches offline CNN/LSTM JSON artifacts when selected and compatible
    (no torch at runtime).
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
            data_source=request.data_source,
        )
        if request.n_folds is not None:
            payload = run_walk_forward_comparison(
                price_df,
                n_folds=request.n_folds,
                transaction_cost=request.transaction_cost,
                short_window=request.short_window,
                long_window=request.long_window,
                momentum_window=request.momentum_window,
                models=request.models,
                scheme=request.scheme,
                preprocessing=request.preprocessing,
                pca_components=request.pca_components,
                select_k=request.select_k,
                tune=request.tune,
            )
        else:
            payload = run_model_comparison(
                price_df,
                split_date=request.split_date,
                transaction_cost=request.transaction_cost,
                short_window=request.short_window,
                long_window=request.long_window,
                momentum_window=request.momentum_window,
                models=request.models,
                preprocessing=request.preprocessing,
                pca_components=request.pca_components,
                select_k=request.select_k,
                tune=request.tune,
            )
        payload = attach_offline_artifacts(
            payload,
            ticker=request.ticker,
            start_date=request.start_date,
            strategies=resolve_offline_strategies(
                request.models,
                include_lstm=request.include_lstm,
            ),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare models for '{request.ticker}': {exc}",
        ) from exc

    return {
        "ticker": request.ticker,
        "start_date": request.start_date,
        "end_date": normalized_end_date,
        "data_source": request.data_source,
        **payload,
    }


COMPARISON_EXPLAIN_POLICY = """You explain model-comparison research results only.

Rules:
1. Use only the provided summary and result metrics.
2. Distinguish facts (reported OOS metrics) from interpretation.
3. NEVER predict future returns or prices.
4. NEVER recommend buy/sell/hold or claim a strategy is profitable/guaranteed.
5. Remind that the best OOS model on this window may not stay best on other windows.
6. Directional accuracy is not a return promise.

Return ONLY JSON: {"explanation": "<short grounded paragraph>"}.
"""


class CompareExplainRequest(BaseModel):
    summary: dict[str, Any]
    results: list[dict[str, Any]]
    mode: Optional[str] = None


_explain_llm_override = None


def set_compare_explain_llm_override(llm) -> None:
    global _explain_llm_override
    _explain_llm_override = llm


@router.post("/compare/explain")
def explain_comparison(request: CompareExplainRequest) -> dict[str, Any]:
    """Optional Copilot-style explanation of comparison results (no predictions)."""
    from app.research_copilot.llm_config import LlmConfigurationError
    from app.research_copilot.llm_port import ContextItem, LlmResult
    from app.research_copilot.service import resolve_llm_adapter
    import json

    class _FakeExplain:
        def generate(self, *, system_prompt, user_prompt, context):
            text = (
                '{"explanation": "On this out-of-sample window the reported summary '
                "highlights relative Sharpe, return, and drawdown among the listed "
                'strategies. These are historical research metrics only — not a forecast '
                'or investment recommendation."}'
            )
            return LlmResult(text=text, model="fake-compare-explain", latency_ms=1)

    llm = _explain_llm_override
    if llm is None:
        try:
            llm = resolve_llm_adapter()
        except LlmConfigurationError:
            llm = _FakeExplain()

    compact = []
    for row in request.results[:20]:
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        compact.append(
            {
                "label": row.get("label"),
                "kind": row.get("kind"),
                "strategy": row.get("strategy"),
                "sharpe": metrics.get("sharpe_ratio"),
                "total_return": metrics.get("total_return"),
                "max_drawdown": metrics.get("strategy_max_drawdown")
                or metrics.get("max_drawdown"),
                "trades": metrics.get("number_of_trades"),
                "cost": metrics.get("transaction_cost_total"),
            }
        )
    context = [
        ContextItem(
            citation_id="summary",
            source_type="model_comparison",
            source_id="summary",
            label="Summary",
            content=json.dumps(request.summary, default=str),
        ),
        ContextItem(
            citation_id="results",
            source_type="model_comparison",
            source_id="results",
            label="Results",
            content=json.dumps(compact, default=str),
        ),
    ]
    result = llm.generate(
        system_prompt=COMPARISON_EXPLAIN_POLICY,
        user_prompt="Explain which models look relatively stronger on this OOS window and why turnover/cost matter. No predictions.",
        context=context,
    )
    try:
        parsed = json.loads(result.text)
        explanation = str(parsed.get("explanation") or "").strip()
    except json.JSONDecodeError:
        explanation = result.text.strip()
    if not explanation:
        raise HTTPException(status_code=502, detail="Empty explanation from model.")
    return {
        "explanation": explanation,
        "model": result.model,
        "disclaimer": "AI interpretation of reported OOS metrics only — not investment advice.",
    }
