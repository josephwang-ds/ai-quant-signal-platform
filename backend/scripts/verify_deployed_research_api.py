#!/usr/bin/env python3
"""Verify deployed research execution API with live provider routing."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any
from urllib.parse import urljoin

import httpx

from app.research_execution.live_verification import (
    LiveVerificationError,
    assert_json_safe,
    assert_no_fabricated_fallback,
    assert_provenance_contract,
    dumps_check_payload,
    execution_to_check_payload,
)
from app.research_execution.symbol import classify_symbol


def _normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        raise LiveVerificationError(
            "base-url must be an absolute http(s) URL",
            category="invalid_request",
        )
    if "127.0.0.1" in value or "localhost" in value:
        raise LiveVerificationError(
            "deployed verification requires a non-localhost base URL",
            category="invalid_request",
        )
    return value


def verify_execution(
    *,
    base_url: str,
    symbol: str,
    start_date: str,
    end_date: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    descriptor = classify_symbol(symbol)
    endpoint = urljoin(f"{_normalize_base_url(base_url)}/", "api/v1/research/execution")
    body = {
        "research_id": "ma-crossover-spy",
        "symbol": symbol,
        "benchmark": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "short_window": 20,
        "long_window": 60,
        "transaction_cost": 0.001,
        "risk_free_rate": 0.0,
    }

    try:
        response = httpx.post(endpoint, json=body, timeout=timeout_seconds)
    except httpx.TimeoutException as exc:
        raise LiveVerificationError("request timed out", category="timeout") from exc
    except httpx.RequestError as exc:
        raise LiveVerificationError(
            f"backend unavailable: {exc}",
            category="backend_unavailable",
        ) from exc

    if response.status_code != 200:
        detail = response.text[:300]
        category = "provider_unavailable" if response.status_code == 502 else "backend_error"
        if response.status_code in {400, 422}:
            category = "invalid_request"
        raise LiveVerificationError(
            f"HTTP {response.status_code}: {detail}",
            category=category,
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise LiveVerificationError(
            "response was not valid JSON",
            category="invalid_response",
        ) from exc

    assert_json_safe(payload)
    assert_provenance_contract(
        payload["provenance"],
        expected_provider=descriptor.preferred_provider,
        expected_asset_class=descriptor.asset_class,
        expected_canonical_symbol=descriptor.canonical_symbol,
        expected_exchange=descriptor.exchange,
        expected_adjustment="qfq" if descriptor.preferred_provider == "akshare" else None,
    )
    assert_no_fabricated_fallback(payload.get("warnings", []))

    metrics = payload.get("metrics", {})
    if not metrics.get("observation_count"):
        raise LiveVerificationError(
            "execution returned no observations",
            category="insufficient_history",
        )

    return execution_to_check_payload(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify deployed research execution API")
    parser.add_argument("--base-url", required=True, help="Deployed backend origin")
    parser.add_argument("--symbol", required=True, help="Canonical symbol")
    parser.add_argument("--start-date", required=True, help="Inclusive start date")
    parser.add_argument("--end-date", default=None, help="Inclusive end date")
    parser.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout seconds")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print stack traces on failure (local diagnostics only)",
    )
    args = parser.parse_args(argv)

    try:
        payload = verify_execution(
            base_url=args.base_url,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            timeout_seconds=args.timeout,
        )
        print(dumps_check_payload(payload))
        return 0
    except Exception as exc:  # noqa: BLE001 — script boundary
        category = getattr(exc, "category", "unknown")
        message = getattr(exc, "message", str(exc))
        print(
            json.dumps(
                {
                    "ok": False,
                    "symbol": args.symbol,
                    "provider": None,
                    "error_category": category,
                    "message": message,
                },
                indent=2,
                sort_keys=True,
            )
        )
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
