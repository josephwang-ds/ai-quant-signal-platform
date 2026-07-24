"""Deterministic workspace context assembly — no LLM involvement."""

from __future__ import annotations

import json
import math
from typing import Any

from app.research_copilot.canonical_notebook import (
    CANONICAL_DEFINITION,
    CANONICAL_RESEARCH_ID,
    NOTEBOOK_ENTRIES,
)
from app.research_copilot.citations import summarize_stage
from app.research_copilot.factor_summary import (
    build_factor_summary,
    is_factor_validation_evidence,
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
        evaluation: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[ContextItem]]:
        if is_factor_validation_evidence(validation):
            return self._assemble_factor(
                research_id=research_id,
                question=question,
                validation=validation,
            )

        evaluation = evaluation or {}
        validation_run_id = validation.get("validation_run_id", "")
        provenance = validation.get("provenance", {})
        strategy = validation.get("strategy", {})
        is_canonical = research_id == CANONICAL_RESEARCH_ID
        research_definition = (
            {**CANONICAL_DEFINITION, "research_id": research_id}
            if is_canonical
            else {
                "research_id": research_id,
                "template": "ma_crossover",
                "symbol": strategy.get("symbol"),
                "benchmark": strategy.get("benchmark_label")
                or strategy.get("benchmark"),
                "short_window": strategy.get("short_window"),
                "long_window": strategy.get("long_window"),
                "transaction_cost": strategy.get("transaction_cost"),
                "scope": (
                    "Local research definition. Interpret only the stored "
                    "validation evidence for this run."
                ),
            }
        )
        execution_stages = [
            _compact_stage(stage)
            for stage in validation.get("stages", [])
            if stage.get("stage") in {"historical_backtest", "benchmark_comparison"}
        ]

        structured = _sanitize(
            {
                "research_definition": research_definition,
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
                "notebook_context": NOTEBOOK_ENTRIES if is_canonical else [],
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
        for entry in NOTEBOOK_ENTRIES if is_canonical else []:
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

    def _assemble_factor(
        self,
        *,
        research_id: str,
        question: str,
        validation: dict[str, Any],
    ) -> tuple[dict[str, Any], list[ContextItem]]:
        """Assemble Factor Validation evidence only — no MA stage fabrication."""
        validation_run_id = validation.get("validation_run_id", "")
        factor_summary = build_factor_summary(validation)
        research_definition = {
            "research_id": research_id,
            "template": "cross_sectional_factor",
            "universe_id": validation.get("universe_id"),
            "factor_id": validation.get("factor_id"),
            "rebalance_frequency": validation.get("rebalance_frequency"),
            "holding_period_months": validation.get("holding_period_months"),
            "scope": (
                "Factor validation evidence only. Summarize RankIC, ICIR, "
                "turnover, long–short return, stability, and warnings from "
                "the stored run — never invent metrics."
            ),
        }
        ic_summary = (validation.get("ic") or {}).get("summary") or {}
        quantiles = validation.get("quantiles") or {}
        long_short = validation.get("long_short") or {}
        benchmark = validation.get("benchmark") or {}

        structured = _sanitize(
            {
                "research_definition": research_definition,
                "factor_summary": factor_summary,
                "factor_validation_evidence": {
                    "validation_run_id": validation_run_id,
                    "generated_at": validation.get("generated_at"),
                    "evidence_kind": validation.get("evidence_kind"),
                    "validation_status": validation.get("validation_status"),
                    "ic_summary": ic_summary,
                    "turnover": quantiles.get("turnover"),
                    "transaction_cost": quantiles.get("transaction_cost"),
                    "long_short": {
                        "cumulative_final": long_short.get("cumulative_final"),
                        "cumulative_final_net_of_cost": long_short.get(
                            "cumulative_final_net_of_cost"
                        ),
                        "note": long_short.get("note"),
                    },
                    "benchmark": {
                        "rationale": benchmark.get("rationale"),
                        "decision": benchmark.get("decision"),
                        "checks": [
                            {
                                "id": check.get("check_id")
                                or check.get("id")
                                or check.get("name"),
                                "status": check.get("status"),
                                "summary": check.get("explanation")
                                or check.get("summary")
                                or check.get("rationale")
                                or check.get("detail"),
                            }
                            for check in (benchmark.get("checks") or [])
                            if isinstance(check, dict)
                        ],
                    },
                    "warnings": validation.get("warnings", []),
                    "provenance": validation.get("provenance", {}),
                    "historical_disclaimer": (
                        "Evidence is based on historical factor-validation "
                        "data only; it is not a forecast or investment recommendation."
                    ),
                },
            }
        )

        context_items: list[ContextItem] = []
        run_id = str(validation_run_id)

        definition_item = _make_item(
            citation_id="research_definition:definition",
            source_type="research_definition",
            source_id=research_id,
            label="Factor research definition",
            content=json.dumps(structured["research_definition"], ensure_ascii=False),
        )
        if definition_item:
            context_items.append(definition_item)

        factor_specs = (
            (
                "factor:rank_ic",
                "RankIC summary",
                {"rank_ic": factor_summary["rank_ic"], "ic_summary": ic_summary},
            ),
            (
                "factor:icir",
                "ICIR",
                {"icir": factor_summary["icir"], "ic_summary": ic_summary},
            ),
            (
                "factor:turnover",
                "Turnover",
                {
                    "turnover": factor_summary["turnover"],
                    "turnover_evidence": quantiles.get("turnover"),
                },
            ),
            (
                "factor:long_short",
                "Long–short return",
                {
                    "long_short_return": factor_summary["long_short_return"],
                    "long_short": structured["factor_validation_evidence"]["long_short"],
                },
            ),
            (
                "factor:stability",
                "Stability",
                {
                    "stability": factor_summary["stability"],
                    "benchmark": structured["factor_validation_evidence"]["benchmark"],
                },
            ),
            (
                "factor:warnings",
                "Factor validation warnings",
                {"warnings": factor_summary["warnings"]},
            ),
        )
        for citation_id, label, payload in factor_specs:
            item = _make_item(
                citation_id=citation_id,
                source_type="factor_validation",
                source_id=run_id,
                label=label,
                content=json.dumps(payload, ensure_ascii=False),
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
