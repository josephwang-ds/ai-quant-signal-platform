"""Inspect bounded document/headline retrieval without calling an LLM."""

from __future__ import annotations

import argparse
import json

from company_lens.llm import (
    LocalDocumentRetriever,
    RetrievalScope,
    import_document,
    import_headline_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--document", action="append", default=[])
    parser.add_argument("--headlines", action="append", default=[])
    parser.add_argument(
        "--source",
        action="append",
        choices=("uploaded", "company_news", "market_news"),
        default=[],
    )
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--published-after", default=None)
    parser.add_argument("--max-chunks", type=int, default=6)
    parser.add_argument("--min-relevance", type=float, default=0.08)
    args = parser.parse_args(argv)

    documents = [
        import_document(path, ticker=args.ticker, tags=args.tag) for path in args.document
    ]
    for path in args.headlines:
        documents.extend(import_headline_index(path))
    default_sources = []
    if args.document:
        default_sources.append("uploaded")
    if args.headlines:
        default_sources.extend(("company_news", "market_news"))
    scope = RetrievalScope(
        ticker=args.ticker,
        source_types=tuple(args.source or default_sources),
        tags=tuple(tag.casefold() for tag in args.tag),
        published_after=args.published_after,
        max_chunks=args.max_chunks,
        min_relevance=args.min_relevance,
    )
    results = LocalDocumentRetriever(documents).search(args.query, scope)
    print(
        json.dumps(
            {
                "query": args.query,
                "scope": scope.to_dict(),
                "documents_considered": len(documents),
                "chunks_selected": len(results),
                "results": [result.to_evidence() for result in results],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
