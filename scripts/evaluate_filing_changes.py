"""Evaluate deterministic prior-filing change detection on labeled spans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_lens.nlp import evaluate_change_cases, load_change_cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=Path("evidence/nlp_eval/change_cases.json")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("evidence/nlp_eval/metrics.json")
    )
    args = parser.parse_args()
    metrics = evaluate_change_cases(load_change_cases(args.cases))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, indent=2) + "\n")
    print(
        f"change evaluation: {metrics['fixture_cases']} cases, "
        f"F1={metrics['overall']['f1']:.3f} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
