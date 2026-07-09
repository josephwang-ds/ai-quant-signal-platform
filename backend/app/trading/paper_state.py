"""模拟试盘账户状态（内存版，重启后重置）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from app.risk.risk_profile import AGGRESSIVE_PROFILE


@dataclass
class PaperTradeRecord:
    trade_date: str
    symbol: str
    action: str
    price: float
    shares: float
    cash_after: float
    reason: str
    risk_level: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "shares": self.shares,
            "cash_after": self.cash_after,
            "reason": self.reason,
            "risk_level": self.risk_level,
        }


@dataclass
class PaperAccountState:
    account_id: str = "default"
    cash: float = AGGRESSIVE_PROFILE.initial_capital
    initial_capital: float = AGGRESSIVE_PROFILE.initial_capital
    ticker: str | None = None
    strategy: str | None = None
    shares: float = 0.0
    entry_price: float | None = None
    position: int = 0
    peak_equity: float = AGGRESSIVE_PROFILE.initial_capital
    realized_pnl: float = 0.0
    consecutive_losses: int = 0
    last_trade_loss_pct: float | None = None
    cooldown_until: str | None = None
    last_risk_level: int | None = None
    last_risk_label: str | None = None
    trades: list[PaperTradeRecord] = field(default_factory=list)
    notes: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def portfolio_value(self, current_price: float | None) -> float:
        if self.position <= 0 or current_price is None:
            return self.cash
        return self.cash + self.shares * current_price

    def unrealized_pnl(self, current_price: float | None) -> float:
        if self.position <= 0 or current_price is None or self.entry_price is None:
            return 0.0
        return (current_price - self.entry_price) * self.shares

    def current_drawdown(self, current_price: float | None) -> float:
        equity = self.portfolio_value(current_price)
        if self.peak_equity <= 0:
            return 0.0
        return equity / self.peak_equity - 1

    def to_dict(self, current_price: float | None = None) -> dict[str, Any]:
        equity = self.portfolio_value(current_price)
        return {
            "account_id": self.account_id,
            "cash": round(self.cash, 2),
            "initial_capital": round(self.initial_capital, 2),
            "ticker": self.ticker,
            "strategy": self.strategy,
            "shares": round(self.shares, 4),
            "entry_price": round(self.entry_price, 4) if self.entry_price else None,
            "position": self.position,
            "current_price": round(current_price, 4) if current_price else None,
            "portfolio_value": round(equity, 2),
            "unrealized_pnl": round(self.unrealized_pnl(current_price), 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "drawdown": round(self.current_drawdown(current_price), 6),
            "consecutive_losses": self.consecutive_losses,
            "cooldown_until": self.cooldown_until,
            "last_risk_level": self.last_risk_level,
            "last_risk_label": self.last_risk_label,
            "notes": self.notes,
            "updated_at": self.updated_at,
            "trade_count": len(self.trades),
        }


_ACCOUNTS: dict[str, PaperAccountState] = {}


def get_paper_account(account_id: str = "default") -> PaperAccountState:
    if account_id not in _ACCOUNTS:
        _ACCOUNTS[account_id] = PaperAccountState(account_id=account_id)
    return _ACCOUNTS[account_id]


def reset_paper_account(account_id: str = "default") -> PaperAccountState:
    _ACCOUNTS[account_id] = PaperAccountState(account_id=account_id)
    return _ACCOUNTS[account_id]


def is_in_cooldown(account: PaperAccountState, as_of: date | None = None) -> bool:
    if not account.cooldown_until:
        return False
    today = as_of or date.today()
    try:
        cooldown_date = date.fromisoformat(account.cooldown_until)
    except ValueError:
        return False
    return today <= cooldown_date
