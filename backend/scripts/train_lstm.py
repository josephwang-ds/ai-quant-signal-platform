#!/usr/bin/env python3
"""Offline LSTM trainer for Compare Models artifacts.

LSTM is trained offline; results ship as JSON artifacts in
``app/models/artifacts/``. The Render / production runtime does **not**
install torch and does **not** run LSTM inference.

Reproduce (from ``backend/``, with requirements-dev.txt installed)::

    PYTHONPATH=. python scripts/train_lstm.py \\
      --ticker SPY --start-date 2020-01-01 --split-date 2022-01-01 \\
      --seq-len 20 --epochs 40 \\
      --out app/models/artifacts/lstm_SPY.json

Leakage discipline matches other models: FEATURE_COLUMNS only, chronological
split, scaler fit on train only, embargo at the train/test boundary, validation
carved from the end of the train window (never from test).
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
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# Allow ``python scripts/train_lstm.py`` from backend/ without requiring PYTHONPATH=.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.backtest.engine import apply_position_and_returns
from app.backtest.metrics import calculate_backtest_metrics
from app.data_providers.yahoo_provider import load_price_data
from app.models.features import FEATURE_COLUMNS, build_feature_frame

DEFAULT_ARTIFACT_DIR = _BACKEND_ROOT / "app" / "models" / "artifacts"
MIN_TRAIN_SEQUENCES = 80
MIN_TEST_SEQUENCES = 40
DEFAULT_VAL_FRACTION = 0.15
EARLY_STOP_PATIENCE = 8


def _require_torch():
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as exc:  # pragma: no cover - offline tooling
        raise SystemExit(
            "torch is required for offline LSTM training. "
            "Install with: pip install -r requirements-dev.txt"
        ) from exc
    return torch, nn, DataLoader, TensorDataset


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline-train a small LSTM for next-day direction and write a "
            "Compare Models artifact (JSON + optional .pt). Not used at runtime."
        )
    )
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--split-date", required=True)
    parser.add_argument("--seq-len", type=int, default=20)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--hidden", type=int, default=32)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-fraction", type=float, default=DEFAULT_VAL_FRACTION)
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    parser.add_argument("--data-source", default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        default=None,
        help="Artifact JSON path (default: app/models/artifacts/lstm_<TICKER>.json)",
    )
    parser.add_argument(
        "--weights-out",
        default=None,
        help="Optional .pt path (default: sibling of --out with .pt suffix)",
    )
    return parser.parse_args(argv)


def _build_endpoint_sequences(
    X_values: np.ndarray,
    y_values: np.ndarray,
    dates: pd.Series,
    endpoint_positions: list[int],
    seq_len: int,
) -> tuple[np.ndarray, np.ndarray, list[pd.Timestamp], list[int]]:
    """Build (N, seq_len, F) sequences ending at allowed positions."""
    xs: list[np.ndarray] = []
    ys: list[float] = []
    end_dates: list[pd.Timestamp] = []
    end_positions: list[int] = []
    allowed = set(endpoint_positions)
    for pos in endpoint_positions:
        start = pos - seq_len + 1
        if start < 0 or pos not in allowed:
            continue
        window = X_values[start : pos + 1]
        if window.shape[0] != seq_len:
            continue
        xs.append(window.astype(np.float32))
        ys.append(float(y_values[pos]))
        end_dates.append(pd.to_datetime(dates.iloc[pos]))
        end_positions.append(pos)
    if not xs:
        return (
            np.empty((0, seq_len, X_values.shape[1]), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            [],
            [],
        )
    return np.stack(xs), np.asarray(ys, dtype=np.float32), end_dates, end_positions


def _make_lstm(nn: Any, *, n_features: int, hidden: int, layers: int) -> Any:
    class SmallLSTM(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            dropout = 0.2 if layers > 1 else 0.0
            self.lstm = nn.LSTM(
                input_size=n_features,
                hidden_size=hidden,
                num_layers=layers,
                batch_first=True,
                dropout=dropout,
            )
            self.head = nn.Linear(hidden, 1)

        def forward(self, x: Any) -> Any:
            out, _ = self.lstm(x)
            logits = self.head(out[:, -1, :])
            return logits.squeeze(-1)

    return SmallLSTM()


def _train_lstm(
    *,
    torch: Any,
    nn: Any,
    DataLoader: Any,
    TensorDataset: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_features: int,
    hidden: int,
    layers: int,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> tuple[Any, dict[str, Any]]:
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cpu")
    model = _make_lstm(nn, n_features=n_features, hidden=hidden, layers=layers).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()

    train_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(X_train),
            torch.from_numpy(y_train),
        ),
        batch_size=batch_size,
        shuffle=False,  # chronological batches; no shuffle for time series
    )
    X_val_t = torch.from_numpy(X_val).to(device)
    y_val_t = torch.from_numpy(y_val).to(device)

    best_state: dict[str, Any] | None = None
    best_val = math.inf
    patience_left = EARLY_STOP_PATIENCE
    history: list[dict[str, float]] = []

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_sum = 0.0
        n_batches = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            train_loss_sum += float(loss.item())
            n_batches += 1

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_loss = float(criterion(val_logits, y_val_t).item())

        train_loss = train_loss_sum / max(n_batches, 1)
        history.append({"epoch": float(epoch), "train_loss": train_loss, "val_loss": val_loss})

        if val_loss + 1e-6 < best_val:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = EARLY_STOP_PATIENCE
        else:
            patience_left -= 1
            if patience_left <= 0:
                break

    if best_state is None:
        raise RuntimeError("LSTM training produced no checkpoint.")
    model.load_state_dict(best_state)
    model.eval()
    return model, {
        "best_val_loss": best_val,
        "epochs_ran": len(history),
        "history": history,
    }


def _predict_signals(
    torch: Any,
    model: Any,
    X_seq: np.ndarray,
) -> np.ndarray:
    device = torch.device("cpu")
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(X_seq).to(device))
        proba = torch.sigmoid(logits).cpu().numpy()
    return (proba >= 0.5).astype(int)


def _normalized_equity_rows(backtest_df: pd.DataFrame, label: str = "LSTM") -> list[dict[str, Any]]:
    if backtest_df.empty or "cumulative_strategy" not in backtest_df.columns:
        return []
    dates = pd.to_datetime(backtest_df["date"]).dt.strftime("%Y-%m-%d")
    values = pd.to_numeric(backtest_df["cumulative_strategy"], errors="coerce")
    series = pd.Series(values.to_numpy(), index=dates, dtype=float)
    series = series[~series.index.duplicated(keep="last")].dropna()
    if series.empty:
        return []
    start = float(series.iloc[0])
    if start == 0 or not math.isfinite(start):
        norm = series
    else:
        norm = series / start
    return [{"date": str(date), label: float(value)} for date, value in norm.items()]


def train_and_write_artifact(args: argparse.Namespace) -> Path:
    torch, nn, DataLoader, TensorDataset = _require_torch()

    ticker = args.ticker.upper().strip()
    if args.seq_len < 5:
        raise SystemExit("--seq-len must be >= 5")
    if args.layers < 1 or args.layers > 2:
        raise SystemExit("--layers must be 1 or 2")
    if args.hidden < 8 or args.hidden > 64:
        raise SystemExit("--hidden should be in [8, 64] for this small model")
    if not (0.05 <= args.val_fraction <= 0.35):
        raise SystemExit("--val-fraction must be between 0.05 and 0.35")

    out_path = Path(
        args.out
        if args.out
        else DEFAULT_ARTIFACT_DIR / f"lstm_{ticker}.json"
    )
    weights_path = Path(
        args.weights_out
        if args.weights_out
        else out_path.with_suffix(".pt")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading prices for {ticker}…")
    price_df = load_price_data(
        ticker,
        args.start_date,
        args.end_date,
        data_source=args.data_source,
    )
    X, y, aligned = build_feature_frame(price_df)
    if aligned.empty:
        raise SystemExit("Feature frame is empty after alignment.")

    assert list(X.columns) == FEATURE_COLUMNS
    assert "y_next_up" not in X.columns

    dates = pd.to_datetime(aligned["date"])
    split_ts = pd.to_datetime(args.split_date)
    train_mask = dates < split_ts
    test_mask = dates >= split_ts
    train_positions = list(np.flatnonzero(train_mask.to_numpy()))
    test_positions = list(np.flatnonzero(test_mask.to_numpy()))

    if len(train_positions) < args.seq_len + 10 or len(test_positions) < 10:
        raise SystemExit(
            f"Insufficient rows around split_date "
            f"(train={len(train_positions)}, test={len(test_positions)})."
        )

    # Embargo: drop the last training row whose label uses the first test-day close.
    train_positions = train_positions[:-1]
    if not train_positions:
        raise SystemExit("Training set empty after embargo.")

    # Scaler fit on train rows only (never test).
    scaler = StandardScaler()
    X_train_fit = X.iloc[train_positions][FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    scaler.fit(X_train_fit)
    X_scaled = scaler.transform(X[FEATURE_COLUMNS].to_numpy(dtype=np.float64)).astype(
        np.float32
    )
    y_values = y.to_numpy(dtype=np.float32)

    X_tr_all, y_tr_all, _, _ = _build_endpoint_sequences(
        X_scaled, y_values, dates, train_positions, args.seq_len
    )
    X_te, y_te, te_dates, te_positions = _build_endpoint_sequences(
        X_scaled, y_values, dates, test_positions, args.seq_len
    )

    if len(X_tr_all) < MIN_TRAIN_SEQUENCES:
        raise SystemExit(
            f"Need at least {MIN_TRAIN_SEQUENCES} train sequences; got {len(X_tr_all)}."
        )
    if len(X_te) < MIN_TEST_SEQUENCES:
        raise SystemExit(
            f"Need at least {MIN_TEST_SEQUENCES} test sequences; got {len(X_te)}."
        )

    # Validation = chronological tail of train sequences (never touches test).
    n_val = max(1, int(round(len(X_tr_all) * args.val_fraction)))
    n_val = min(n_val, len(X_tr_all) // 4) if len(X_tr_all) >= 40 else n_val
    n_fit = len(X_tr_all) - n_val
    if n_fit < MIN_TRAIN_SEQUENCES // 2:
        raise SystemExit("Not enough train sequences after carving validation.")

    X_fit, y_fit = X_tr_all[:n_fit], y_tr_all[:n_fit]
    X_val, y_val = X_tr_all[n_fit:], y_tr_all[n_fit:]

    print(
        f"Sequences — fit={len(X_fit)}, val={len(X_val)}, test={len(X_te)}; "
        f"seq_len={args.seq_len}, features={len(FEATURE_COLUMNS)}"
    )

    model, train_info = _train_lstm(
        torch=torch,
        nn=nn,
        DataLoader=DataLoader,
        TensorDataset=TensorDataset,
        X_train=X_fit,
        y_train=y_fit,
        X_val=X_val,
        y_val=y_val,
        n_features=len(FEATURE_COLUMNS),
        hidden=args.hidden,
        layers=args.layers,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
    )

    signal = _predict_signals(torch, model, X_te)
    directional_accuracy = float(accuracy_score(y_te, signal))

    # Map predictions onto aligned test rows (sequence endpoints only).
    model_df = aligned.iloc[te_positions][["date", "close", "daily_return"]].copy()
    model_df["model_signal"] = signal.astype(int)
    backtest_df = apply_position_and_returns(
        model_df,
        signal_col="model_signal",
        transaction_cost=args.transaction_cost,
        buy_reason="LSTM predicts next-day up",
        sell_reason="LSTM predicts next-day down",
    )
    metrics = calculate_backtest_metrics(backtest_df)
    equity_curve = _normalized_equity_rows(backtest_df, label="LSTM")

    trained_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    artifact: dict[str, Any] = {
        "label": "LSTM",
        "kind": "ml",
        "strategy": "lstm",
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
        "equity_curve": equity_curve,
        "n_train_sequences": int(len(X_fit)),
        "n_val_sequences": int(len(X_val)),
        "n_test_sequences": int(len(X_te)),
        "test_start": te_dates[0].strftime("%Y-%m-%d"),
        "test_end": te_dates[-1].strftime("%Y-%m-%d"),
        "train_info": {
            "best_val_loss": train_info["best_val_loss"],
            "epochs_ran": train_info["epochs_ran"],
            "hidden": int(args.hidden),
            "layers": int(args.layers),
        },
        "note": (
            "Offline-trained; results as of trained_at. "
            "Reproduce via scripts/train_lstm.py"
        ),
    }

    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote artifact: {out_path}")

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "scaler_mean": scaler.mean_.tolist(),
            "scaler_scale": scaler.scale_.tolist(),
            "feature_columns": list(FEATURE_COLUMNS),
            "seq_len": int(args.seq_len),
            "hidden": int(args.hidden),
            "layers": int(args.layers),
            "ticker": ticker,
            "split_date": artifact["split_date"],
            "trained_at": trained_at,
        },
        weights_path,
    )
    print(f"Wrote weights:   {weights_path}")
    print(
        f"OOS directional_accuracy={directional_accuracy:.4f} "
        f"sharpe={metrics.get('sharpe_ratio')} "
        f"total_return={metrics.get('total_return')}"
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    train_and_write_artifact(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
