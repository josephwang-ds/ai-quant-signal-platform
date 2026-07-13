# Slice: Research Experiments (PR-005)

Story 2.4. Structured experiment registry inside each Research Workspace.

## Delivered

- `/research/[researchId]?tab=experiments`
- Optional detail selection via `?experimentId=`
- Status / type filters, search, sort
- Local Designed composer with validation
- Experiment detail + Ch3 lifecycle + metrics
- Session Notebook Decision + Timeline `ExperimentDesigned` on create
- Loading / empty / filter-empty / error / not-found states

## Demo

| State | URL |
|---|---|
| List | `/research/rs-momentum-001?tab=experiments` |
| Detail | open any card |
| New | **New Experiment** → Save as Designed |
| Timeline | save then open Timeline tab |

## Deferred

Execution engine, approval workflow, persistence, Validation engine, AI interpretation.
