"""Offline tests for live verification helpers, scripts, and error paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.research_execution.live_verification import (
    LiveVerificationError,
    assert_no_fabricated_fallback,
    assert_provenance_contract,
    dumps_check_payload,
    validate_json_safe,
    validate_no_fabricated_fallback,
    validate_provenance_contract,
)
from app.research_execution.market_data_port import (
    MarketDataUnavailableError,
    MarketDataValidationError,
)
from app.research_execution.market_data_router import MarketDataRouter
from app.research_execution.price_cache import PriceCache


def _sample_provenance(**overrides) -> dict:
    base = {
        "provider": "yahoo",
        "adapter": "yahoo",
        "requested_symbol": "SPY",
        "canonical_symbol": "SPY",
        "provider_symbol": "SPY",
        "asset_class": "etf",
        "exchange": None,
        "currency": "USD",
        "adjustment": "auto_adjust",
        "interval": "1d",
        "actual_start": "2023-01-03",
        "actual_end": "2024-12-30",
        "row_count": 250,
        "cache_hit": False,
        "cache_stale": False,
    }
    base.update(overrides)
    return base


def test_validate_provenance_contract_ok() -> None:
    errors = validate_provenance_contract(
        _sample_provenance(),
        expected_provider="yahoo",
        expected_asset_class="etf",
        expected_canonical_symbol="SPY",
    )
    assert errors == []


def test_validate_provenance_contract_detects_missing_fields() -> None:
    errors = validate_provenance_contract({"provider": "yahoo"})
    assert any("missing field" in error for error in errors)


def test_validate_json_safe_rejects_nan() -> None:
    errors = validate_json_safe({"metric": float("nan")})
    assert errors


def test_assert_no_fabricated_fallback_rejects_fixture_warning() -> None:
    with pytest.raises(LiveVerificationError, match="fabricated"):
        assert_no_fabricated_fallback(
            ["Using deterministic local fixture — not live market data."]
        )


def test_router_rejects_malformed_symbol_offline() -> None:
    router = MarketDataRouter(cache=PriceCache(root=Path("/tmp/unused")))
    with pytest.raises(MarketDataValidationError):
        router.get_daily_ohlcv("!!!!", "2023-01-01", "2024-12-31")


def test_router_rejects_unsupported_bare_mainland_code_offline() -> None:
    router = MarketDataRouter(cache=PriceCache(root=Path("/tmp/unused2")))
    with pytest.raises(MarketDataValidationError):
        router.get_daily_ohlcv("600519", "2023-01-01", "2024-12-31")


def test_akshare_not_installed_maps_to_provider_not_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "akshare":
            raise ImportError("AKShare is not installed.")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    adapter_module = __import__(
        "app.research_execution.akshare_adapter",
        fromlist=["AkShareMarketDataAdapter"],
    )
    adapter = adapter_module.AkShareMarketDataAdapter(cache=PriceCache(root=tmp_path))
    with pytest.raises(MarketDataUnavailableError, match="not installed"):
        adapter.get_daily_ohlcv("600519.SH", "2023-01-01", "2024-12-31")


def test_stale_cache_warning_is_detected() -> None:
    errors = validate_no_fabricated_fallback(
        ["Serving labeled stale cache after live provider failure."]
    )
    assert errors == []


def test_dumps_check_payload_is_json_serializable() -> None:
    payload = dumps_check_payload(
        {
            "ok": True,
            "symbol": "SPY",
            "provider": "yahoo",
            "row_count": 10,
            "actual_start": "2023-01-03",
            "actual_end": "2024-12-30",
            "cache_hit": False,
            "cache_stale": False,
            "warnings": [],
        }
    )
    parsed = json.loads(payload)
    assert parsed["ok"] is True


def test_live_market_data_check_script_malformed_symbol_exit_code(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts import live_market_data_check as checker

    exit_code = checker.main(
        ["--symbol", "!!!!", "--cache-root", str(tmp_path)]
    )
    assert exit_code != 0


def test_verify_deployed_research_api_non_200(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import verify_deployed_research_api as verifier

    class FakeResponse:
        status_code = 502
        text = '{"detail":"provider unavailable"}'

        @staticmethod
        def json() -> dict:
            return {"detail": "provider unavailable"}

    monkeypatch.setattr(
        verifier.httpx,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )
    exit_code = verifier.main(
        [
            "--base-url",
            "https://example.test",
            "--symbol",
            "SPY",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2024-12-31",
        ]
    )
    assert exit_code != 0


def test_verify_deployed_research_api_success_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import verify_deployed_research_api as verifier

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {
                "research_id": "ma-crossover-spy",
                "provenance": _sample_provenance(),
                "metrics": {"observation_count": 200, "total_return": 0.1},
                "warnings": [],
                "supported_evidence": {"evaluation": "unavailable"},
            }

    monkeypatch.setattr(
        verifier.httpx,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )
    result = verifier.verify_execution(
        base_url="https://example.test",
        symbol="SPY",
        start_date="2023-01-01",
        end_date="2024-12-31",
        timeout_seconds=5.0,
    )
    assert result["ok"] is True
    assert result["provider"] == "yahoo"


def test_assert_provenance_contract_provider_mismatch() -> None:
    with pytest.raises(LiveVerificationError, match="provider"):
        assert_provenance_contract(
            _sample_provenance(provider="akshare"),
            expected_provider="yahoo",
        )
