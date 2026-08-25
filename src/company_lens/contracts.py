"""Stable read-model contracts shared by the CLI and a future web UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Citation:
    anchor: str
    accession: str
    source_url: str
    text: str


@dataclass(frozen=True)
class FilingChange:
    kind: str
    current: Citation | None
    prior: Citation | None
    similarity: float | None = None


@dataclass(frozen=True)
class FilingComparison:
    comparable_key: str
    prior_accession: str
    prior_accepted_at: str
    prior_source_url: str
    changes: list[FilingChange]
    counts: dict[str, int]


@dataclass(frozen=True)
class FilingEntity:
    text: str
    kind: str
    normalized_value: str
    unit: str
    citation: str
    source_start: int
    source_end: int


@dataclass(frozen=True)
class FilingReaction:
    session: str
    asset_open_to_close: float
    benchmark_open_to_close: float
    benchmark_adjusted_move: float
    magnitude_percentile: float | None
    prior_sample_size: int


@dataclass(frozen=True)
class FilingBrief:
    accession: str
    form: str
    accepted_at: str
    items: list[dict[str, str]]
    source_url: str
    novelty: float | None
    key_numbers: list[dict[str, str]] = field(default_factory=list)
    entities: list[FilingEntity] = field(default_factory=list)
    passages: list[Citation] = field(default_factory=list)
    comparison: FilingComparison | None = None
    reaction: FilingReaction | None = None


@dataclass(frozen=True)
class FilingTimelinePoint:
    accession: str
    accepted_at: str
    item_code: str
    item_label: str
    source_url: str
    reaction: FilingReaction | None = None


@dataclass(frozen=True)
class EvidenceScopeSummary:
    status: Literal["available", "empty", "stale", "not_configured"]
    source_types: list[str]
    query: str | None
    max_chunks: int
    selected_chunks: int
    published_after: str | None
    generated_at: str | None


@dataclass(frozen=True)
class HeadlineBrief:
    headline: str
    publisher: str
    published_at: str
    fetched_at: str | None
    url: str
    source_type: Literal["company_news", "market_news"]
    ticker: str | None
    topic: str | None
    citation: str


@dataclass(frozen=True)
class CompanySnapshot:
    schema_version: str
    ticker: str
    company_name: str
    as_of: str
    benchmark: str
    period: dict[str, str]
    profile: dict[str, Any]
    market: dict[str, Any]
    performance: dict[str, Any]
    growth: list[dict[str, Any]]
    period_options: dict[str, dict[str, Any]]
    latest_filings: list[FilingBrief]
    explanation: dict[str, Any]
    provenance: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    filing_timeline: list[FilingTimelinePoint] = field(default_factory=list)
    evidence_scope: EvidenceScopeSummary | None = None
    headlines: list[HeadlineBrief] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.evidence_scope is None:
            payload.pop("evidence_scope")
            payload.pop("headlines")
        return payload
