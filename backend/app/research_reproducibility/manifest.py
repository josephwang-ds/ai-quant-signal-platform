"""Stable reproducibility metadata and content hashes for research artifacts.

Hash contract:
1. Serialize normalized inputs with stable column order and stable date order
2. SHA-256
3. Explicit missing-value representation (``MISSING``)
4. No random object addresses or unstable timestamps inside hash inputs
5. Same inputs → same hash
6. Protocol hash independent of dict key order when semantics are identical
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from app.research_execution.market_data_port import utc_now_iso

MISSING = "__MISSING__"
UNAVAILABLE = "unavailable"

PROTOCOL_VERSION = "reproducibility-manifest/v1"
ENGINE_VERSION = "research-calc/v1"

# Stable column order for OHLCV data fingerprints.
DATA_HASH_COLUMNS: tuple[str, ...] = (
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def canonicalize(value: Any) -> Any:
    """Normalize a value for stable hashing (no object addresses / NaN noise)."""
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return value
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return MISSING
        return number
    if isinstance(value, (datetime, pd.Timestamp)):
        ts = pd.Timestamp(value)
        if pd.isna(ts):
            return MISSING
        if ts.tzinfo is not None:
            return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        return ts.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(
            (canonicalize(item) for item in value),
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, np.ndarray):
        return [canonicalize(item) for item in value.tolist()]
    # Never embed id()/repr() object addresses in hash inputs.
    return MISSING


def stable_serialize(value: Any) -> bytes:
    """JSON-serialize a canonicalized value with stable key order."""
    payload = canonicalize(value)
    text = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def hash_protocol(protocol: Mapping[str, Any] | None) -> str:
    """SHA-256 of protocol parameters; dict key order does not affect the result."""
    return sha256_hex(stable_serialize(protocol or {}))


def hash_ohlcv_frame(
    frame: pd.DataFrame | None,
    *,
    columns: Sequence[str] | None = None,
) -> str:
    """Fingerprint a market frame with stable columns and ascending date order."""
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return sha256_hex(stable_serialize({"columns": [], "rows": []}))

    preferred = tuple(columns) if columns is not None else DATA_HASH_COLUMNS
    present = [name for name in preferred if name in frame.columns]
    if not present:
        # Fall back to sorted remaining columns so callers still get a stable hash.
        present = sorted(str(name) for name in frame.columns)

    work = frame.loc[:, present].copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        sort_keys = ["date"]
        if "symbol" in work.columns:
            work["symbol"] = work["symbol"].astype(str).str.upper()
            sort_keys = ["symbol", "date"]
        work = work.sort_values(sort_keys, kind="mergesort").reset_index(drop=True)
        work["date"] = work["date"].dt.strftime("%Y-%m-%d")
        work["date"] = work["date"].where(work["date"].notna(), other=None)

    rows: list[list[Any]] = []
    for record in work.itertuples(index=False, name=None):
        row: list[Any] = []
        for cell in record:
            if cell is None or (isinstance(cell, float) and math.isnan(cell)):
                row.append(MISSING)
            elif isinstance(cell, (pd.Timestamp, datetime, date)):
                row.append(canonicalize(cell))
            elif isinstance(cell, (np.floating, float)):
                number = float(cell)
                row.append(MISSING if math.isnan(number) or math.isinf(number) else number)
            elif isinstance(cell, (np.integer, int)) and not isinstance(cell, bool):
                row.append(int(cell))
            elif isinstance(cell, (np.bool_, bool)):
                row.append(bool(cell))
            elif pd.isna(cell):
                row.append(MISSING)
            else:
                row.append(str(cell) if not isinstance(cell, str) else cell)
        rows.append(row)

    return sha256_hex(stable_serialize({"columns": present, "rows": rows}))


@lru_cache(maxsize=1)
def resolve_git_commit_sha() -> str:
    """Return the repository commit SHA, or ``unavailable`` when unknown.

    Never fabricates a SHA. Checks ``GIT_COMMIT_SHA`` / ``SOURCE_COMMIT`` first,
    then ``git rev-parse HEAD`` from the repository root.
    """
    for env_key in ("GIT_COMMIT_SHA", "SOURCE_COMMIT", "RENDER_GIT_COMMIT"):
        value = (os.environ.get(env_key) or "").strip()
        if value and value.lower() not in {"unknown", "unavailable", "none"}:
            return value

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return UNAVAILABLE

    if completed.returncode != 0:
        return UNAVAILABLE
    sha = (completed.stdout or "").strip()
    if not sha or sha.lower() in {"unknown", "unavailable"}:
        return UNAVAILABLE
    return sha


def resolve_runtime_version() -> str:
    info = sys.version_info
    return f"python/{info.major}.{info.minor}.{info.micro}"


def _as_manifest_value(value: Any) -> Any:
    if value is None or value == "":
        return MISSING
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    return canonicalize(value)


def build_reproducibility_manifest(
    *,
    data_source: Any = None,
    symbol: Any = None,
    universe: Any = None,
    requested_start_date: Any = None,
    requested_end_date: Any = None,
    actual_start_date: Any = None,
    actual_end_date: Any = None,
    retrieval_timestamp: Any = None,
    row_count: Any = None,
    adjustment_mode: Any = None,
    protocol: Mapping[str, Any] | None = None,
    protocol_version: str = PROTOCOL_VERSION,
    data_hash: str | None = None,
    frame: pd.DataFrame | None = None,
    engine_version: str = ENGINE_VERSION,
    git_commit_sha: str | None = None,
    runtime_version: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Assemble the Phase 5 reproducibility manifest for an evidence artifact."""
    protocol_payload = dict(protocol or {})
    resolved_data_hash = data_hash if data_hash is not None else hash_ohlcv_frame(frame)
    resolved_git = (
        git_commit_sha
        if git_commit_sha is not None and str(git_commit_sha).strip()
        else resolve_git_commit_sha()
    )
    if not resolved_git or str(resolved_git).lower() in {"unknown", "none", ""}:
        resolved_git = UNAVAILABLE

    row_count_value: Any
    if row_count is None and frame is not None:
        row_count_value = int(len(frame))
    elif row_count is None:
        row_count_value = MISSING
    else:
        try:
            row_count_value = int(row_count)
        except (TypeError, ValueError):
            row_count_value = MISSING

    return {
        "data_source": _as_manifest_value(data_source),
        "symbol": _as_manifest_value(symbol),
        "universe": _as_manifest_value(universe),
        "requested_start_date": _as_manifest_value(requested_start_date),
        "requested_end_date": _as_manifest_value(requested_end_date),
        "actual_start_date": _as_manifest_value(actual_start_date),
        "actual_end_date": _as_manifest_value(actual_end_date),
        "retrieval_timestamp": _as_manifest_value(retrieval_timestamp),
        "row_count": row_count_value,
        "adjustment_mode": _as_manifest_value(adjustment_mode),
        "protocol_version": protocol_version,
        "protocol_hash": hash_protocol(protocol_payload),
        "data_hash": resolved_data_hash,
        "engine_version": engine_version,
        "git_commit_sha": resolved_git,
        "runtime_version": runtime_version or resolve_runtime_version(),
        "created_at": created_at or utc_now_iso(),
    }


def extract_manifest_from_metrics(metrics: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Pull a stored manifest out of a metrics blob without mutating the caller."""
    if not isinstance(metrics, Mapping):
        return None
    raw = metrics.get("reproducibility_manifest")
    return dict(raw) if isinstance(raw, Mapping) else None


def metrics_without_manifest(metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metrics, Mapping):
        return {}
    return {
        key: value
        for key, value in metrics.items()
        if key != "reproducibility_manifest"
    }


def attach_manifest_to_metrics(
    metrics: Mapping[str, Any] | None,
    manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(metrics or {})
    if isinstance(manifest, Mapping) and manifest:
        payload["reproducibility_manifest"] = dict(manifest)
    return payload
