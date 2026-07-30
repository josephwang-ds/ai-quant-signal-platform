#!/usr/bin/env python3
"""Seed / publish an operator Portfolio from a DRAFT manifest JSON file.

Uses the Phase 5.1C publication application service and Phase 5.1B repository.
Never bypasses ports. Never used as an automatic frontend fallback.

Usage (from ``backend/``):

    source .venv/bin/activate
    python scripts/seed_published_demo_portfolio.py --manifest path.json --dry-run
    python scripts/seed_published_demo_portfolio.py --manifest path.json
    python scripts/seed_published_demo_portfolio.py --manifest path.json --registry-root /tmp/portfolios
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.intelligence.storage import IntelligenceStorage
from app.intelligence_serving.deps import build_intelligence_service
from app.portfolio.publication import (
    PortfolioPublicationCommand,
    PortfolioPublicationResult,
    PortfolioPublicationService,
    PortfolioPublicationStatus,
)
from app.portfolio.repository import FilesystemPortfolioRepository
from app.portfolio.research_adapter import as_published_research_query_port
from app.portfolio.schemas import PortfolioManifest, manifest_from_dict
from app.portfolio.storage import PortfolioStorage


def _result_payload(result: PortfolioPublicationResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "dry_run": result.dry_run,
        "portfolio_id": result.portfolio_id,
        "portfolio_version": result.portfolio_version,
        "status": result.status.value,
        "idempotent": result.idempotent,
        "published_at": (
            result.published_at.isoformat() if result.published_at is not None else None
        ),
        "integrity_verified": result.integrity_verified,
        "resolved_member_count": len(result.resolved_members),
        "issues": [
            {
                "code": issue.code.value,
                "message": issue.message,
                "field": issue.field,
                "context": issue.context,
            }
            for issue in result.issues
        ],
    }


def publish_portfolio_from_manifest(
    *,
    manifest: PortfolioManifest,
    dry_run: bool,
    registry_root: Optional[Path] = None,
    intelligence_root: Optional[Path] = None,
) -> PortfolioPublicationResult:
    portfolio_storage = (
        PortfolioStorage(root=registry_root)
        if registry_root is not None
        else PortfolioStorage()
    )
    intelligence_storage = (
        IntelligenceStorage(root=intelligence_root)
        if intelligence_root is not None
        else IntelligenceStorage()
    )
    research = as_published_research_query_port(
        build_intelligence_service(intelligence_storage)
    )
    repository = FilesystemPortfolioRepository(storage=portfolio_storage)
    service = PortfolioPublicationService(repository, research)
    return service.publish(
        PortfolioPublicationCommand(manifest=manifest, dry_run=dry_run)
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish an operator DRAFT Portfolio manifest through Phase 5.1C."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to a DRAFT PortfolioManifest JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and resolve sources without writing the portfolio registry",
    )
    parser.add_argument(
        "--registry-root",
        default=None,
        help="Optional Portfolio registry root (defaults to PORTFOLIO_OUTPUT_DIR)",
    )
    parser.add_argument(
        "--intelligence-root",
        default=None,
        help="Optional Intelligence registry root (defaults to INTELLIGENCE_OUTPUT_DIR)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured result as JSON (default behaviour)",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest).expanduser()
    if not manifest_path.is_file():
        print(
            json.dumps(
                {
                    "ok": False,
                    "status": PortfolioPublicationStatus.REJECTED.value,
                    "issues": [
                        {
                            "code": "PORTFOLIO_DOMAIN_INVALID",
                            "message": f"manifest file not found: {manifest_path}",
                        }
                    ],
                },
                indent=2,
            )
        )
        return 1

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = manifest_from_dict(payload)
    except Exception as exc:  # noqa: BLE001 — operator CLI surface
        print(
            json.dumps(
                {
                    "ok": False,
                    "status": PortfolioPublicationStatus.REJECTED.value,
                    "issues": [
                        {
                            "code": "PORTFOLIO_DOMAIN_INVALID",
                            "message": f"unable to parse portfolio manifest: {exc}",
                        }
                    ],
                },
                indent=2,
            )
        )
        return 1

    result = publish_portfolio_from_manifest(
        manifest=manifest,
        dry_run=bool(args.dry_run),
        registry_root=Path(args.registry_root) if args.registry_root else None,
        intelligence_root=(
            Path(args.intelligence_root) if args.intelligence_root else None
        ),
    )
    print(json.dumps(_result_payload(result), indent=2, sort_keys=True))
    if result.status is PortfolioPublicationStatus.ALREADY_PUBLISHED:
        return 0
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
