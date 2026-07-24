# Paper Observation Center (PR-025, revised)

## Purpose

Paper Observation is a **bounded forward-observation log** that sits after
Robustness.

It is **not**:

- a broker terminal
- live trading
- an order management system
- a place to invent returns, fills, positions, PnL, or dates

## Inputs

Eligibility derives only from:

- Research definition (name, experiment, benchmark, strategy)
- Validation / Evaluation evidence (when available)
- the four implemented Robustness checks
- a real browser-local observation-session record

No backend trading or paper-account computation is added in this slice.

## Eligibility states

`Not Eligible` | `Needs Review` | `Eligible` | `Active` | `Completed`

Rules:

- **Not Eligible** — no Validation evidence
- **Needs Review** — Validation/Robustness blocked or incomplete supported work
- **Eligible** — all four implemented checks are complete; no session yet
- **Active / Completed** — only when a persisted observation session exists

## Observation plan

The reviewer supplies a cadence, minimum duration, and explicit exit criteria.
These fields are stored in browser-local storage and remain inspectable.

## Session

An active session accepts dated human notes. A reviewer can close the session,
after which its plan and notes remain visible. The application never generates
orders, fills, positions, returns, or PnL.

## Surfaces

- Research Workspace tab: `?tab=paper`
- Standalone module route: `/paper-trading` (canonical research only)

## Lifecycle navigation

Research → Experiment → Validation → Robustness → Paper Observation → Decision

Decision stores a human-authored outcome and rationale. Archive is a real
repository action rather than an empty page.

## Authenticity

No KPI dashboard, trading terminal, candlesticks, portfolio widgets,
percentages, or dummy session data.
