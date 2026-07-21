# Research Robustness Center (PR-024)

## Purpose

The Robustness Center is a **research management interface** that sits after
Validation. It organises which robustness checks are completed, pending,
planned, or blocked.

It is **not**:

- a stress-testing engine
- a new quantitative model
- a KPI / maturity dashboard
- a place to invent metrics, scores, or failure frequencies

## Inputs

Status is derived only from existing evidence:

- Validation result (PR-009), when available
- Evaluation result (PR-010), when available

No backend computation is added in this slice.

## Validation matrix

| Check | Implemented today | Typical status source |
| --- | --- | --- |
| Parameter Sensitivity | Yes | Validation / Evaluation |
| Benchmark Comparison | Yes | Validation / Evaluation |
| Transaction Cost | Yes | Validation / Evaluation |
| Data Quality | Yes | Validation / Evaluation |
| Stress Test | No | Always Planned |
| Market Regime Analysis | No | Always Planned |
| Walk-forward Validation | No | Always Planned |
| Monte Carlo Simulation | No | Always Planned |
| Liquidity & Capacity | No | Always Planned |

Allowed item states: `Completed` | `Pending` | `Planned` | `Blocked`.

Rules:

- **Completed** — existing evidence marks the stage completed
- **Pending** — supported workflow exists but evidence is incomplete / not yet run
- **Planned** — capability is not implemented
- **Blocked** — only when Evaluation is blocked (or a validation stage failed)

## Known failure conditions

Structured warnings for situations where conclusions should not be generalized.
Shown when the related matrix item is not completed. Copy is informational —
no fabricated numerical evidence.

## Next recommended action

The first unfinished matrix item in catalogue order:

1. resolve a blocked item, else
2. continue a pending item, else
3. continue the first planned item

## Surfaces

- Research Workspace tab: `?tab=robustness`
- Standalone module route: `/robustness` (canonical research evidence only)

## Authenticity

No fake percentages, radar charts, donut charts, or invented robustness scores.
