"""Evaluate one provider's outputs on the frozen bilingual grounded cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_lens.llm.evaluation import (
    evaluate_provider_run,
    load_grounded_cases,
    load_provider_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=Path("evidence/llm_eval/cases.json")
    )
    parser.add_argument(
        "--responses",
        type=Path,
        default=Path("evidence/llm_eval/reference_responses.json"),
    )
    parser.add_argument("--out", type=Path, default=Path("data/build/llm_eval.json"))
    args = parser.parse_args()
    scorecard = evaluate_provider_run(
        load_grounded_cases(args.cases), load_provider_run(args.responses)
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scorecard, indent=2, ensure_ascii=False) + "\n")
    gate = "PASS" if scorecard["pilot_gate"]["passed"] else "FAIL"
    print(
        f"grounded LLM evaluation: {scorecard['fixture_cases']} cases, "
        f"grounded={scorecard['metrics']['grounded_pass_rate']:.1%}, "
        f"coverage={scorecard['metrics']['material_concept_coverage']:.1%}, "
        f"pilot gate={gate} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
