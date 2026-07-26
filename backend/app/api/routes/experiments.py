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
from app.research_reproducibility.manifest import (
    MISSING,
    UNAVAILABLE,
    attach_manifest_to_metrics,
    build_reproducibility_manifest,
    extract_manifest_from_metrics,
    metrics_without_manifest,
)
from app.schemas import SaveBacktestRunRequest

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def _database_unavailable_response(exc: DatabaseUnavailableError) -> HTTPException:
    message = str(exc) or "Database connection failed."
    return HTTPException(status_code=503, detail=message)


def _manifest_for_saved_run(run: dict) -> dict:
    """Return stored manifest or a partial reconstruction for legacy rows."""
    stored = extract_manifest_from_metrics(run.get("metrics"))
    if stored:
        return stored
    strategy_config = run.get("strategy_config") or {}
    return build_reproducibility_manifest(
        data_source=run.get("data_source"),
        symbol=run.get("ticker"),
        universe=None,
        requested_start_date=run.get("start_date"),
        requested_end_date=run.get("end_date"),
        actual_start_date=MISSING,
        actual_end_date=MISSING,
        retrieval_timestamp=MISSING,
        row_count=MISSING,
        adjustment_mode=MISSING,
        protocol={
            "strategy": run.get("strategy"),
            "ticker": run.get("ticker"),
            **(
                strategy_config
                if isinstance(strategy_config, dict)
                else {}
            ),
            "transaction_cost": run.get("transaction_cost"),
        },
        data_hash=UNAVAILABLE,
        git_commit_sha=UNAVAILABLE,
        created_at=run.get("created_at"),
    )


def _with_manifest(run: dict) -> dict:
    payload = dict(run)
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    payload["reproducibility_manifest"] = _manifest_for_saved_run(payload)
    payload["metrics"] = metrics_without_manifest(metrics)
    return payload


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

    manifest = request.reproducibility_manifest
    if not isinstance(manifest, dict) or not manifest:
        manifest = build_reproducibility_manifest(
            data_source=request.data_source,
            symbol=request.ticker,
            universe=None,
            requested_start_date=request.start_date,
            requested_end_date=request.end_date,
            actual_start_date=MISSING,
            actual_end_date=MISSING,
            retrieval_timestamp=MISSING,
            row_count=MISSING,
            adjustment_mode=MISSING,
            protocol={
                "strategy": request.strategy,
                "ticker": request.ticker,
                **(request.strategy_config or {}),
                "transaction_cost": request.transaction_cost,
            },
            data_hash=UNAVAILABLE,
        )
    metrics = attach_manifest_to_metrics(request.metrics, manifest)

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
            metrics=metrics,
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
        "items": [_with_manifest(item) for item in items],
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

    return _with_manifest(run)


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
