"""Small reproducible evaluation for prior-filing sentence changes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from company_lens.contracts import FilingChange
from company_lens.filings import compare_filing_texts

KINDS = ("changed", "added", "removed")


def load_change_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, list):
        raise TypeError("change evaluation fixture must contain a JSON list")
    return payload


def evaluate_change_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure span-level change precision/recall with explicit text fragments."""
    totals = {kind: {"tp": 0, "fp": 0, "fn": 0} for kind in KINDS}
    case_results = []
    for case in cases:
        predictions, _ = compare_filing_texts(
            case["current_text"],
            case["prior_text"],
            current_accession=f"{case['id']}-current",
            prior_accession=f"{case['id']}-prior",
            current_source_url="https://www.sec.gov/current",
            prior_source_url="https://www.sec.gov/prior",
            limit_per_kind=20,
        )
        expected = case.get("expected", [])
        matched_predictions: set[int] = set()
        matched_expected: set[int] = set()
        for expected_index, label in enumerate(expected):
            for prediction_index, prediction in enumerate(predictions):
                if prediction_index in matched_predictions:
                    continue
                if _matches(prediction, label):
                    matched_predictions.add(prediction_index)
                    matched_expected.add(expected_index)
                    break
        for index, prediction in enumerate(predictions):
            key = "tp" if index in matched_predictions else "fp"
            totals[prediction.kind][key] += 1
        for index, label in enumerate(expected):
            if index not in matched_expected:
                totals[label["kind"]]["fn"] += 1
        case_results.append(
            {
                "id": case["id"],
                "expected": len(expected),
                "predicted": len(predictions),
                "matched": len(matched_expected),
            }
        )

    by_kind = {kind: _metrics(**totals[kind]) for kind in KINDS}
    overall_counts = {
        key: sum(totals[kind][key] for kind in KINDS) for key in ("tp", "fp", "fn")
    }
    return {
        "fixture_cases": len(cases),
        "overall": _metrics(**overall_counts),
        "by_kind": by_kind,
        "cases": case_results,
        "method": "deterministic sentence-span labels; no future filing context",
    }


def _matches(change: FilingChange, label: dict[str, str]) -> bool:
    if change.kind != label["kind"]:
        return False
    current = _normalize(change.current.text if change.current else "")
    prior = _normalize(change.prior.text if change.prior else "")
    expected_current = _normalize(label.get("current_contains", ""))
    expected_prior = _normalize(label.get("prior_contains", ""))
    return (not expected_current or expected_current in current) and (
        not expected_prior or expected_prior in prior
    )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _metrics(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
