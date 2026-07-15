"""Deterministic workspace context assembly — no LLM involvement."""

from __future__ import annotations

import json
import math
from typing import Any

from app.research_copilot.canonical_notebook import (
    CANONICAL_DEFINITION,
    NOTEBOOK_ENTRIES,
)
from app.research_copilot.citations import summarize_stage
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


def _find_stage(validation: dict[str, Any], stage_name: str) -> dict[str, Any] | None:
    for stage in validation.get("stages", []):
        if stage.get("stage") == stage_name:
            return _compact_stage(stage)
    return None


def _make_item(
    *,
    citation_id: str,
    source_type: str,
    source_id: str,
    label: str,
    content: str,
) -> ContextItem | None:
    if not content.strip():
        return None
    return ContextItem(
        citation_id=citation_id,
        source_type=source_type,
        source_id=source_id,
        label=label,
        content=content,
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

        execution_stages = [
            _compact_stage(stage)
            for stage in validation.get("stages", [])
            if stage.get("stage") in {"historical_backtest", "benchmark_comparison"}
        ]

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
                    "stages": execution_stages,
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

        context_items: list[ContextItem] = []
        run_id = str(validation_run_id)

        definition_item = _make_item(
            citation_id="research_definition:definition",
            source_type="research_definition",
            source_id=research_id,
            label="Research definition",
            content=json.dumps(structured["research_definition"], ensure_ascii=False),
        )
        if definition_item:
            context_items.append(definition_item)

        execution_item = _make_item(
            citation_id="execution:metrics",
            source_type="execution",
            source_id=run_id,
            label="Execution metrics",
            content=summarize_stage(
                {
                    "stages": execution_stages,
                    "provenance": provenance,
                }
            ),
        )
        if execution_item:
            context_items.append(execution_item)

        stage_specs = (
            ("validation:out_of_sample", "out_of_sample", "Out-of-sample evidence"),
            (
                "validation:parameter_sensitivity",
                "parameter_sensitivity",
                "Parameter sensitivity evidence",
            ),
            (
                "validation:transaction_cost_sensitivity",
                "transaction_cost_sensitivity",
                "Transaction-cost sensitivity evidence",
            ),
            ("validation:data_quality", "data_quality", "Data quality evidence"),
        )
        for citation_id, stage_name, label in stage_specs:
            stage_payload = _find_stage(validation, stage_name)
            item = _make_item(
                citation_id=citation_id,
                source_type="validation",
                source_id=run_id,
                label=label,
                content=summarize_stage(stage_payload),
            )
            if item:
                context_items.append(item)

        evaluation_status_item = _make_item(
            citation_id="evaluation:status",
            source_type="evaluation",
            source_id=run_id,
            label="Evaluation status",
            content=json.dumps(
                {
                    "evaluation_status": evaluation.get("evaluation_status"),
                    "evidence_coverage": evaluation.get("evidence_coverage"),
                    "completed_stages": evaluation.get("completed_stages", []),
                    "incomplete_stages": evaluation.get("incomplete_stages", []),
                    "blockers": evaluation.get("blockers", []),
                    "limitations": evaluation.get("limitations", []),
                },
                ensure_ascii=False,
            ),
        )
        if evaluation_status_item:
            context_items.append(evaluation_status_item)

        outstanding = evaluation.get("outstanding_evidence") or []
        outstanding_item = _make_item(
            citation_id="evaluation:outstanding_evidence",
            source_type="evaluation",
            source_id=run_id,
            label="Outstanding evidence",
            content=json.dumps(outstanding, ensure_ascii=False),
        )
        if outstanding and outstanding_item:
            context_items.append(outstanding_item)

        notebook_map = {
            "Hypothesis": "notebook:hypothesis",
            "Methodology": "notebook:methodology",
            "Observation": "notebook:observation",
        }
        for entry in NOTEBOOK_ENTRIES:
            citation_id = notebook_map.get(entry.get("entry_type", ""))
            if not citation_id:
                continue
            item = _make_item(
                citation_id=citation_id,
                source_type="notebook",
                source_id=entry.get("id", research_id),
                label=entry.get("title", "Notebook entry"),
                content=entry.get("body", ""),
            )
            if item:
                context_items.append(item)

        for chunk in self.retrieval.search(question):
            context_items.append(_chunk_to_context_item(chunk))

        return structured, context_items


def _chunk_to_context_item(chunk: DocumentChunk) -> ContextItem:
    return ContextItem(
        citation_id=chunk.citation_id,
        source_type=chunk.source_type,
        source_id=chunk.source_id,
        label=chunk.label,
        content=chunk.text,
    )
