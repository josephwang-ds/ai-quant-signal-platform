"""POST /api/v1/models/compare — chronological ML vs rule comparison."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.data_providers.yahoo_provider import load_price_data
from app.models.model_comparison import (
    attach_lstm_offline_artifact,
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
    Optionally attaches an offline LSTM artifact when compatible (no torch at runtime).
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
            )
        payload = attach_lstm_offline_artifact(
            payload,
            ticker=request.ticker,
            start_date=request.start_date,
            include_lstm=request.include_lstm,
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
