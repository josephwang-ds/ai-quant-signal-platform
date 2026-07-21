# Decision Center (PR-026)

## Purpose

The Decision Center is a **research approval interface** at the end of the
research lifecycle, after Paper Trading.

It is **not**:

- portfolio management
- a place to invent trading results, approvals, or confidence scores
- a backend decision engine

## Inputs

Status and checklists derive only from:

- Research definition and lifecycle status
- Validation / Evaluation evidence
- Robustness Center projection (PR-024)
- Paper Trading Deployment projection (PR-025)

No backend decision API is added in this slice.

## Decision status

`Not Ready` | `Under Review` | `Approved for Paper Trading` | `Rejected` | `Archived`

Rules:

- **Archived** — research lifecycle status is Archived
- **Approved for Paper Trading** — lifecycle is Paper Trading or Monitoring
  (existing operational state only)
- **Rejected** — never invented; no rejection artifact in this slice
- **Under Review** — validation exists but review work remains
- **Not Ready** — no validation evidence

## Decision evidence

Validation, Robustness, Paper Trading — each `Completed` or `Pending` only.

## Remaining risks

Unresolved items from Robustness failure conditions and pending implemented
robustness checks. No fabricated risk scores.

## Approval checklist

Completed / Pending only. Never invent approvals.

## Decision notes

Read-only. If no real notes exist: “No decision notes available.”

## Surfaces

- Research Workspace tab: `?tab=decision`

## Authenticity

No KPI cards, gauges, donut charts, fake scores, or confidence percentages.
