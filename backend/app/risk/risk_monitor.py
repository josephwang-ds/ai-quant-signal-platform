"""五档风控引擎（最高风险优先）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.risk.risk_profile import (
    AGGRESSIVE_PROFILE,
    ALLOWED_ACTIONS,
    RISK_LABELS,
    RiskProfile,
)


def _level_from_thresholds(value: float, thresholds: tuple[float, float, float, float]) -> int:
    """值越差（更负或更大），等级越高。"""
    if value >= thresholds[0]:
        return 1
    if value >= thresholds[1]:
        return 2
    if value >= thresholds[2]:
        return 3
    if value >= thresholds[3]:
        return 4
    return 5


def calculate_drawdown_level(drawdown: float, profile: RiskProfile = AGGRESSIVE_PROFILE) -> int:
    return _level_from_thresholds(drawdown, profile.drawdown_levels)


def calculate_single_trade_loss_level(
    trade_loss_pct: float | None,
    profile: RiskProfile = AGGRESSIVE_PROFILE,
) -> int:
    if trade_loss_pct is None:
        return 1
    return _level_from_thresholds(trade_loss_pct, profile.single_trade_loss_levels)


def calculate_consecutive_loss_level(
    consecutive_losses: int,
    profile: RiskProfile = AGGRESSIVE_PROFILE,
) -> int:
    if consecutive_losses <= 1:
        return 1
    if consecutive_losses == 2:
        return 2
    if consecutive_losses < profile.consecutive_loss_yellow:
        return 3
    if consecutive_losses < profile.consecutive_loss_red:
        return 4
    return 5


def calculate_volatility_level(
    volatility: float | None,
    baseline_volatility: float | None = None,
) -> int:
    if volatility is None:
        return 1
    baseline = baseline_volatility or volatility
    if baseline <= 0:
        return 1
    ratio = volatility / baseline
    if ratio <= 1.1:
        return 1
    if ratio <= 1.25:
        return 2
    if ratio <= 1.45:
        return 3
    if ratio <= 1.7:
        return 4
    return 5


def calculate_cost_drag_level(
    cost_drag_ratio: float | None,
    profile: RiskProfile = AGGRESSIVE_PROFILE,
) -> int:
    if cost_drag_ratio is None or cost_drag_ratio <= 0:
        return 1
    t1, t2, t3, t4 = profile.cost_drag_levels
    if cost_drag_ratio < t1:
        return 1
    if cost_drag_ratio < t2:
        return 2
    if cost_drag_ratio < t3:
        return 3
    if cost_drag_ratio < t4:
        return 4
    return 5


def calculate_signal_conflict_level(
    ma_signal: int | None,
    momentum_signal: int | None,
) -> int:
    if ma_signal is None or momentum_signal is None:
        return 1
    if ma_signal == momentum_signal:
        return 1
    return 3


def calculate_sharpe_decline_level(
    sharpe_ratio: float | None,
    recent_sharpe: float | None,
) -> int:
    if sharpe_ratio is None or recent_sharpe is None:
        return 1
    if recent_sharpe >= sharpe_ratio * 0.85 and recent_sharpe > 0.5:
        return 1
    if recent_sharpe >= 0.3:
        return 2
    if recent_sharpe >= 0:
        return 3
    if recent_sharpe >= -0.3:
        return 4
    return 5


@dataclass
class RiskMonitorInput:
    current_drawdown: float
    last_trade_loss_pct: float | None = None
    consecutive_losses: int = 0
    volatility: float | None = None
    baseline_volatility: float | None = None
    sharpe_ratio: float | None = None
    recent_sharpe: float | None = None
    cost_drag_ratio: float | None = None
    ma_signal: int | None = None
    momentum_signal: int | None = None


@dataclass
class RiskAssessment:
    risk_level: int
    risk_label: str
    allowed_action: str
    risk_reasons: list[str] = field(default_factory=list)
    component_levels: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "risk_label": self.risk_label,
            "allowed_action": self.allowed_action,
            "risk_reasons": self.risk_reasons,
            "component_levels": self.component_levels,
        }


def calculate_overall_risk_level(
    inputs: RiskMonitorInput,
    profile: RiskProfile = AGGRESSIVE_PROFILE,
) -> RiskAssessment:
    components = {
        "drawdown": calculate_drawdown_level(inputs.current_drawdown, profile),
        "single_trade_loss": calculate_single_trade_loss_level(
            inputs.last_trade_loss_pct, profile
        ),
        "consecutive_losses": calculate_consecutive_loss_level(
            inputs.consecutive_losses, profile
        ),
        "volatility": calculate_volatility_level(
            inputs.volatility, inputs.baseline_volatility
        ),
        "sharpe_decline": calculate_sharpe_decline_level(
            inputs.sharpe_ratio, inputs.recent_sharpe
        ),
        "cost_drag": calculate_cost_drag_level(inputs.cost_drag_ratio, profile),
        "signal_conflict": calculate_signal_conflict_level(
            inputs.ma_signal, inputs.momentum_signal
        ),
    }

    risk_level = max(components.values())
    reasons: list[str] = []

    if components["drawdown"] >= 2:
        reasons.append(f"Current drawdown reached {inputs.current_drawdown:.1%}")
    if components["single_trade_loss"] >= 2 and inputs.last_trade_loss_pct is not None:
        reasons.append(f"Last trade loss was {inputs.last_trade_loss_pct:.1%}")
    if components["consecutive_losses"] >= 2:
        reasons.append(f"Consecutive losing trades: {inputs.consecutive_losses}")
    if components["volatility"] >= 3 and inputs.volatility is not None:
        reasons.append(f"Volatility elevated at {inputs.volatility:.1%}")
    if components["sharpe_decline"] >= 3:
        reasons.append("Recent Sharpe ratio declined")
    if components["cost_drag"] >= 3 and inputs.cost_drag_ratio is not None:
        reasons.append(f"Transaction costs are {inputs.cost_drag_ratio:.0%} of gross return")
    if components["signal_conflict"] >= 3:
        reasons.append("MA and momentum signals conflict")

    if not reasons:
        reasons.append("Risk indicators are within normal range")

    return RiskAssessment(
        risk_level=risk_level,
        risk_label=RISK_LABELS[risk_level],
        allowed_action=ALLOWED_ACTIONS[risk_level],
        risk_reasons=reasons,
        component_levels=components,
    )


def paper_action_allowed(risk_level: int, desired_action: str) -> bool:
    """根据风控等级判断是否允许模拟动作。"""
    action = desired_action.upper()
    if risk_level >= 5:
        return action in {"SELL", "WAIT", "HOLD"}
    if risk_level >= 4:
        return action in {"SELL", "HOLD", "WAIT"}
    if risk_level >= 3:
        return action in {"SELL", "HOLD", "WAIT"}
    return True
