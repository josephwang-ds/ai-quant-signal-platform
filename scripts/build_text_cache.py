"""Encode the filing corpus once, so nothing downstream ever loads a model.

Runtime is dominated by the transformer and the corpus is fixed, so this is a
build step rather than part of any pipeline run. Rerunning it over an unchanged
corpus touches no model at all: every document already in the cache is skipped,
and the model is only constructed when there is work.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from filing_triage.text_model import (
    TextCache,
    available,
    encode,
    encoded_from_heading,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path,
                        default=Path("data/build/events.parquet"))
    parser.add_argument("--cache", type=Path,
                        default=Path("data/build/text_cache"))
    parser.add_argument("--limit", type=int, default=None,
                        help="encode only the first N filings, for a smoke test")
    args = parser.parse_args()

    if not available():
        raise SystemExit(
            "transformers and torch are not installed. This is an optional "
            "feature group: `pip install -e '.[nlp]'`. Everything else in the "
            "project works without it."
        )

    events = pd.read_parquet(args.events)
    if args.limit:
        events = events.head(args.limit)
    texts = events["text"].fillna("").astype(str).tolist()

    parsed = encoded_from_heading(texts)
    print(f"{len(texts):,} filings · {parsed:.1%} have a findable item heading")
    if parsed < 0.5:
        print("  WARNING: most filings fell back to raw text, which begins with "
              "XBRL and SEC boilerplate. Check the heading pattern before "
              "trusting these features.")

    cache = TextCache(args.cache)
    started = time.time()
    encode(texts, cache, progress=True)
    print(f"cache: {cache.fingerprint()}")
    print(f"elapsed {time.time() - started:.0f}s -> {args.cache}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
