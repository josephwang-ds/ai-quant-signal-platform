"""Build a Company Lens snapshot from the existing local data artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from company_lens import build_snapshot
from company_lens.contracts import EvidenceScopeSummary
from company_lens.llm import (
    JsonExplanationCache,
    LocalDocumentRetriever,
    RetrievalScope,
    build_grounded_request,
    create_explanation_provider,
    extend_request_with_retrieval,
    generate_with_fallback,
    import_document,
    import_headline_index,
    persist_llm_provenance,
    persist_retrieval,
)
from company_lens.storage import LocalJsonStorage
from company_lens.universe import UnsupportedCompanyError
from company_lens.web import render_company_page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="company-lens", description="Source-backed company intelligence snapshot"
    )
    parser.add_argument("ticker", help="US ticker present in the local data, e.g. AAPL")
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--initial", type=float, default=10_000)
    parser.add_argument("--data-dir", default="data/build")
    parser.add_argument("--out", default=None, help="JSON output path")
    parser.add_argument("--html-out", default=None, help="self-contained HTML output path")
    parser.add_argument(
        "--headline-index",
        default=None,
        metavar="PATH",
        help="optional cached JSON/CSV headline index displayed on the company page",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="try a grounded provider brief; validate and fall back safely on failure",
    )
    parser.add_argument(
        "--llm-provider",
        choices=("openai", "deepseek", "qwen", "anthropic", "gemini"),
        default=None,
        help="provider override; otherwise COMPANY_LENS_LLM_PROVIDER or openai",
    )
    parser.add_argument("--llm-model", default=None, help="optional provider model override")
    parser.add_argument("--llm-language", default="English")
    parser.add_argument("--llm-depth", choices=("beginner", "professional"), default="beginner")
    parser.add_argument("--llm-cache", default="data/build/llm_cache")
    parser.add_argument(
        "--storage-dir",
        default="data/build/company_lens_storage",
        help="local JSON persistence root for retrieval and LLM provenance",
    )
    parser.add_argument(
        "--llm-document",
        action="append",
        default=[],
        metavar="PATH",
        help="local txt/md/html/json/csv evidence document; repeatable",
    )
    parser.add_argument(
        "--llm-headlines",
        action="append",
        default=[],
        metavar="PATH",
        help="JSON/CSV headline index with publisher, date, URL, and optional ticker",
    )
    parser.add_argument(
        "--llm-search-query",
        default=None,
        help="bounded query applied only to imported documents/headlines",
    )
    parser.add_argument(
        "--llm-search-source",
        action="append",
        choices=("uploaded", "company_news", "market_news"),
        default=[],
        help="allowed retrieval source; repeatable",
    )
    parser.add_argument(
        "--llm-search-tag",
        action="append",
        default=[],
        help="required lowercase metadata tag; repeatable",
    )
    parser.add_argument("--llm-news-after", default=None, help="ISO date/time freshness floor")
    parser.add_argument("--llm-max-chunks", type=int, default=6)
    parser.add_argument("--llm-min-relevance", type=float, default=0.08)
    parser.add_argument(
        "--llm-rule",
        action="append",
        default=[],
        help="safe reader emphasis/style rule; repeatable",
    )
    args = parser.parse_args(argv)
    retrieval_controls = (
        args.llm_document
        or args.llm_headlines
        or args.llm_search_query
        or args.llm_search_source
        or args.llm_search_tag
        or args.llm_news_after
        or args.llm_rule
    )
    if retrieval_controls and not args.llm:
        parser.error("LLM retrieval and reader controls require --llm")
    if (
        args.llm
        and (args.llm_search_query or args.llm_search_source or args.llm_news_after)
        and not (args.llm_document or args.llm_headlines)
    ):
        parser.error("LLM search controls require --llm-document or --llm-headlines")

    try:
        snapshot = build_snapshot(
            args.ticker,
            data_dir=args.data_dir,
            benchmark=args.benchmark,
            years=args.years,
            initial_investment=args.initial,
            headline_index=args.headline_index,
        )
    except UnsupportedCompanyError as error:
        parser.error(str(error))
    llm_result = None
    if args.llm and snapshot.latest_filings:
        storage = LocalJsonStorage(args.storage_dir)
        provider = create_explanation_provider(
            args.llm_provider,
            model=args.llm_model,
        )
        request = build_grounded_request(
            snapshot.ticker,
            snapshot.performance,
            snapshot.latest_filings,
            language=args.llm_language,
            depth=args.llm_depth,
        )
        retrieval_provenance = None
        if args.llm_document or args.llm_headlines or args.llm_rule:
            documents = [
                import_document(path, ticker=snapshot.ticker, tags=args.llm_search_tag)
                for path in args.llm_document
            ]
            for path in args.llm_headlines:
                documents.extend(import_headline_index(path))
            default_sources = []
            if args.llm_document:
                default_sources.append("uploaded")
            if args.llm_headlines:
                default_sources.extend(("company_news", "market_news"))
            scope = RetrievalScope(
                ticker=snapshot.ticker,
                source_types=tuple(args.llm_search_source or default_sources),
                tags=tuple(tag.casefold() for tag in args.llm_search_tag),
                published_after=args.llm_news_after,
                max_chunks=args.llm_max_chunks,
                min_relevance=args.llm_min_relevance,
            )
            query = args.llm_search_query or (
                f"{snapshot.ticker} material company developments, risks, and market context"
            )
            retrieval_started = perf_counter()
            chunks = LocalDocumentRetriever(documents).search(query, scope) if documents else []
            retrieval_latency_ms = round((perf_counter() - retrieval_started) * 1_000)
            request = extend_request_with_retrieval(
                request,
                chunks,
                query=query,
                scope=scope,
                reader_rules=args.llm_rule,
            )
            try:
                stored_retrieval = persist_retrieval(
                    storage,
                    documents=documents,
                    chunks=chunks,
                    query=query,
                    scope=scope,
                    reader_rules=tuple(request.evidence.get("reader_rules", ())),
                    latency_ms=retrieval_latency_ms,
                )
                storage_provenance = {
                    "status": "stored",
                    "retrieval_run_id": stored_retrieval.run_id,
                    "ruleset_id": stored_retrieval.ruleset_id,
                    "index_version": stored_retrieval.index_version,
                }
            except (OSError, TypeError, ValueError):
                storage_provenance = {"status": "failed"}
            retrieval_provenance = {
                "query": query,
                "scope": scope.to_dict(),
                "documents_considered": len(documents),
                "chunks_selected": len(chunks),
                "citations": [chunk.citation for chunk in chunks],
                "reader_rules": list(args.llm_rule),
                "local_storage": storage_provenance,
            }
            snapshot = replace(
                snapshot,
                evidence_scope=EvidenceScopeSummary(
                    status="available" if chunks else "empty",
                    source_types=list(scope.source_types),
                    query=query,
                    max_chunks=scope.max_chunks,
                    selected_chunks=len(chunks),
                    published_after=scope.published_after,
                    generated_at=datetime.now(UTC).isoformat(),
                ),
            )
        llm_result = generate_with_fallback(
            provider,
            request,
            performance=snapshot.performance,
            filings=snapshot.latest_filings,
            cache=JsonExplanationCache(args.llm_cache),
        )
        try:
            llm_storage_run_id = persist_llm_provenance(
                storage,
                request=request,
                result=llm_result,
            )
            llm_storage_provenance = {
                "status": "stored",
                "llm_run_id": llm_storage_run_id,
            }
        except (OSError, TypeError, ValueError):
            llm_storage_provenance = {"status": "failed"}
        provenance = {
            **snapshot.provenance,
            "grounded_explanation": {
                "provider": llm_result.provider,
                "model": llm_result.model,
                "cache_key": llm_result.cache_key,
                "cache_hit": llm_result.cache_hit,
                "status": (
                    "deterministic_fallback"
                    if llm_result.fallback_reason
                    else "grounded_llm"
                ),
                "retrieval": retrieval_provenance,
                "local_storage": llm_storage_provenance,
            },
        }
        snapshot = replace(
            snapshot,
            explanation=llm_result.explanation,
            provenance=provenance,
        )
    output = Path(args.out or f"data/build/company_{snapshot.ticker.lower()}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False))
    html_output = Path(
        args.html_out or f"data/build/company_{snapshot.ticker.lower()}.html"
    )
    render_company_page(snapshot, html_output)

    asset = snapshot.performance["asset"]
    print(f"{snapshot.company_name} ({snapshot.ticker}) — as of {snapshot.as_of}")
    print(f"  period              {snapshot.period['start']} to {snapshot.period['end']}")
    print(f"  total return        {asset['total_return']:.1%}")
    print(f"  CAGR                {asset['cagr']:.1%}")
    print(f"  max drawdown        {asset['max_drawdown']:.1%}")
    print(f"  beta vs {snapshot.benchmark:<9} {snapshot.performance['beta']:.2f}")
    print(f"  latest filings      {len(snapshot.latest_filings)}")
    if args.llm:
        if llm_result is None:
            print("  grounded brief      skipped: no local filing")
        elif llm_result.fallback_reason:
            print("  grounded brief      deterministic fallback")
        else:
            source = "cache" if llm_result.cache_hit else llm_result.model
            print(f"  grounded brief      {source}")
            retrieval = snapshot.provenance["grounded_explanation"].get("retrieval")
            if retrieval:
                print(
                    "  retrieval evidence  "
                    f"{retrieval['chunks_selected']} selected from "
                    f"{retrieval['documents_considered']} documents"
                )
    print(f"\nsnapshot written to {output}")
    print(f"company page written to {html_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
