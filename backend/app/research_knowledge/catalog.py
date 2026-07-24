"""Catalog metadata for Research Rulebook documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ResearchTypeFilter = Literal["all", "trend_following", "factor"]


@dataclass(frozen=True)
class KnowledgeDocument:
    knowledge_id: str
    title: str
    topic: str
    research_type: ResearchTypeFilter
    version: str
    status: Literal["active", "deprecated"]
    source_path: str
    tags: tuple[str, ...]


DOCUMENTS_DIR = Path(__file__).resolve().parent / "documents"

RULEBOOK_CATALOG: tuple[KnowledgeDocument, ...] = (
    KnowledgeDocument(
        knowledge_id="kb.research_protocol.v1",
        title="Research Protocol",
        topic="protocol",
        research_type="all",
        version="v1",
        status="active",
        source_path="research_protocol.md",
        tags=("protocol", "hypothesis", "criteria", "definition"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.trend_following.v1",
        title="Trend Following Methodology",
        topic="methodology",
        research_type="trend_following",
        version="v1",
        status="active",
        source_path="trend_following_methodology.md",
        tags=("trend", "ma", "oos", "buy-and-hold", "lag"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.factor_validation.v1",
        title="Factor Validation",
        topic="methodology",
        research_type="factor",
        version="v1",
        status="active",
        source_path="factor_validation.md",
        tags=("factor", "rankic", "quantile", "icir", "momentum"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.benchmark_definitions.v1",
        title="Benchmark Definitions",
        topic="benchmark",
        research_type="all",
        version="v1",
        status="active",
        source_path="benchmark_definitions.md",
        tags=("benchmark", "buy-and-hold", "equal-weight"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.rank_ic_interpretation.v1",
        title="RankIC Interpretation",
        topic="factor_ic",
        research_type="factor",
        version="v1",
        status="active",
        source_path="rank_ic_interpretation.md",
        tags=("rankic", "icir", "stability", "factor"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.transaction_costs.v1",
        title="Transaction Costs",
        topic="costs",
        research_type="all",
        version="v1",
        status="active",
        source_path="transaction_costs.md",
        tags=("cost", "turnover", "sensitivity"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.robustness_review.v1",
        title="Robustness Review",
        topic="robustness",
        research_type="all",
        version="v1",
        status="active",
        source_path="robustness_review.md",
        tags=("robustness", "oos", "sensitivity", "data-quality"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.decision_rules.v1",
        title="Decision Rules",
        topic="decision",
        research_type="all",
        version="v1",
        status="active",
        source_path="decision_rules.md",
        tags=("decision", "promote", "hold", "reject", "archive"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.feature_interpretation.v1",
        title="Feature Interpretation",
        topic="features",
        research_type="trend_following",
        version="v1",
        status="active",
        source_path="feature_interpretation.md",
        tags=("feature", "importance", "causality"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.known_limitations.v1",
        title="Known Limitations",
        topic="limitations",
        research_type="all",
        version="v1",
        status="active",
        source_path="known_limitations.md",
        tags=("limitations", "safety", "injection"),
    ),
    KnowledgeDocument(
        knowledge_id="kb.glossary.v1",
        title="Glossary",
        topic="glossary",
        research_type="all",
        version="v1",
        status="active",
        source_path="glossary.md",
        tags=("glossary", "definitions"),
    ),
    # Kept for exclusion tests — never retrieved when status=deprecated
    KnowledgeDocument(
        knowledge_id="kb.deprecated_example.v0",
        title="Deprecated Example",
        topic="deprecated",
        research_type="all",
        version="v0",
        status="deprecated",
        source_path="glossary.md",
        tags=("deprecated",),
    ),
)


def active_catalog() -> list[KnowledgeDocument]:
    return [doc for doc in RULEBOOK_CATALOG if doc.status == "active"]
