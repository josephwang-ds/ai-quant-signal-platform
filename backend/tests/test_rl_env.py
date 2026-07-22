"""Offline RL env guards — gymnasium optional; never imports stable-baselines3."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("gymnasium")

import gymnasium as gym
from gymnasium import spaces

from app.models.rl_env import action_to_long_signal, build_discrete_trading_env


def test_reward_uses_next_day_return_minus_cost() -> None:
    # Constant features; next returns known a priori for the reward check.
    features = np.zeros((12, 3), dtype=np.float32)
    next_returns = np.array(
        [0.01, 0.02, -0.01, 0.0, 0.03, 0.01, -0.02, 0.01, 0.0, 0.02, 0.01, 0.0],
        dtype=np.float64,
    )
    env = build_discrete_trading_env(
        spaces,
        gym,
        features=features,
        next_returns=next_returns,
        seq_len=3,
        cost=0.001,
    )
    obs, _ = env.reset(seed=0)
    assert obs.shape == (9,)

    # First action: flat → half (turnover 0.5) at pos=2 → reward = 0.5*(-0.01) - 0.0005
    obs2, reward, terminated, truncated, _ = env.step(1)
    assert not terminated and not truncated
    assert reward == pytest.approx(0.5 * (-0.01) - 0.5 * 0.001)
    assert obs2.shape == (9,)


def test_observation_excludes_future_rows() -> None:
    rng = np.random.default_rng(0)
    features = rng.normal(size=(20, 4)).astype(np.float32)
    # Put a huge spike only in the final rows — early obs windows must not see it.
    features[-1] = 99.0
    next_returns = rng.normal(0, 0.01, size=20)
    env = build_discrete_trading_env(
        spaces,
        gym,
        features=features,
        next_returns=next_returns,
        seq_len=5,
        cost=0.0,
    )
    obs, _ = env.reset(seed=1)
    assert 99.0 not in obs.tolist()


def test_action_to_long_signal_mapping() -> None:
    assert action_to_long_signal(np.array([0, 1, 2])).tolist() == [0, 1, 1]
