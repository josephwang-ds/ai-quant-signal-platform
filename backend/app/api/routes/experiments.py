"""Experiments Persistence v1 API。"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.db.repositories.backtest_runs import (
    DatabaseUnavailableError,
    create_backtest_run,
    delete_backtest_run,
    get_backtest_run,
    list_backtest_runs,
)
from app.schemas import SaveBacktestRunRequest

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def _database_unavailable_response(exc: DatabaseUnavailableError) -> HTTPException:
    message = str(exc) or "Database connection failed."
    return HTTPException(status_code=503, detail=message)


@router.post("/backtest-runs")
def save_backtest_run(request: SaveBacktestRunRequest) -> dict:
    """保存回测实验元数据与交易日志（不存完整权益曲线）。"""
    trades = [
        {
            "trade_date": item.date,
            "action": item.action,
            "price": item.price,
            "signal": item.signal,
            "position_after": item.position_after,
            "reason": item.reason,
        }
        for item in request.trade_log
    ]

    try:
        run_id = create_backtest_run(
            ticker=request.ticker,
            market=request.market,
            data_source=request.data_source,
            strategy=request.strategy,
            strategy_config=request.strategy_config,
            start_date=request.start_date,
            end_date=request.end_date,
            transaction_cost=request.transaction_cost,
            metrics=request.metrics,
            notes=request.notes,
            trades=trades,
        )
    except DatabaseUnavailableError as exc:
        raise _database_unavailable_response(exc) from exc

    return {
        "id": run_id,
        "message": "Backtest run saved.",
    }


@router.get("/backtest-runs")
def get_backtest_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """列出已保存的回测实验（按创建时间倒序）。"""
    try:
        items = list_backtest_runs(limit=limit, offset=offset)
    except DatabaseUnavailableError as exc:
        raise _database_unavailable_response(exc) from exc

    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.get("/backtest-runs/{run_id}")
def get_backtest_run_detail(run_id: str) -> dict:
    """获取单条回测实验详情与交易日志。"""
    try:
        UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid backtest run id.") from exc

    try:
        run = get_backtest_run(run_id)
    except DatabaseUnavailableError as exc:
        raise _database_unavailable_response(exc) from exc

    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found.")

    return run


@router.delete("/backtest-runs/{run_id}")
def remove_backtest_run(run_id: str) -> dict:
    """删除已保存的回测实验。"""
    try:
        UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid backtest run id.") from exc

    try:
        deleted = delete_backtest_run(run_id)
    except DatabaseUnavailableError as exc:
        raise _database_unavailable_response(exc) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest run not found.")

    return {"id": run_id, "message": "Backtest run deleted."}
