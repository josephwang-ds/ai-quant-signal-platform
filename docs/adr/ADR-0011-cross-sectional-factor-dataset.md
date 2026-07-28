# ADR-0011: Cross-Sectional Factor Dataset (Phase 1)

**Status:** Accepted  
**Date:** 2026-07-28  
**Last verified:** 2026-07-28  
**Deciders:** Research platform team  

## Context

Phase 0 approved an additive expansion toward a cross-sectional equity
factor research workflow. The repository already ships ADR-0008
`factor_validation/` (sector-ETF Momentum / Low Volatility RankIC + Q1–Q5).
That path must remain unchanged.

Phase 1 needs a reusable, leakage-safe **date × symbol** factor panel with
quality reporting, without model training, portfolio construction, frontend
redesign, or a mega research endpoint.

## Decision

1. Add package `backend/app/cross_sectional/` as an additive Research /
   Market Intelligence utility. It does **not** replace `factor_validation/`.
2. Expose `POST /api/v1/research/cross-sectional/dataset` only. Do not add
   an orchestrated `/cross-sectional` mega endpoint in this phase.
3. Universe preset **`us_liquid_31_v1`** is a **static, manually configured
   demonstration** membership list (31 unique tickers including `MU` and
   domain-form `BRK-B`). Authoritative membership lives only in
   `backend/app/cross_sectional/universe.py`. Callers may override `symbols`.
   This is **not** a point-in-time S&P 500 (or any index) universe.
   Historical membership and **survivorship bias are not solved**.
4. Factor grain is one row per `(date, symbol)`. Factors use only information
   available on or before date `t`. Labels are forward returns and never enter
   factor calculations. Rolling windows and shifts are computed **per symbol**
   after sorting by date; they never cross symbol boundaries.
5. Factor families in v1: momentum, risk, volume/liquidity (fixed column set).
   No RSI/MACD/fundamentals/sentiment/model scores.
6. **`downside_volatility_20d`** (API field name retained) is **annualized
   downside deviation**:
   `sqrt(mean(min(r, 0)^2)) * sqrt(252)` over a trailing 20-observation window
   with `min_periods=20`. Positive returns are replaced with zero; negatives
   are preserved. Insufficient history → null (not zero, not infinity).
7. Adjusted-price behavior depends on the current `MarketDataPort` provider
   adapter (`adjustment=auto`). This is not an institutional corporate-action
   feed.
8. Market data is loaded exclusively through `MarketDataPort` (ADR-0007).
   Provider-specific ticker formatting stays in adapters; the universe list
   keeps domain-canonical tickers.
9. API returns configuration, dataset summary, quality/coverage summaries,
   feature metadata, and a bounded `records_preview` — never an unlimited
   panel payload. Null factors/labels serialize as JSON `null`, not zero.
10. Quality checks distinguish expected warm-up nulls, expected future-label
    nulls, provider failures, and calculation failures. Missing stays missing;
    infinities become missing and are counted.
11. Persist a **summary-only** artifact via `ValidationResultStore` as
    `dataset_run_id`. This does not mutate Trend Following or Factor
    Validation research state. Existing evidence kinds remain separate.

## Phase 1 scope boundary (explicit non-goals)

Phase 1 does **not** implement RankIC, model scoring, stock ranking,
portfolio construction, backtesting, frontend integration, governance
wiring beyond the dataset summary store key, monitoring, or LLM features.

## Consequences

### Positive

- Interview-friendly, testable panel builder beside the existing factor study.
- Clear leakage contract and honest universe disclosures.
- Existing Trend Following and Factor Validation APIs stay intact.

### Negative

- Static universe retains survivorship bias.
- No sector field yet (`sector` listed under `unavailable_evidence`).
- Provider-adjusted prices are not an institutional corporate-action feed.

## Alternatives considered

- **Replace ADR-0008 / introduce `factor_research/`** — rejected; breaks
  accepted contracts and existing studies.
- **Extend monthly ETF factor panels only** — rejected; cannot support the
  daily multi-factor stock panel needed for later ranking phases.
- **Return full panels over HTTP** — rejected; payload risk and demo limits.
- **Sample std of clipped returns for downside** — rejected in verification
  pass; Phase 1 standardizes on RMS downside deviation as documented above.

## Related

- ADR-0007 Market data router
- ADR-0008 Factor validation engine
- `docs/data/AUTHENTICITY_POLICY.md`
- Phase 0 audit (approved)
