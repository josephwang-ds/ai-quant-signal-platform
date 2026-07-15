# ADR-0007: Route market data by asset class behind MarketDataPort

**Status:** Accepted  
**Date:** 2026-07-15  
**Deciders:** Research platform team  

## Context

PR-008B introduced `MarketDataPort` with a Yahoo Finance adapter hard-wired in
research routes. Portfolio demos need mainland China A-share daily history
without leaking provider selection into Execution, Validation, Evaluation, or
Copilot. A legacy `MarketDataService` auto-failover chain (`akshare → yahoo →
stooq`) exists for dashboard endpoints but must not become the research path.

## Decision

1. **Preserve one `MarketDataPort`** for research slices.
2. **Add `MarketDataRouter`** in infrastructure to classify symbols and invoke
   exactly one adapter per request.
3. **Yahoo** remains the default for US/HK equities, ETFs, indices, and crypto.
4. **AkShare** serves mainland A-shares (`*.SZ`, `*.SH`, `*.BJ`) with `qfq`
   adjustment by default.
5. **No automatic cross-provider failover** in this release — failures return
   honest provider-unavailable errors; stale cache may be served only under the
   existing labeled cache policy.
6. **Extend `DataProvenance`** with routing metadata without breaking existing
   frontend contracts (new fields are additive).

## Consequences

### Positive

- Research layers stay provider-agnostic.
- Deterministic, testable routing by asset class.
- Canonical SPY MA20/60 workflow unchanged (Yahoo via router).
- Offline CI remains fully deterministic with fixtures and mocks.

### Negative

- Two parallel market-data stacks coexist until legacy dashboard paths migrate.
- A-share research requires AkShare installed on the backend host.
- Provider override is restricted to validated combinations only.

## Alternatives considered

- **Reuse `MarketDataService` auto-failover in research** — rejected because
  AkShare and Yahoo do not provide equivalent symbol coverage or semantics.
- **Frontend provider selection for research** — rejected; violates Clean
  Architecture and authenticity policy.
- **Infer mainland exchange from first digit** — rejected; ambiguous without
  explicit suffix.

## Related

- `docs/slices/multi-provider-market-data.md`
- PR-008B Research Execution
- PR-009 Research Validation
