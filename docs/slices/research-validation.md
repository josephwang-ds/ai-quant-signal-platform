# Slice: Research Validation Pipeline (PR-006)

Story 2.5. Evidence-oriented validation pipeline inside each Research Workspace.

## Delivered

- `/research/[researchId]?tab=validation`
- Optional detail selection via `?validationStageId=`
- Eight-stage pipeline overview + readiness
- Deterministic mock gates and blocking issues
- Stage search / status filter + detail panel
- Timeline linkage via mock `Validation*` events
- Loading / empty / filter-empty / error / not-found states
- Disabled “Run Validation” (governed workflow deferred)

## Demo

| State | URL |
|---|---|
| Pipeline | `/research/rs-momentum-001?tab=validation` |
| Detail | open Stress Testing / any stage |
| Blocked (thin evidence) | `/research/rs-rsi-002?tab=validation` |
| Empty | `/research/rs-vol-004?tab=validation` |
| Timeline | open Timeline after Validation tab loads events |

## Deferred

Validation engine, ValidationRun API, persistence, Evaluation packet generation, Research Confidence calc, AI interpretation.
