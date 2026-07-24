# Product

## What is AI Quant Research Workspace?

**AI Quant Research Workspace** is a research operating space for moving quantitative ideas through a visible lifecycle: definition → experiment → validation → robustness review → paper observation → decision.

It keeps hypotheses, protocols, calculated evidence, and governed next steps in one place so conclusions remain traceable.

It is **not** a trading platform, broker, order-management system, or stock picker.

## Target users

- Quantitative researchers who need reproducible experiment and validation records
- Reviewers who must see what evidence exists before a decision
- Portfolio interviewers evaluating research-process quality (demonstration deployments)

## Design philosophy

| Principle | Meaning |
| --- | --- |
| Research first | Quantitative evidence is produced before AI interpretation |
| Deterministic before probabilistic | Validation and risk rules are testable; AI is advisory |
| Evidence before conclusion | Durable claims require metrics, provenance, and source |
| Lifecycle over snapshots | Work progresses through named stages; history is preserved |

Canonical product statement: **Research First. AI Second. Decisions Last.**

## Research lifecycle

```text
Research → Experiment → Validation → Robustness → Paper Observation → Decision
```

| Stage | Intent |
| --- | --- |
| Research | Frame the question, hypothesis, and protocol |
| Experiment | Define and run historical execution against real market data |
| Validation | Deterministic OOS, sensitivity, cost, and data-quality checks |
| Robustness | Review four implemented checks and disclose unsupported methods as scope boundaries |
| Paper Observation | Create a bounded browser-local plan and record dated notes — not live brokerage |
| Decision | Save a human-authored outcome and rationale against the evidence |

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

## Reference study

One bundled sample exists for demonstration:

- **Trend Following Study** (`ma-crossover-spy`)
- Protocol: SPY MA20 / MA60 vs buy-and-hold

It demonstrates the lifecycle. It does not imply live investment use.
