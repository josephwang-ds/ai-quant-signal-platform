# Research Deployment Center — Paper Trading (PR-025)

## Purpose

Paper Trading is a **research deployment and observation interface** that sits
after Robustness.

It is **not**:

- a broker terminal
- live trading
- an order management system
- a place to invent returns, fills, positions, PnL, or dates

## Inputs

Eligibility and observation plan status derive only from:

- Research definition (name, experiment, benchmark, strategy, lifecycle status)
- Validation / Evaluation evidence (when available)
- Robustness Center projection (PR-024)

No backend paper-session computation is added in this slice.

## Eligibility states

`Not Eligible` | `Needs Review` | `Eligible` | `Active` | `Completed` | `Stopped`

Rules:

- **Not Eligible** — no Validation evidence
- **Needs Review** — Validation/Robustness blocked or incomplete supported work
- **Eligible** — no blockers; incomplete planned work may remain; no session yet
- **Active / Completed / Stopped** — only when a **real** paper session exists
  (not available in this slice)

## Observation plan

Monitors listed without live values:

| Monitor | Without session |
| --- | --- |
| Signal Consistency | Pending if related evidence completed, else Planned |
| Benchmark Behaviour | same |
| Transaction Cost Drift | same |
| Drawdown Behaviour | Planned |
| Data Quality | Pending if related evidence completed, else Planned |
| Position Changes | Planned |

**Configured** only when a real session exists.

## Session

If no real session exists, show an empty state:

> Paper Trading has not started.
> This research has not entered observation.

Do not simulate trading.

## Review criteria

Checklist only; every item is **Awaiting Observation**. Never mark Passed.

## Surfaces

- Research Workspace tab: `?tab=paper`
- Standalone module route: `/paper-trading` (canonical research only)

## Lifecycle navigation

Research → Experiment → Validation → Robustness → Paper Trading → Decision → Archive

Decision and Archive are editorial placeholders until those slices ship.

## Authenticity

No KPI dashboard, trading terminal, candlesticks, portfolio widgets,
percentages, or dummy session data.
