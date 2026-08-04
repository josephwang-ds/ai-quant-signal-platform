"""Canonical Portfolio manifest serialization for checksums (Phase 5.1B).

Analytical weights serialize as decimal strings (for example ``\"0.25\"``),
matching Pydantic ``model_dump(mode=\"json\")`` Decimal handling. Members are
ordered by ``member_order`` before canonical JSON encoding so checksums are
stable regardless of list insertion order.
"""

from __future__ import annotations

import json
from typing import Any

from app.portfolio.errors import PortfolioInvalidStoredManifestError
from app.portfolio.schemas import PortfolioManifest, manifest_from_dict


def canonical_manifest_payload(manifest: PortfolioManifest) -> dict[str, Any]:
    payload = manifest.model_dump(mode="json")
    members = list(payload.get("members") or [])
    payload["members"] = sorted(members, key=lambda item: item["member_order"])
    return payload


def serialize_portfolio_manifest(manifest: PortfolioManifest) -> bytes:
    """Return deterministic UTF-8 JSON bytes used for SHA-256 integrity."""
    payload = canonical_manifest_payload(manifest)
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def parse_portfolio_manifest_bytes(raw: bytes) -> PortfolioManifest:
    try:
        text = raw.decode("utf-8")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PortfolioInvalidStoredManifestError(
            "stored portfolio manifest is not valid UTF-8 JSON",
            path_category="manifest",
        ) from exc
    if not isinstance(payload, dict):
        raise PortfolioInvalidStoredManifestError(
            "stored portfolio manifest must be a JSON object",
            path_category="manifest",
        )
    try:
        return manifest_from_dict(payload)
    except Exception as exc:  # pydantic ValidationError and ValueError
        raise PortfolioInvalidStoredManifestError(
            "stored portfolio manifest failed contract validation",
            path_category="manifest",
        ) from exc
