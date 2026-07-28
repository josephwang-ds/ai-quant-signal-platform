# ADR-0012: Cross-Sectional Factor Research (Phase 2)

**Status:** Accepted  
**Date:** 2026-07-28  
**Deciders:** Research platform team  

## Context

Phase 1 delivered a leakage-safe date×symbol factor panel
(`ADR-0011`, package `cross_sectional/`). Existing ADR-0008
`factor_validation/` continues to serve the sector-ETF Momentum / Low
Volatility study and must remain unchanged.

Phase 2 evaluates whether Phase 1 factors consistently rank future returns
across dates and horizons. It does **not** train models or construct
portfolios.

## Decision

1. **Additive package** `backend/app/cross_sectional/research/` on top of
   Phase 1. Do not replace `factor_validation/` or rewrite Phase 1 modules.
2. **Universes:** preserve verified `us_liquid_31_v1` (default). Add
   selectable `us_liquid_50_v1` = all 31 names plus 19 curated extras.
   Both are static demonstration lists — **not** historical S&P 500 /
   Nasdaq-100 membership; survivorship bias is not solved.
3. **Endpoint:** `POST /api/v1/research/cross-sectional/factors` only.
   No mega research endpoint. Phase 1 dataset endpoint unchanged.
4. **Panel reuse:** research calls `CrossSectionalDatasetService.load_panel`
   (internal) so factors/labels are not recalculated separately.
5. **Research factors:** Phase 1 continuous factors only.
   `liquidity_eligible` is an eligibility filter, not an alpha factor.
6. **Eligibility** is computed per factor × label × date. Missing values
   stay missing. Below-minimum cross-section → `unavailable`, not zero IC.
   Default `minimum_cross_section_size=10` (justified for 31–50 name demos;
   also supports 5×`minimum_quantile_size=2`).
7. **RankIC:** daily cross-sectional Spearman (average-rank ties). Dates are
   not pooled before IC. Constant factor/label → unavailable.
8. **ICIR:** `mean(RankIC) / std(RankIC, ddof=1)`. **Not annualized.**
   Zero/undefined std → null ICIR.
9. **Quantiles:** Q1 = lowest factor … Qn = highest; equal-weight mean
   forward return; top−bottom = Qn−Q1. No costs. Risk factors are **not**
   auto-inverted.
10. **Turnover:** `1 - Spearman(factor_rank_t, factor_rank_{t-1})` on
    overlapping eligible symbols; range `[0, 2]`; insufficient overlap →
    unavailable. Descriptive only — no cost claim.
11. **Correlation:** pairwise Spearman of factor values; unordered pairs
    (`factor_a < factor_b`); redundancy warnings descriptive only.
12. **Stability:** calendar-year summaries; thin years → unavailable.
13. **Sector analysis:** unavailable unless deterministic sector metadata
    exists (it does not in Phase 2).
14. **Summaries** expose evidence status (`complete|incomplete|unavailable|failed`)
    without an opaque Factor Score and without Promote/Hold/Reject wiring.

### Reuse vs reimplement

| Component | Decision |
|-----------|----------|
| ADR-0008 `_spearman_rank_ic` / wide-panel engines | **Not imported** — silently drop thin dates; wide monthly panels; costed LS books |
| Conceptual Spearman + Q1-low/Q5-high + symbol tie-break | **Reimplemented** for long panels with explicit unavailable states |
| Phase 1 `load_panel` / factor builders | **Reused** |

## Non-goals

No Ridge/LightGBM/XGBoost, scores, SHAP/PCA, Top-K, weights, costs,
portfolio backtests, frontend, LLM, governance Promote/Hold/Reject expansion,
live trading, or monitoring.

## Consequences

### Positive

- Interview-friendly factor evidence layer beside existing studies.
- Clear metric conventions and unavailable-state honesty.

### Negative

- Static universes retain survivorship bias.
- Daily RankIC on ~31–50 names is noisy; minimum sample gates are required.
- No sector diagnostics in this phase.

## Related

- ADR-0008 Factor validation engine
- ADR-0011 Cross-sectional factor dataset
- `docs/data/AUTHENTICITY_POLICY.md`
