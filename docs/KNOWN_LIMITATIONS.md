# Known Limitations

Concise product boundaries for this AI-assisted quantitative research workspace.
This is not a signal generator, trading platform, or investment recommendation system.

1. **Historical research only** — evidence is calculated on past market data.
2. **Not investment advice** — outputs do not recommend buying or selling.
3. **No live trading or broker execution** — there is no order routing.
4. **No portfolio optimization** — quantile / MA protocols are research evidence, not optimized books.
5. **No institutional risk model** — no VaR, factor risk, or borrow model.
6. **No guaranteed alpha** — past RankIC, Sharpe, or returns do not predict future performance.
7. **Market-data provider limitations** — Yahoo-style providers may throttle, adjust, or omit bars.
8. **Missing / adjusted / delayed data** — corporate actions and delayed feeds can distort history.
9. **Survivorship bias** — static universes may omit delisted names.
10. **Look-ahead controls** — position lag and month-end formation reduce leakage; residual risk remains in feature design and provider adjustments.
11. **Factor universe ≠ index membership** — sector-ETF presets are not historical index reconstitutions.
12. **Supported factors (v1)** — Momentum and Low Volatility only.
13. **Value is not implemented** — Coming Soon; unsupported requests are rejected.
14. **SHAP is optional** — if the `shap` package is absent, the API marks SHAP unavailable (no substitute values).
15. **Feature importance ≠ causality** — diagnostics do not explain future market movement.
16. **Single-asset ML sample size** — Compare Models on one symbol has limited statistical power.
17. **Regime / cost / parameter sensitivity** — results can flip under different windows or costs.
18. **Paper observation ≠ live capital** — paper stages are observational, not real deployment.

See also: [AUTHENTICITY.md](AUTHENTICITY.md), [DEMO_CONFIGURATIONS.md](DEMO_CONFIGURATIONS.md), ADR-0008.
