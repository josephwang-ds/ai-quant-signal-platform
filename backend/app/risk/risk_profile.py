"""Risk profile presets (aggressive / moderate / conservative)."""

from __future__ import annotations

from dataclasses import dataclass, replace


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


# Historical max-drawdown is typically much deeper than a live "current" drawdown.
# Use wider thresholds so feeding metrics["max_drawdown"] does not pin every run at L5.
HISTORICAL_DRAWDOWN_LEVELS: tuple[float, float, float, float] = (
    -0.10,
    -0.20,
    -0.35,
    -0.50,
)

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

MODERATE_PROFILE = RiskProfile(
    name="moderate",
    initial_capital=100_000.0,
    default_position_size=0.35,
    transaction_cost_rate=0.0005,
    drawdown_levels=(-0.025, -0.05, -0.08, -0.12),
    single_trade_loss_levels=(-0.025, -0.04, -0.07, -0.10),
    consecutive_loss_yellow=3,
    consecutive_loss_red=4,
    cost_drag_levels=(0.08, 0.18, 0.30, 0.45),
    portfolio_hard_stop=-0.15,
    cooldown_days_after_red=5,
)

# Conservative escalates sooner (tighter drawdown / loss thresholds).
CONSERVATIVE_PROFILE = RiskProfile(
    name="conservative",
    initial_capital=100_000.0,
    default_position_size=0.25,
    transaction_cost_rate=0.0005,
    drawdown_levels=(-0.02, -0.04, -0.07, -0.10),
    single_trade_loss_levels=(-0.02, -0.035, -0.06, -0.09),
    consecutive_loss_yellow=2,
    consecutive_loss_red=4,
    cost_drag_levels=(0.06, 0.15, 0.25, 0.40),
    portfolio_hard_stop=-0.12,
    cooldown_days_after_red=7,
)

PROFILE_BY_NAME: dict[str, RiskProfile] = {
    "aggressive": AGGRESSIVE_PROFILE,
    "moderate": MODERATE_PROFILE,
    "conservative": CONSERVATIVE_PROFILE,
}


def resolve_risk_profile(
    risk_profile: str = "aggressive",
    *,
    drawdown_mode: str = "current",
) -> RiskProfile:
    """
    Resolve a named profile; for historical drawdown mode, swap in wider
    HISTORICAL_DRAWDOWN_LEVELS while keeping other thresholds from the base profile.
    """
    base = PROFILE_BY_NAME.get(risk_profile, AGGRESSIVE_PROFILE)
    if drawdown_mode == "historical":
        return replace(base, drawdown_levels=HISTORICAL_DRAWDOWN_LEVELS)
    return base


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
