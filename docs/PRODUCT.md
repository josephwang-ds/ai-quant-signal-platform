# Product

## Positioning

**AI Investment Intelligence Platform**  
**Built on an Evidence-driven Quant Research Engine.**

Every AI insight is backed by structured research evidence. Explainable. Traceable. Reviewable.

Canonical identity strings live in `frontend/lib/productIdentity.ts` and must stay aligned across README, GitHub, site chrome, and resume copy.

## Phase status

```text
Phase 1 ✅ Data Foundation
Phase 2 ✅ Factor Research
Phase 3 ✅ Modeling
Phase 4 ✅ Intelligence Publishing Layer
Phase 4 RC ✅ Complete
```

Phase 5.1 Portfolio Registry Foundation is complete; Phase 5.2 snapshot builders
have not started. Release record: [`releases/PHASE_4_RC.md`](releases/PHASE_4_RC.md).

## What is this product?

The product presents two layers:

1. **AI Investment Intelligence** — user-facing answers to “what is happening?” (market, research, signal, portfolio, risk, assistant).
2. **Quant Research Engine** — the evidence layer that answers “why?” through a guided research workflow.

Research remains the source of truth. AI explains, summarizes, and helps review research; it does not replace deterministic validation or human decisions.

It is **not** a trading platform, broker, order-management system, or stock picker.

## Canonical surfaces (Phase 4 RC complete)

| Route | Surface |
| --- | --- |
| `/` | Research Library — published intelligence runs |
| `/platform` | Platform Overview |
| `/research/run_*` | Published Workspace (Overview, Signals, Evidence, Validation) |
| `/engine/research/*` | Active Workspace — catalog execution studies |
| `/post-trade` | Deterministic Performance Attribution and Anomaly Detection demo |

## Target users

- Quantitative researchers who need reproducible experiment and validation records
- Reviewers who must see what evidence exists before a decision
- Portfolio interviewers evaluating research-process quality (demonstration deployments)

## Design philosophy

| Principle | Meaning |
| --- | --- |
| Evidence before AI | Structured research evidence precedes any LLM summary or explanation |
| Deterministic before probabilistic | Validation and risk rules are testable; AI is advisory |
| Explainable · Traceable · Reviewable | Every intelligence surface must show its evidence path |
| Lifecycle over snapshots | Work progresses through named engine stages; history is preserved |

Canonical operating rule: **Research First. AI Second. Decisions Last.**

## Research lifecycle

```text
Research Setup → Data → Features → Factors → Modeling → Portfolio → Backtest → Review
```

| Stage | Intent |
| --- | --- |
| Research Setup | Frame the question, universe, horizon, and protocol |
| Data Foundation | Assemble point-in-time market inputs |
| Feature Engineering | Build features and labels |
| Factor Research | Evaluate individual factors |
| Modeling | Produce leakage-safe out-of-sample scores |
| Portfolio Construction | Convert scores into constrained weights |
| Backtesting | Evaluate costs, turnover, and robustness |
| Research Review | Human Promote / Hold / Reject on accumulated evidence |

Archive is a real research action after review, not an empty lifecycle page.

Details: [`RESEARCH_WORKFLOW.md`](RESEARCH_WORKFLOW.md).

## Why it is not a trading platform

| Trading platform | This workspace |
| --- | --- |
| Primary object: order | Primary object: strategy / research evidence |
| Outcome: execution | Outcome: governed research decision |
| Broker connectivity | Explicitly none in the demo surface |
| Live P&L as product truth | P&L only when calculated from real sessions or backend evidence |

Demo and portfolio deployments must state: research only, not investment advice, no live trading, no broker connection. See [`AUTHENTICITY.md`](AUTHENTICITY.md).

## Reference studies

Bundled samples for demonstration:

- **Trend Following Study** (`ma-crossover-spy`)
  - Protocol: SPY MA20 / MA60 vs buy-and-hold
- **Cross-Sectional Momentum Factor Study** (`cross-sectional-factor-sector-etfs`)
- **Cross-Sectional Low Volatility Factor Study** (`cross-sectional-low-vol-sector-etfs`)
  - Factor validation on `us_sector_etfs` (Momentum / Low Volatility; Value Coming Soon)
  - Evidence: RankIC / ICIR and equal-weight Q1–Q5 long–short — not portfolio optimization

They demonstrate the lifecycle. They do not imply live investment use.
