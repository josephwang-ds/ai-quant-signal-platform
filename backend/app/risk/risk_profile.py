"""Aggressive 风控配置（与设计文档 3.5 节一致）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskProfile:
    name: str
    initial_capital: float
    default_position_size: float
    transaction_cost_rate: float
    drawdown_levels: tuple[float, float, float, float]
    single_trade_loss_levels: tuple[float, float, float, float]
    consecutive_loss_yellow: int
    consecutive_loss_red: int
    cost_drag_levels: tuple[float, float, float, float]
    portfolio_hard_stop: float
    cooldown_days_after_red: int


AGGRESSIVE_PROFILE = RiskProfile(
    name="aggressive",
    initial_capital=100_000.0,
    default_position_size=0.5,
    transaction_cost_rate=0.0005,
    drawdown_levels=(-0.03, -0.06, -0.10, -0.15),
    single_trade_loss_levels=(-0.03, -0.05, -0.08, -0.12),
    consecutive_loss_yellow=3,
    consecutive_loss_red=5,
    cost_drag_levels=(0.10, 0.20, 0.35, 0.50),
    portfolio_hard_stop=-0.20,
    cooldown_days_after_red=5,
)

RISK_LABELS: dict[int, str] = {
    1: "Green",
    2: "Light Yellow",
    3: "Yellow",
    4: "Orange",
    5: "Red",
}

RISK_LABELS_ZH: dict[int, str] = {
    1: "正常",
    2: "轻度预警",
    3: "谨慎",
    4: "高风险",
    5: "停止跟随",
}

ALLOWED_ACTIONS: dict[int, str] = {
    1: "Normal paper trading",
    2: "Cautious paper trading",
    3: "Hold or reduce only",
    4: "No new positions",
    5: "Stop following / cooldown",
}

ALLOWED_ACTIONS_ZH: dict[int, str] = {
    1: "正常模拟",
    2: "小心模拟",
    3: "仅持有或减仓",
    4: "暂停新增仓位",
    5: "停止模拟跟随",
}
