"""五档风控引擎测试。"""

from app.risk.risk_monitor import (
    RiskMonitorInput,
    calculate_consecutive_loss_level,
    calculate_drawdown_level,
    calculate_overall_risk_level,
    paper_action_allowed,
)


def test_drawdown_levels() -> None:
    assert calculate_drawdown_level(0.0) == 1
    assert calculate_drawdown_level(-0.04) == 2
    assert calculate_drawdown_level(-0.08) == 3
    assert calculate_drawdown_level(-0.12) == 4
    assert calculate_drawdown_level(-0.20) == 5


def test_consecutive_loss_levels() -> None:
    assert calculate_consecutive_loss_level(0) == 1
    assert calculate_consecutive_loss_level(2) == 2
    assert calculate_consecutive_loss_level(3) == 4
    assert calculate_consecutive_loss_level(4) == 4
    assert calculate_consecutive_loss_level(5) == 5


def test_overall_risk_uses_max_component() -> None:
    assessment = calculate_overall_risk_level(
        RiskMonitorInput(
            current_drawdown=-0.02,
            consecutive_losses=4,
        )
    )
    assert assessment.risk_level == 4
    assert assessment.risk_label == "Orange"


def test_paper_action_blocked_at_high_risk() -> None:
    assert paper_action_allowed(5, "BUY") is False
    assert paper_action_allowed(4, "BUY") is False
    assert paper_action_allowed(3, "BUY") is False
    assert paper_action_allowed(3, "SELL") is True
