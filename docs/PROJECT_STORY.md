# Project Story

Interview-oriented narrative for **AI Quant Research Workspace**. Factual, not marketing.

## Problem

Quantitative research rarely fails for lack of another chart. It fails when hypotheses, datasets, experiments, validation, and decisions live in disconnected notebooks and sheets. Reviewers cannot see what evidence exists, what is still planned, or why a conclusion is allowed.

Hiring-manager-visible failure mode for “demo products”: fabricated Sharpes, fake P&L, and UI that implies live trading.

## Product decision

Build a **research operating system** that makes one lifecycle explicit:

```text
Research → Experiment → Validation → Robustness → Paper Trading → Decision → Archive
```

Positioning:

- Primary object: strategy / research evidence
- Primary outcome: governed research decision
- Explicit non-goals: broker integration, live execution, stock picking

Canonical demo protocol: Trend Following Study (`ma-crossover-spy`) — SPY MA20/MA60 vs buy-and-hold.

## Technical architecture

Current demonstrable runtime:

```text
Next.js (Vercel) → FastAPI (Render) → Market data (Yahoo / AkShare)
                                 → Optional LLM (Copilot, backend secrets)
                                 → Optional Supabase Postgres (legacy experiment durability)
```

- Frontend owns workspace UX and honest empty states
- Backend owns historical execution, deterministic validation, evaluation summary, Copilot
- Longer-term modular-monolith / DDD design is documented in the Architecture Bible; `apps/api/` is a reference path, not the live demo path

## Authenticity principles

- No fabricated performance, P&L, trades, confidence scores, or paper sessions
- Metrics only from backend responses
- Provider failure → error / unavailable — never substitute demo numbers
- Unimplemented work stays Planned / Not Started
- AI interprets evidence; it does not create quantitative truth

See [AUTHENTICITY.md](AUTHENTICITY.md).

## Major trade-offs

| Choice | Why |
| --- | --- |
| Narrow executable template (MA crossover) | Complete vertical slice beats shallow multi-strategy theatre |
| Management centers for Robustness / Paper / Decision | Show lifecycle organisation without inventing engines or fills |
| Browser-local research definitions (today) | Unblocks demos; durability is an honest limitation |
| Evaluation folded into Validation UX | Keep the product spine to seven stages |
| Copilot as supporting tool | Explanation without becoming the climax of the demo |

## What was intentionally not built

- Broker connectivity / production OMS
- Autonomous trading agents
- Full stress / regime / Monte Carlo engines presented as finished
- Fake Decision Room / Ledger “results” for public preview
- Claiming cross-browser durable research persistence before it exists

## Future improvements

- Durable research + validation lineage across restarts and browsers
- Deeper robustness engines under the same authenticity rules
- Stronger CI gates and dependency-boundary checks
- Incremental migration toward the frozen Architecture Bible shape without rewriting the demo path overnight

## One-line summary

A portfolio-ready research workspace that prefers an honest empty state over a convincing lie.
