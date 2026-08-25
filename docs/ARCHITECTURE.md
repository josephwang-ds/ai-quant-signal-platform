# Company Lens Architecture

Company Lens is a read product built on top of the existing point-in-time filing
pipeline. It does not restore the pre-rewrite research operating system.

## Runtime flow

```text
local/remote sources
  SEC filings ───────────────┐
  adjusted daily prices ─────┼──> deterministic snapshot ──> CLI / future API / UI
  company universe ──────────┘          │
                                        ├── performance and risk
                                        ├── filing NLP and citations
                                        └── bounded explanation
```

The snapshot is the product boundary. A UI must not calculate financial metrics,
re-run NLP, or ask an LLM to invent a field. It renders the versioned snapshot and
links back to its evidence.

## Package responsibilities

| Package | Owns | Does not own |
|---|---|---|
| `filing_triage` | point-in-time ingest, event study, leakage audit, attention ranking | company-page presentation |
| `company_lens.performance` | historical buy-and-hold and benchmark calculations | forecasts or strategy returns |
| `company_lens.filings` | item taxonomy, causal novelty, passages, numbers, SEC links | investment conclusions |
| `company_lens.llm` | structured explanation, bounded retrieval, validation and fallback | authoritative calculations or open web browsing |
| `company_lens.snapshots` | source assembly, freshness, provenance, warnings | provider-specific UI behavior |
| `company_lens.contracts` | stable serialized read models | business logic |

## Current vertical slice

`company-lens AAPL` reads `events.parquet`, `prices.parquet`, `universe.csv`, and
`provenance.json` from `data/build`. It writes a versioned JSON payload and a
self-contained HTML page that remain useful without network access or an LLM key.

The snapshot contains:

- one common asset/benchmark date range;
- a bounded cached-demo profile, SEC issuer identity, and observable evidence window;
- adjusted-close growth of a user-supplied initial investment;
- total return, CAGR, annualized volatility, maximum/current drawdown, worst day,
  recovery sessions, beta, and correlation;
- the latest five local 8-K filings, item labels, acceptance timestamps, and SEC
  source URLs;
- novelty computed only against earlier issuer filings;
- changed, added, and removed sentences against the latest earlier filing with the
  same form and primary SEC item;
- deterministic key passages and numbers with stable accession anchors;
- a cited deterministic explanation and explicit limitations; and
- source paths, input provenance, calculation version, and generation time.

## Trust rules

1. Deterministic code calculates every displayed number.
2. Asset and benchmark metrics share a declared period.
3. Filing novelty never compares a document with a future document.
4. Every extracted filing number points to a supplied passage.
5. Missing evidence stays missing; it is never represented as zero.
6. The explanation distinguishes historical observation from forecast.
7. An LLM provider is optional and must obey the same output contract as the
   deterministic fallback.
8. Filing comparison can only select a strictly earlier issuer filing with the same
   declared comparable key.

## Next interfaces

The next implementation steps are intentionally narrow:

1. preserve paragraph/table anchors during SEC normalization;
2. add prior-comparable-filing change detection and a labeled NLP evaluation set;
3. add an LLM provider protocol plus citation/numeric/unsupported-claim validators;
4. move local file loading behind source adapters and add cache freshness checks;
5. expose the snapshot through a small read-only API; and
6. add minimal idempotent refresh automation before any portfolio view.

The former research agent, alpha lab, factor discovery, strategy backtests, paper
trading, and broker actions stay outside this architecture.
