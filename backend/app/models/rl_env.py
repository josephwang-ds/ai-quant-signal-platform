"""Offline RL trading environment — gymnasium optional at import time.

Used by ``scripts/train_rl.py``. Production runtime never imports this module.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def build_discrete_trading_env(
    spaces: Any,
    gym: Any,
    *,
    features: np.ndarray,
    next_returns: np.ndarray,
    seq_len: int,
    cost: float,
) -> Any:
    """
    Single-asset env: actions flat / half / full; reward = next-day return × pos − cost.

    Observation at index ``t`` is the feature window ending at ``t`` (no future bars).
    Reward for the action taken at ``t`` is ``next_returns[t]`` (close_t → close_{t+1})
    minus turnover cost — the training label, never part of the observation.
    """

    class DiscreteTradingEnv(gym.Env):
        metadata = {"render_modes": []}

        def __init__(self) -> None:
            super().__init__()
            if len(features) != len(next_returns):
                raise ValueError("features and next_returns length mismatch")
            if seq_len < 2 or seq_len >= len(features):
                raise ValueError("seq_len out of range for feature series")
            self.features = np.asarray(features, dtype=np.float32)
            self.next_returns = np.asarray(next_returns, dtype=np.float64)
            self.seq_len = int(seq_len)
            self.cost = float(cost)
            n_f = self.features.shape[1]
            self.observation_space = spaces.Box(
                low=-10.0,
                high=10.0,
                shape=(self.seq_len * n_f,),
                dtype=np.float32,
            )
            # 0=空(flat), 1=持(half), 2=满(full)
            self.action_space = spaces.Discrete(3)
            self._pos = self.seq_len - 1
            self._position = 0.0

        def _obs(self) -> np.ndarray:
            window = self.features[self._pos - self.seq_len + 1 : self._pos + 1]
            return window.reshape(-1).astype(np.float32)

        def reset(self, *, seed: int | None = None, options: dict | None = None):
            super().reset(seed=seed)
            self._pos = self.seq_len - 1
            self._position = 0.0
            return self._obs(), {}

        def step(self, action: int):
            target = {0: 0.0, 1: 0.5, 2: 1.0}.get(int(action), 0.0)
            turnover = abs(target - self._position)
            cost_paid = turnover * self.cost
            # Next-day return only — never today's already-realized daily_return.
            r = float(self.next_returns[self._pos]) * target - cost_paid
            self._position = target
            self._pos += 1
            # Stop before the final row so every reward had a defined next day in-slice.
            terminated = self._pos >= len(self.features) - 1
            truncated = False
            return self._obs(), float(r), terminated, truncated, {}

    return DiscreteTradingEnv()


def action_to_long_signal(actions: np.ndarray) -> np.ndarray:
    """Map half/full → long (1); flat → 0 for the shared long/flat backtest pipe."""
    return (np.asarray(actions) >= 1).astype(int)
