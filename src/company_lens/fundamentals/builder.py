"""Load, build, and persist fundamentals artifacts for company snapshots."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from company_lens.contracts import (
    DerivedMetricObservation,
    DerivedMetricSeries,
    FundamentalCitation,
    FundamentalObservation,
    FundamentalSeries,
    FundamentalsSection,
)
from company_lens.fundamentals.concepts import TEMPLATE_ID
from company_lens.fundamentals.metrics import FORMULA_VERSION, build_derived_metrics
from company_lens.fundamentals.normalize import normalize_annual_fundamentals

SCHEMA_VERSION = "company-lens.fundamentals.v1"
MIN_AVAILABLE_YEARS = 3


def fundamentals_path(root: str | Path, ticker: str) -> Path:
    return Path(root) / "fundamentals" / f"{ticker.lower()}.json"


def not_ingested_section(*, requested_years: int = 10) -> FundamentalsSection:
    return FundamentalsSection(
        schema_version=SCHEMA_VERSION,
        status="not_ingested",
        template=TEMPLATE_ID,
        requested_years=requested_years,
        knowledge_at=None,
        annual_periods=(),
        reported_series=(),
        derived_series=(),
        coverage={},
        warnings=("No local fundamentals artifact was found for this ticker.",),
        provenance={"source": "missing", "calculation": "company_lens.fundamentals.v1"},
        as_reported_series=(),
        series_basis="latest_restated",
    )


def build_fundamentals_section(
    company_facts: dict[str, Any],
    *,
    ticker: str,
    submissions: dict[str, Any] | None = None,
    requested_years: int = 10,
    fiscal_years: tuple[int, ...] | None = None,
) -> FundamentalsSection:
    """Normalize Company Facts and attach derived metrics."""
    normalized = normalize_annual_fundamentals(
        company_facts,
        ticker=ticker,
        submissions=submissions,
        requested_years=requested_years,
        fiscal_years=fiscal_years,
    )
    derived = build_derived_metrics(normalized.reported_series)
    year_count = len(normalized.annual_periods)
    status = (
        "insufficient_history"
        if year_count < MIN_AVAILABLE_YEARS
        else "available"
    )
    provenance = {
        **normalized.provenance,
        "generated_at": datetime.now(UTC).isoformat(),
        "formula_version": FORMULA_VERSION,
        "calculation": "company_lens.fundamentals.v1",
    }
    return FundamentalsSection(
        schema_version=SCHEMA_VERSION,
        status=status,
        template=normalized.template,
        requested_years=normalized.requested_years,
        knowledge_at=normalized.knowledge_at,
        annual_periods=normalized.annual_periods,
        reported_series=normalized.reported_series,
        derived_series=derived,
        coverage=normalized.coverage,
        warnings=normalized.warnings,
        provenance=provenance,
        as_reported_series=normalized.as_reported_series,
        series_basis="latest_restated",
    )


def save_fundamentals(section: FundamentalsSection, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.part")
    temporary.write_text(
        json.dumps(asdict(section), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def load_fundamentals(path: str | Path) -> FundamentalsSection:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return fundamentals_section_from_dict(payload)


def try_load_fundamentals(
    root: str | Path, ticker: str, *, requested_years: int = 10
) -> FundamentalsSection:
    path = fundamentals_path(root, ticker)
    if not path.exists():
        return not_ingested_section(requested_years=requested_years)
    return load_fundamentals(path)


def fundamentals_section_from_dict(payload: dict[str, Any]) -> FundamentalsSection:
    return FundamentalsSection(
        schema_version=str(payload.get("schema_version", SCHEMA_VERSION)),
        status=payload["status"],
        template=str(payload.get("template", TEMPLATE_ID)),
        requested_years=int(payload.get("requested_years", 10)),
        knowledge_at=payload.get("knowledge_at"),
        annual_periods=tuple(payload.get("annual_periods") or ()),
        reported_series=tuple(
            _series_from_dict(item) for item in payload.get("reported_series") or ()
        ),
        derived_series=tuple(
            _derived_series_from_dict(item)
            for item in payload.get("derived_series") or ()
        ),
        coverage=dict(payload.get("coverage") or {}),
        warnings=tuple(payload.get("warnings") or ()),
        provenance=dict(payload.get("provenance") or {}),
        as_reported_series=tuple(
            _series_from_dict(item) for item in payload.get("as_reported_series") or ()
        ),
        series_basis=str(payload.get("series_basis", "latest_restated")),
    )


def _series_from_dict(payload: dict[str, Any]) -> FundamentalSeries:
    return FundamentalSeries(
        metric_id=payload["metric_id"],
        label=payload["label"],
        definition=payload["definition"],
        expected_unit=payload["expected_unit"],
        observations=tuple(
            _observation_from_dict(item) for item in payload.get("observations") or ()
        ),
        concept_priority=tuple(payload.get("concept_priority") or ()),
        coverage_status=payload.get("coverage_status", "partial"),
    )


def _observation_from_dict(payload: dict[str, Any]) -> FundamentalObservation:
    citation_payload = payload["citation"]
    citation = FundamentalCitation(
        citation_id=citation_payload["citation_id"],
        taxonomy=citation_payload["taxonomy"],
        concept=citation_payload["concept"],
        accession=citation_payload["accession"],
        form=citation_payload["form"],
        source_url=citation_payload["source_url"],
        period_start=citation_payload.get("period_start"),
        period_end=citation_payload["period_end"],
        filed_date=citation_payload["filed_date"],
        accepted_at=citation_payload.get("accepted_at"),
        fiscal_year=int(citation_payload["fiscal_year"]),
        fiscal_period=citation_payload.get("fiscal_period", "FY"),
        unit=citation_payload["unit"],
        document_fy=(
            None
            if citation_payload.get("document_fy") is None
            else int(citation_payload["document_fy"])
        ),
        document_fp=citation_payload.get("document_fp"),
    )
    return FundamentalObservation(
        metric_id=payload["metric_id"],
        value=float(payload["value"]),
        unit=payload["unit"],
        period_start=payload.get("period_start"),
        period_end=payload["period_end"],
        fiscal_year=int(payload["fiscal_year"]),
        knowledge_at=payload["knowledge_at"],
        citation=citation,
        quality_flags=tuple(payload.get("quality_flags") or ()),
    )


def _derived_series_from_dict(payload: dict[str, Any]) -> DerivedMetricSeries:
    return DerivedMetricSeries(
        metric_id=payload["metric_id"],
        label=payload["label"],
        definition=payload["definition"],
        unit=payload["unit"],
        observations=tuple(
            DerivedMetricObservation(
                metric_id=item["metric_id"],
                value=None if item.get("value") is None else float(item["value"]),
                unit=item["unit"],
                period_end=item["period_end"],
                fiscal_year=int(item["fiscal_year"]),
                status=item["status"],
                formula_version=item.get("formula_version", FORMULA_VERSION),
                components=dict(item.get("components") or {}),
                quality_flags=tuple(item.get("quality_flags") or ()),
            )
            for item in payload.get("observations") or ()
        ),
    )
