"""Phase 5 reproducibility manifest hash and snapshot contract tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.research_agent.evidence import build_evidence_snapshot
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter
from app.research_reproducibility import (
    MISSING,
    UNAVAILABLE,
    build_reproducibility_manifest,
    hash_ohlcv_frame,
    hash_protocol,
)
from app.research_reproducibility.manifest import canonicalize, stable_serialize
from app.research_validation.result_store import InMemoryValidationResultStore
from app.research_validation.service import ResearchValidationService

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "spy_daily_sample.csv"


@pytest.fixture
def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["SPY", "SPY", "SPY"],
            "date": ["2020-01-03", "2020-01-02", "2020-01-06"],
            "open": [100.0, 99.0, 101.0],
            "high": [101.0, 100.0, 102.0],
            "low": [99.0, 98.0, 100.0],
            "close": [100.5, 99.5, 101.5],
            "adjusted_close": [100.5, 99.5, 101.5],
            "volume": [1000, 1100, 1200],
        }
    )


def test_same_input_same_data_hash(sample_frame: pd.DataFrame) -> None:
    left = hash_ohlcv_frame(sample_frame)
    right = hash_ohlcv_frame(sample_frame.copy())
    assert left == right
    assert len(left) == 64


def test_one_row_change_changes_data_hash(sample_frame: pd.DataFrame) -> None:
    baseline = hash_ohlcv_frame(sample_frame)
    changed = sample_frame.copy()
    changed.loc[0, "close"] = 123.45
    assert hash_ohlcv_frame(changed) != baseline


def test_date_order_does_not_change_data_hash(sample_frame: pd.DataFrame) -> None:
    sorted_frame = sample_frame.sort_values("date").reset_index(drop=True)
    shuffled = sample_frame.sample(frac=1.0, random_state=7).reset_index(drop=True)
    assert hash_ohlcv_frame(sorted_frame) == hash_ohlcv_frame(shuffled)


def test_param_change_changes_protocol_hash() -> None:
    base = {"short_window": 20, "long_window": 60, "transaction_cost": 0.001}
    changed = {**base, "short_window": 30}
    assert hash_protocol(base) != hash_protocol(changed)


def test_dict_key_order_irrelevant_for_protocol_hash() -> None:
    left = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    right = {"a": 1, "nested": {"y": 8, "z": 9}, "b": 2}
    assert hash_protocol(left) == hash_protocol(right)
    assert stable_serialize(left) == stable_serialize(right)


def test_missing_values_are_explicit() -> None:
    assert canonicalize(None) == MISSING
    assert canonicalize(float("nan")) == MISSING
    frame = pd.DataFrame(
        {
            "date": ["2020-01-02"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [float("nan")],
            "volume": [10],
        }
    )
    digest = hash_ohlcv_frame(frame)
    assert isinstance(digest, str) and len(digest) == 64


def test_manifest_never_fabricates_git_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("SOURCE_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    from app.research_reproducibility import manifest as manifest_mod

    class _Failed:
        returncode = 1
        stdout = ""

    manifest_mod.resolve_git_commit_sha.cache_clear()
    monkeypatch.setattr(
        manifest_mod.subprocess,
        "run",
        lambda *args, **kwargs: _Failed(),
    )
    built = build_reproducibility_manifest(
        data_source="fixture",
        symbol="SPY",
        protocol={"short_window": 20},
        data_hash="abc",
    )
    assert built["git_commit_sha"] == UNAVAILABLE
    assert built["git_commit_sha"] != "unknown"
    manifest_mod.resolve_git_commit_sha.cache_clear()


def test_validation_result_and_evidence_snapshot_include_manifest() -> None:
    adapter = FixtureMarketDataAdapter(FIXTURE)
    store = InMemoryValidationResultStore()
    service = ResearchValidationService(adapter, store)
    result = service.execute({"end_date": "2021-01-01"})
    manifest = result["reproducibility_manifest"]
    assert isinstance(manifest, dict)
    assert manifest["data_source"] == "fixture"
    assert manifest["symbol"] == "SPY"
    assert isinstance(manifest["protocol_hash"], str) and len(manifest["protocol_hash"]) == 64
    assert isinstance(manifest["data_hash"], str) and len(manifest["data_hash"]) == 64
    assert manifest["protocol_version"]
    assert manifest["engine_version"]
    assert manifest["runtime_version"].startswith("python/")
    assert manifest["git_commit_sha"]

    snapshot = build_evidence_snapshot(result, research_type="trend_following")
    assert snapshot["reproducibility_manifest"] == manifest
    assert snapshot["reproducibility_manifest"]["data_hash"] == manifest["data_hash"]


def test_same_protocol_inputs_same_manifest_hashes(sample_frame: pd.DataFrame) -> None:
    protocol = {"short_window": 20, "long_window": 60, "b": 1, "a": 2}
    left = build_reproducibility_manifest(
        data_source="fixture",
        symbol="SPY",
        requested_start_date="2020-01-01",
        requested_end_date="2020-01-31",
        protocol=protocol,
        frame=sample_frame,
        created_at="2026-07-26T00:00:00Z",
        git_commit_sha="deadbeef",
        runtime_version="python/3.12.0",
    )
    right = build_reproducibility_manifest(
        data_source="fixture",
        symbol="SPY",
        requested_start_date="2020-01-01",
        requested_end_date="2020-01-31",
        protocol={"a": 2, "long_window": 60, "short_window": 20, "b": 1},
        frame=sample_frame.sample(frac=1.0, random_state=3).reset_index(drop=True),
        created_at="2026-07-26T00:00:00Z",
        git_commit_sha="deadbeef",
        runtime_version="python/3.12.0",
    )
    assert left["protocol_hash"] == right["protocol_hash"]
    assert left["data_hash"] == right["data_hash"]
