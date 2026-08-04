# Authenticity

This document summarises the repository authenticity policy for portfolio and open-source readers. Full policy text: [`data/AUTHENTICITY_POLICY.md`](data/AUTHENTICITY_POLICY.md).

## Research-first philosophy

Quantitative evidence is authoritative. AI may explain, summarise, or compare evidence. AI must not create performance truth, override validation, or invent confidence.

## Explicit prohibitions

| Prohibited | Required behaviour |
| --- | --- |
| Fabricated performance | Metrics only from Research Execution / Validation responses |
| Fake P&L | No invented session or portfolio P&L in empty states |
| Fake trades | No synthetic fills or trade journals without a real session |
| Fake confidence scores | Confidence / evaluation scores only when backend evidence exists |
| Fake approvals | Decision / governance labels only from real lifecycle evidence |
| Silent provider fallbacks | Provider failure → error / unavailable — never demo numbers |

Deterministic synthetic fixtures are permitted only when all of the following
are true:

- the interface labels them as synthetic demo data before showing results;
- the API contract records `input_data_kind=synthetic_demo`;
- no value is described as a live fill, exchange observation, or realized return;
- the same deterministic service accepts caller-supplied observations without
  changing methodology.

## Allowed without calculation

- Research name, question, hypothesis, objective
- Protocol parameters (symbol, windows, costs)
- Planned stage names and pending statuses
- Design notebook notes clearly labeled as planning
- Product copy that describes intended capabilities without claiming completed results

## Canonical sample

**Trend Following Study** (`ma-crossover-spy`) — SPY MA20/MA60 vs buy-and-hold.

**Cross-Sectional Momentum Factor Study** (`cross-sectional-factor-sector-etfs`) — sector-ETF RankIC / quantile validation (Momentum).

**Cross-Sectional Low Volatility Factor Study** (`cross-sectional-low-vol-sector-etfs`) — same universe protocol for Low Volatility.

**Feature Interpretation** (Compare Models) — diagnostic importance only; does not change predictions or backtest metrics. SHAP is optional. Feature importance does not imply causality.

**Post-Trade Analytics** — deterministic synthetic trade and latency observations
demonstrate attribution and anomaly-detection contracts. They are not production
orders, exchange data, or realized investment performance.

Static definition metadata is allowed. Calculated evidence appears only after successful backend execution/validation.

## Enforcement

- Frontend authenticity regression tests (`frontend/lib/publicPreviewAuthenticity.test.ts` and related)
- Backend research routes reject inventing metrics on provider failure
- Copilot returns structured failure when the LLM is unavailable; it does not fabricate answers
- Factor Copilot summarizes stored RankIC / ICIR / turnover / long–short evidence only; it does not forecast or recommend trades
- Governance Agent orchestrates review with LangGraph; DeepSeek does not create quantitative truth

## Demo language

Portfolio demonstration surfaces must communicate:

- research only
- not investment advice
- no live trading
- no broker connection
