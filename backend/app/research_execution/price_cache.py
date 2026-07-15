"""Filesystem cache for research market-data responses (MVP — no Redis)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.research_execution.market_data_port import (
    DataProvenance,
    NormalizedMarketSeries,
    validate_normalized_ohlcv,
)

# Cache expiry: 24 hours. Documented for operators and Authenticity Policy.
CACHE_TTL_SECONDS = 24 * 60 * 60


class PriceCache:
    """
    Simple provider cache keyed by provider|symbol|start|end|interval.

    Stale entries may be returned on provider failure only when callers
    explicitly request and label them — never as silent fake data.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (
            Path(__file__).resolve().parents[2] / ".cache" / "market_data"
        )
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(
        provider: str,
        symbol: str,
        start: str,
        end: str | None,
        interval: str = "1d",
        adjustment: str = "auto",
    ) -> str:
        end_part = end or "latest"
        raw = (
            f"{provider}|{symbol.upper()}|{adjustment}|{start}|{end_part}|{interval}"
        )
        return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in raw)

    def _paths(self, key: str) -> tuple[Path, Path]:
        return self.root / f"{key}.csv", self.root / f"{key}.meta.json"

    def get(
        self,
        key: str,
        *,
        allow_stale: bool = False,
    ) -> tuple[NormalizedMarketSeries | None, bool]:
        """
        Return (series, is_stale).

        Fresh hits: is_stale=False.
        Stale hits only when allow_stale=True: is_stale=True.
        Miss / expired (and not allow_stale): (None, False).
        """
        csv_path, meta_path = self._paths(key)
        if not csv_path.exists() or not meta_path.exists():
            return None, False

        try:
            meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
            retrieved_at = meta.get("retrieved_at")
            if not retrieved_at:
                return None, False
            retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - retrieved).total_seconds()
            stale = age > CACHE_TTL_SECONDS
            if stale and not allow_stale:
                return None, False

            frame = pd.read_csv(csv_path)
            symbol = str(meta.get("symbol", "")).upper()
            frame = validate_normalized_ohlcv(frame, symbol=symbol)
            provenance = DataProvenance(
                provider=str(meta.get("provider", "unknown")),
                symbol=symbol,
                source=str(meta.get("source", meta.get("provider", "unknown"))),
                retrieved_at=retrieved_at,
                requested_start=str(meta.get("requested_start", "")),
                requested_end=meta.get("requested_end"),
                actual_start=str(meta.get("actual_start", "")),
                actual_end=str(meta.get("actual_end", "")),
                interval=str(meta.get("interval", "1d")),
                cache_hit=True,
                cache_stale=stale,
                currency=meta.get("currency"),
                adapter=str(meta.get("adapter", "")),
                requested_symbol=str(meta.get("requested_symbol", "")),
                canonical_symbol=str(meta.get("canonical_symbol", symbol)),
                provider_symbol=str(meta.get("provider_symbol", "")),
                asset_class=str(meta.get("asset_class", "")),
                exchange=meta.get("exchange"),
                adjustment=str(meta.get("adjustment", "auto")),
                row_count=int(meta.get("row_count", len(frame))),
            )
            return (
                NormalizedMarketSeries(
                    symbol=symbol,
                    frame=frame,
                    provenance=provenance,
                    warnings=list(meta.get("warnings", [])),
                ),
                stale,
            )
        except Exception:
            return None, False

    def put(self, key: str, series: NormalizedMarketSeries) -> None:
        csv_path, meta_path = self._paths(key)
        series.frame.to_csv(csv_path, index=False)
        meta = {
            **asdict(series.provenance),
            "warnings": series.warnings,
            "cache_ttl_seconds": CACHE_TTL_SECONDS,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
