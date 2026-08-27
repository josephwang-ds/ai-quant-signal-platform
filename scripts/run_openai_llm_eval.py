"""Run frozen grounded cases through a selected provider with checkpoints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from time import perf_counter

from company_lens.llm import (
    GroundedExplanationRequest,
    create_explanation_provider,
    evaluate_provider_run,
    load_grounded_cases,
)
from company_lens.llm.evidence import PROMPT_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("evidence/llm_eval/cases.json"))
    parser.add_argument(
        "--provider",
        choices=("openai", "deepseek", "qwen", "anthropic", "gemini"),
        default="openai",
    )
    parser.add_argument("--model")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input-cost-per-million", type=float)
    parser.add_argument("--output-cost-per-million", type=float)
    args = parser.parse_args()

    cases = load_grounded_cases(args.cases)
    if args.case_id:
        requested = set(args.case_id)
        cases = [case for case in cases if case["id"] in requested]
        missing = sorted(requested - {case["id"] for case in cases})
        if missing:
            parser.error(f"unknown case IDs: {', '.join(missing)}")
    if args.limit is not None:
        cases = cases[: args.limit]
    provider = create_explanation_provider(args.provider, model=args.model)
    if args.dry_run:
        print(
            f"LLM eval dry run: {len(cases)} cases, provider={provider.provider_name}, "
            f"model={provider.model}; "
            "no API request sent"
        )
        return 0

    safe_model = re.sub(r"[^a-zA-Z0-9._-]+", "_", provider.model)
    safe_prompt = re.sub(r"[^a-zA-Z0-9._-]+", "_", PROMPT_VERSION)
    out = args.out or Path(
        f"data/build/llm_eval/{provider.provider_name}_{safe_model}_{safe_prompt}.json"
    )
    run = _load_checkpoint(out, provider.provider_name, provider.model, PROMPT_VERSION)

    for index, case in enumerate(cases, start=1):
        previous = run["responses"].get(case["id"])
        if previous and not (args.retry_errors and "error" in previous):
            cost = _estimated_cost(previous.get("usage", {}), args)
            if cost is not None and "estimated_cost_usd" not in previous:
                previous["estimated_cost_usd"] = cost
                _write_json_atomic(out, run)
            print(f"[{index}/{len(cases)}] {case['id']}: cached")
            continue
        if not provider.api_key:
            parser.error(
                f"{provider.provider_name} API key is not configured and the requested "
                "run has uncached cases"
            )
        request = _request(case)
        started = perf_counter()
        try:
            output, usage = provider.generate_with_metadata(request)
            elapsed_ms = (perf_counter() - started) * 1_000
            record = {
                "output": output,
                "latency_ms": round(elapsed_ms, 1),
                "usage": usage,
            }
            cost = _estimated_cost(usage, args)
            if cost is not None:
                record["estimated_cost_usd"] = cost
            print(f"[{index}/{len(cases)}] {case['id']}: {elapsed_ms:.0f} ms")
        except Exception as error:  # noqa: BLE001 - preserve partial paid evaluation runs
            record = {
                "error": f"{type(error).__name__}: {error}",
                "latency_ms": round((perf_counter() - started) * 1_000, 1),
            }
            print(f"[{index}/{len(cases)}] {case['id']}: ERROR {type(error).__name__}")
        run["responses"][case["id"]] = record
        _write_json_atomic(out, run)

    scorecard = evaluate_provider_run(cases, run)
    scorecard_path = out.with_name(f"{out.stem}_scorecard.json")
    _write_json_atomic(scorecard_path, scorecard)
    cost = scorecard["operations"]["estimated_cost_usd"]
    cost_label = "not supplied" if cost is None else f"${cost:.4f}"
    print(
        f"scorecard: grounded={scorecard['metrics']['grounded_pass_rate']:.1%}, "
        f"coverage={scorecard['metrics']['material_concept_coverage']:.1%}, "
        f"cost={cost_label} -> {scorecard_path}"
    )
    return 0


def _request(case: dict) -> GroundedExplanationRequest:
    evidence = case["evidence"]
    return GroundedExplanationRequest(
        ticker=evidence["ticker"],
        accession=evidence["accession"],
        prompt_version=PROMPT_VERSION,
        language=case["language"],
        depth=case["depth"],
        evidence=evidence,
        allowed_citations=frozenset(case["allowed_citations"]),
        allowed_number_literals=frozenset(case["allowed_number_literals"]),
    )


def _load_checkpoint(path: Path, provider: str, model: str, prompt_version: str) -> dict:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("provider") != provider or payload.get("model") != model:
            raise ValueError("checkpoint provider/model does not match this run")
        if payload.get("prompt_version") != prompt_version:
            raise ValueError("checkpoint prompt version does not match this run")
        return payload
    return {
        "schema_version": "company-lens.llm-provider-run.v1",
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
        "responses": {},
    }


def _estimated_cost(usage: dict, args: argparse.Namespace) -> float | None:
    if args.input_cost_per_million is None or args.output_cost_per_million is None:
        return None
    if not isinstance(usage, dict):
        return None
    return round(
        int(usage.get("input_tokens", 0)) / 1_000_000 * args.input_cost_per_million
        + int(usage.get("output_tokens", 0)) / 1_000_000 * args.output_cost_per_million,
        8,
    )


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
