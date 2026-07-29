# ADR-0014: AI Investment Intelligence Platform information architecture

- Status: Accepted
- Date: 2026-07-28

## Context

The product previously presented as a Research Library / research-home collection with fragmented surfaces (experiments, lifecycle cards, activity feeds). That IA competed with the flagship Cross-Sectional Equity Research path and obscured the relationship between AI surfaces and deterministic research evidence.

## Decision

Reorganize the frontend into two product layers:

1. **AI Investment Intelligence** (user-facing): Market, Research, Signal, Portfolio, Risk, and AI Research Assistant. These answer “what is happening?” and must remain evidence-backed.
2. **Quant Research Engine** (evidence layer): an eight-stage guided workflow — Research Setup → Data Foundation → Feature Engineering → Factor Research → Modeling → Portfolio Construction → Backtesting → Research Review.

Homepage becomes the Intelligence Platform overview, not a project catalog. Experiments are not a top-level destination; their content is absorbed into the producing engine stage. Documentation (Architecture, API, Methodology, ADR) is a third nav group linking to repository docs.

Existing research workspaces (`/research/[id]`), Strategy Studio, Compare Models, Data Center, Market Watch, and AI Insights remain reachable as tools under the appropriate layer — they are not deleted.

## Consequences

- Navigation and routing change; `/experiments` redirects into `/engine/backtest`.
- Intelligence pages may show honest “evidence not yet available” states rather than inventing summaries, rankings, or portfolio health.
- Phase 4+ engine stages remain shell-only until backend work is explicitly scoped.
- Product identity chrome uses “AI Investment Intelligence Platform” with the frozen slogan and philosophy in `frontend/lib/productIdentity.ts`. Domain invariants in `docs/PROJECT_BIBLE.md` remain authoritative for research-control behavior.
