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
18. **Walk-forward is not a future-return guarantee** — chronological expanding/rolling folds with fixed MA20/MA60 reduce but do not eliminate overfitting risk; the protocol is not per-fold parameter tuning, and Compare Models walk-forward is a separate ML path.
19. **Paper observation ≠ live capital** — paper stages are observational, not real deployment.
20. **Governance Agent runs are process-local** — LangGraph MemorySaver / in-memory run store may be lost on Render restart.
21. **Research Rulebook is curated local docs** — not a broad financial corpus or external paper search.
22. **No autonomous multi-day research loops** — tool calls and planning cycles are hard-capped.
23. **DeepSeek interpretation is imperfect** — all AI output requires human review; metrics stay deterministic.
24. **In-memory demo rate limits are single-instance** — request rate limits and LLM concurrency use process-local counters suitable for a one-process portfolio demo (for example one Render web service). They are not a distributed multi-replica exact limiter.
25. **Trusted-proxy client IP** — `X-Forwarded-For` / `X-Real-IP` are consulted only when the direct TCP peer is listed in `TRUSTED_PROXY_IPS`; arbitrary forwarding headers are not blindly trusted.
26. **Public-demo request budgets** — body size, symbol-list length, prompt/question length, notes/rationale length, LLM concurrency, and explicit LLM/provider/validation timeouts are enforced to protect cost and availability.

See also: [AUTHENTICITY.md](AUTHENTICITY.md), [AGENT_GOVERNANCE.md](AGENT_GOVERNANCE.md), [DEMO_CONFIGURATIONS.md](DEMO_CONFIGURATIONS.md), ADR-0008, ADR-0010.
