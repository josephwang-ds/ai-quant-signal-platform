"""Deterministic workspace context assembly — no LLM involvement."""

from __future__ import annotations

import json
import math
from typing import Any

from app.research_copilot.canonical_notebook import (
    CANONICAL_DEFINITION,
    NOTEBOOK_ENTRIES,
)
from app.research_copilot.llm_port import ContextItem
from app.research_copilot.retrieval import DocumentChunk, RetrievalIndex


def _sanitize(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _compact_stage(stage: dict[str, Any]) -> dict[str, Any]:
    evidence = stage.get("evidence")
    if isinstance(evidence, dict):
        compact_evidence = {
            key: value
            for key, value in evidence.items()
            if key not in {"series", "prices", "equity_curve", "daily_returns"}
        }
    else:
        compact_evidence = evidence
    return _sanitize(
        {
            "stage": stage.get("stage"),
            "label": stage.get("label"),
            "status": stage.get("status"),
            "summary": stage.get("summary"),
            "blockers": stage.get("blockers", []),
            "warnings": stage.get("warnings", []),
            "evidence": compact_evidence,
        }
    )


class ResearchContextAssembler:
    """Build bounded structured context from stored research artifacts."""

    def __init__(self, retrieval: RetrievalIndex | None = None) -> None:
        self.retrieval = retrieval or RetrievalIndex()

    def assemble(
        self,
        *,
        research_id: str,
        question: str,
        validation: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> tuple[dict[str, Any], list[ContextItem]]:
        validation_run_id = validation.get("validation_run_id", "")
        provenance = validation.get("provenance", {})

        structured = _sanitize(
            {
                "research_definition": {
                    **CANONICAL_DEFINITION,
                    "research_id": research_id,
                },
                "execution_evidence": {
                    "source": "validation_stages",
                    "provenance": provenance,
                    "historical_disclaimer": (
                        "Evidence is based on historical research data only; "
                        "it is not a forecast or investment recommendation."
                    ),
                    "stages": [
                        _compact_stage(stage)
                        for stage in validation.get("stages", [])
                        if stage.get("stage")
                        in {
                            "historical_backtest",
                            "benchmark_comparison",
                        }
                    ],
                },
                "validation_evidence": {
                    "validation_run_id": validation_run_id,
                    "generated_at": validation.get("generated_at"),
                    "stages": [
                        _compact_stage(stage)
                        for stage in validation.get("stages", [])
                    ],
                    "warnings": validation.get("warnings", []),
                },
                "evaluation_governance": {
                    "evaluation_status": evaluation.get("evaluation_status"),
                    "evidence_coverage": evaluation.get("evidence_coverage"),
                    "completed_stages": evaluation.get("completed_stages", []),
                    "incomplete_stages": evaluation.get("incomplete_stages", []),
                    "blockers": evaluation.get("blockers", []),
                    "limitations": evaluation.get("limitations", []),
                    "outstanding_evidence": evaluation.get(
                        "outstanding_evidence", []
                    ),
                    "generated_at": evaluation.get("generated_at"),
                },
                "notebook_context": NOTEBOOK_ENTRIES,
            }
        )

        doc_chunks = self.retrieval.search(question)
        context_items: list[ContextItem] = [
            ContextItem(
                source_type="research_definition",
                source_id=research_id,
                label="Research definition",
                content=json.dumps(structured["research_definition"], ensure_ascii=False),
            ),
            ContextItem(
                source_type="validation",
                source_id=str(validation_run_id),
                label="Validation evidence",
                content=json.dumps(structured["validation_evidence"], ensure_ascii=False),
            ),
            ContextItem(
                source_type="evaluation",
                source_id=str(validation_run_id),
                label="Evaluation governance",
                content=json.dumps(structured["evaluation_governance"], ensure_ascii=False),
            ),
            ContextItem(
                source_type="notebook",
                source_id=research_id,
                label="Structured notebook",
                content=json.dumps(structured["notebook_context"], ensure_ascii=False),
            ),
        ]
        for chunk in doc_chunks:
            context_items.append(_chunk_to_context_item(chunk))

        return structured, context_items


def _chunk_to_context_item(chunk: DocumentChunk) -> ContextItem:
    return ContextItem(
        source_type=chunk.source_type,
        source_id=chunk.source_id,
        label=chunk.label,
        content=chunk.text,
    )
