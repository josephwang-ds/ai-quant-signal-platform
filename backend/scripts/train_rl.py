#!/usr/bin/env python3
"""Offline RL (PPO) trainer for Compare Models artifacts — experimental.

Interview framing
-----------------
Industry RL is mainly used for **optimal execution / market making**. Directional
alpha with RL is rare in production and easy to overfit. This script is a
constrained, reproducible experiment with explicit limits — not a production
alpha claim.

Contract
--------
- Dev-only deps: ``gymnasium`` + ``stable-baselines3`` (``requirements-dev.txt``).
- Custom gym env: single asset; discrete actions 空/持/满 (flat / half / full);
  state = leakage-safe feature window; reward = next-day return − turnover cost.
- Train on the chronological train segment only; test segment is evaluate-only
  (no ``learn``); shared backtest pipe includes costs; no future features in obs.
- Writes ``app/models/artifacts/rl_<TICKER>.json`` with note
  ``RL·离线·实验性·非收益承诺``. Render never installs SB3 / gymnasium.

Reproduce (from ``backend/``)::

    PYTHONPATH=. python scripts/train_rl.py \\
      --ticker SPY --start-date 2020-01-01 --split-date 2022-01-01 \\
      --out app/models/artifacts/rl_SPY.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.backtest.engine import apply_position_and_returns
from app.backtest.metrics import calculate_backtest_metrics
from app.data_providers.yahoo_provider import load_price_data
from app.models.features import FEATURE_COLUMNS, build_feature_frame
from app.models.rl_env import action_to_long_signal, build_discrete_trading_env

DEFAULT_ARTIFACT_DIR = _BACKEND_ROOT / "app" / "models" / "artifacts"
RL_NOTE = (
    "RL·离线·实验性·非收益承诺. Offline PPO; reproduce via scripts/train_rl.py. "
    "Industry RL is mostly execution/market-making — directional alpha is rare "
    "and easy to overfit; this is a constrained research experiment only."
)
INTERVIEW_NOTE = (
    "RL in production is mainly optimal execution / market making; "
    "directional alpha is uncommon and overfit-prone. This artifact is a "
    "constrained, reproducible experiment with explicit limitations."
)


def _require_rl_stack():
    try:
        import gymnasium as gym
        from gymnasium import spaces
        from stable_baselines3 import PPO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "gymnasium and stable-baselines3 are required for offline RL training. "
            "Install with: pip install -r requirements-dev.txt"
        ) from exc
    return gym, spaces, PPO


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Offline RL trading experiment → Compare Models artifact JSON"
    )
    p.add_argument("--ticker", default="SPY")
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default=None)
    p.add_argument("--split-date", required=True)
    p.add_argument("--seq-len", type=int, default=20)
    p.add_argument("--timesteps", type=int, default=20_000)
    p.add_argument("--transaction-cost", type=float, default=0.001)
    p.add_argument("--data-source", default="auto")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=None)
    return p.parse_args(argv)


def _normalized_equity_rows(
    backtest_df: pd.DataFrame, label: str = "RL (experimental)"
) -> list[dict[str, Any]]:
    if backtest_df.empty or "cumulative_strategy" not in backtest_df.columns:
        return []
    dates = pd.to_datetime(backtest_df["date"]).dt.strftime("%Y-%m-%d")
    values = pd.to_numeric(backtest_df["cumulative_strategy"], errors="coerce")
    series = pd.Series(values.to_numpy(), index=dates, dtype=float)
    series = series[~series.index.duplicated(keep="last")].dropna()
    if series.empty:
        return []
    start = float(series.iloc[0])
    norm = series if start == 0 or not math.isfinite(start) else series / start
    return [{"date": str(d), label: float(v)} for d, v in norm.items()]


def train_and_write_artifact(args: argparse.Namespace) -> Path:
    gym, spaces, PPO = _require_rl_stack()
    ticker = args.ticker.upper().strip()
    if args.seq_len < 5:
        raise SystemExit("--seq-len must be >= 5")

    out_path = Path(args.out or DEFAULT_ARTIFACT_DIR / f"rl_{ticker}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading prices for {ticker}…")
    price_df = load_price_data(
        ticker, args.start_date, args.end_date, data_source=args.data_source
    )
    X, y, aligned = build_feature_frame(price_df)
    assert list(X.columns) == FEATURE_COLUMNS
    assert "y_next_return" not in X.columns

    dates = pd.to_datetime(aligned["date"])
    split_ts = pd.to_datetime(args.split_date)
    train_mask = dates < split_ts
    test_mask = dates >= split_ts
    # Embargo: drop last train row whose label uses the first test-day close.
    train_idx = list(np.flatnonzero(train_mask.to_numpy()))[:-1]
    test_idx = list(np.flatnonzero(test_mask.to_numpy()))
    if len(train_idx) < args.seq_len + 40 or len(test_idx) < 40:
        raise SystemExit("Insufficient train/test rows around split_date.")

    scaler = StandardScaler()
    scaler.fit(X.iloc[train_idx][FEATURE_COLUMNS].to_numpy(dtype=np.float64))
    X_scaled = scaler.transform(X[FEATURE_COLUMNS].to_numpy(dtype=np.float64)).astype(
        np.float32
    )
    # Reward series = next-day return (training label), never placed in observations.
    next_rets = aligned["y_next_return"].to_numpy(dtype=np.float64)

    train_feat = X_scaled[train_idx]
    train_next = next_rets[train_idx]
    env = build_discrete_trading_env(
        spaces,
        gym,
        features=train_feat,
        next_returns=train_next,
        seq_len=args.seq_len,
        cost=args.transaction_cost,
    )
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        seed=args.seed,
        learning_rate=3e-4,
        n_steps=min(1024, max(64, len(train_idx) // 4)),
    )
    model.learn(total_timesteps=int(args.timesteps))

    # Test segment: evaluate only — no further learning.
    test_feat = X_scaled[test_idx]
    test_next = next_rets[test_idx]
    test_env = build_discrete_trading_env(
        spaces,
        gym,
        features=test_feat,
        next_returns=test_next,
        seq_len=args.seq_len,
        cost=args.transaction_cost,
    )
    obs, _ = test_env.reset(seed=args.seed)
    actions: list[int] = []
    while True:
        action, _ = model.predict(obs, deterministic=True)
        actions.append(int(action))
        obs, _, terminated, truncated, _ = test_env.step(int(action))
        if terminated or truncated:
            break

    endpoint_local = list(range(args.seq_len - 1, len(test_idx) - 1))
    n = min(len(actions), len(endpoint_local))
    endpoint_local = endpoint_local[:n]
    signal = action_to_long_signal(np.asarray(actions[:n], dtype=int))
    global_positions = [test_idx[i] for i in endpoint_local]

    model_df = aligned.iloc[global_positions][["date", "close", "daily_return"]].copy()
    model_df["model_signal"] = signal.astype(int)
    backtest_df = apply_position_and_returns(
        model_df,
        signal_col="model_signal",
        transaction_cost=args.transaction_cost,
        buy_reason="RL policy chooses long",
        sell_reason="RL policy chooses flat",
    )
    metrics = calculate_backtest_metrics(backtest_df)
    y_te = y.iloc[global_positions].to_numpy()
    directional_accuracy = (
        float(np.mean((signal == y_te).astype(float))) if len(y_te) else 0.0
    )

    trained_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    te_dates = pd.to_datetime(aligned.iloc[global_positions]["date"])
    artifact: dict[str, Any] = {
        "label": "RL (experimental)",
        "kind": "ml",
        "strategy": "rl",
        "source": "offline_artifact",
        "trained_at": trained_at,
        "ticker": ticker,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "split_date": pd.to_datetime(args.split_date).strftime("%Y-%m-%d"),
        "seq_len": int(args.seq_len),
        "feature_columns": list(FEATURE_COLUMNS),
        "metrics": metrics,
        "directional_accuracy": directional_accuracy,
        "directional_accuracy_note": (
            "directional accuracy — next-day up/down hit rate, not a return promise"
        ),
        "equity_curve": _normalized_equity_rows(backtest_df),
        "n_train_rows": int(len(train_idx)),
        "n_test_actions": int(n),
        "test_start": te_dates.iloc[0].strftime("%Y-%m-%d") if len(te_dates) else None,
        "test_end": te_dates.iloc[-1].strftime("%Y-%m-%d") if len(te_dates) else None,
        "note": RL_NOTE,
        "interview_note": INTERVIEW_NOTE,
    }
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote artifact → {out_path}")
    print(
        f"OOS directional_accuracy={directional_accuracy:.4f} "
        f"sharpe={metrics.get('sharpe_ratio')} "
        f"total_return={metrics.get('total_return')}"
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    train_and_write_artifact(_parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
