# Slice: Research Workspace Detail

Story 2.2. Research workspace for the canonical MA Crossover research project.

## Delivered

- `/research/[researchId]` workspace route
- Research list cards open the matching workspace
- Overview, Notebook, Experiments, Timeline, Validation, Evaluation, and Copilot tabs
- Research Execution evidence when the backend is available
- Local section navigation via canonical `?tab=` / `?section=` routing
- Right-side action panel wired to existing workflows (PR-020)
- Loading, error, and not-found states

## Workspace actions (PR-020)

| Action | Behavior |
|---|---|
| Add Notebook Entry | Navigate to Notebook (`?tab=notebook`). Does not auto-create an entry. |
| Create Experiment | Navigate to Experiments (`?tab=experiments`). Does not invent experiments. |
| Run Validation | Navigate to Validation; first visit lets `useResearchValidation` own the request; already-active evidence sections call `reloadValidation()` once. |
| Request Evaluation | Enabled only with `validation_run_id`. Navigate to Evaluation; reload only if already on that tab. Never re-runs Validation. |
| Open Research Copilot | Enabled only with `validation_run_id`. Navigate to Copilot. Does **not** submit a paid LLM request. |
| Export Research | Disabled. Honest hint: not available in this release. |

Duplicate-request prevention: one Validation/Evaluation hook instance owned by `ResearchWorkspacePage`; action rail never imports API clients.

## Key paths

```text
frontend/app/research/[researchId]/page.tsx
frontend/components/features/research/ResearchWorkspacePage.tsx
frontend/components/features/research/ResearchActionPanel.tsx
frontend/lib/workspaceActionTriggers.ts
frontend/lib/researchWorkspace.ts
```

## Demo

| State | How |
|---|---|
| Ready | `/research/ma-crossover-spy` |
| Validation | `/research/ma-crossover-spy?tab=validation` |
| Evaluation | `/research/ma-crossover-spy?tab=evaluation` (after Validation) |
| Copilot | `/research/ma-crossover-spy?tab=copilot` (after Validation) |
| Not found | `/research/does-not-exist` |

## Still deferred

- Export Research
- Durable Notebook / Experiment persistence beyond the current presentation/session model
- Files and Settings forms
- Auth / multi-tenant workspace boundaries
