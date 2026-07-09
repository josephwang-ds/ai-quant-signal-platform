"""模拟试盘 API。"""

from fastapi import APIRouter, HTTPException, Query

from app.schemas import PaperTradingRequest
from app.trading.paper_trading import (
    build_paper_dashboard,
    execute_paper_action,
    reset_account,
)
from app.trading.paper_state import get_paper_account

router = APIRouter(prefix="/api/paper", tags=["paper-trading"])


def _request_kwargs(request: PaperTradingRequest) -> dict:
    return {
        "ticker": request.ticker,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "end_date": request.end_date.strip() if request.end_date else None,
        "short_window": request.short_window,
        "long_window": request.long_window,
        "momentum_window": request.momentum_window,
        "combined_mode": request.combined_mode,
        "transaction_cost": request.transaction_cost,
        "account_id": request.account_id,
        "notes": request.notes,
    }


@router.get("/account")
def get_paper_account_state(account_id: str = Query("default")) -> dict:
    """获取当前模拟账户快照。"""
    account = get_paper_account(account_id)
    return {
        "account": account.to_dict(),
        "trade_journal": [trade.to_dict() for trade in account.trades[-20:]],
    }


@router.post("/dashboard")
def paper_dashboard(request: PaperTradingRequest) -> dict:
    """评估今日信号、五档风控与模拟账户状态（不执行交易）。"""
    try:
        return build_paper_dashboard(**_request_kwargs(request))
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build paper trading dashboard: {exc}",
        ) from exc


@router.post("/execute")
def paper_execute(request: PaperTradingRequest) -> dict:
    """在风控允许时执行一笔模拟买卖。"""
    try:
        return execute_paper_action(**_request_kwargs(request))
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute paper trade: {exc}",
        ) from exc


@router.post("/reset")
def paper_reset(account_id: str = Query("default")) -> dict:
    """重置模拟账户为初始资金。"""
    account = reset_account(account_id)
    return {"account": account, "message": "Paper account reset."}
