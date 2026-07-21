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

## Allowed without calculation

- Research name, question, hypothesis, objective
- Protocol parameters (symbol, windows, costs)
- Planned stage names and pending statuses
- Design notebook notes clearly labeled as planning
- Product copy that describes intended capabilities without claiming completed results

## Canonical sample

**Trend Following Study** (`ma-crossover-spy`) — SPY MA20/MA60 vs buy-and-hold.

Static definition metadata is allowed. Calculated evidence appears only after successful backend execution/validation.

## Enforcement

- Frontend authenticity regression tests (`frontend/lib/publicPreviewAuthenticity.test.ts` and related)
- Backend research routes reject inventing metrics on provider failure
- Copilot returns structured failure when the LLM is unavailable; it does not fabricate answers

## Demo language

Portfolio demonstration surfaces must communicate:

- research only
- not investment advice
- no live trading
- no broker connection
