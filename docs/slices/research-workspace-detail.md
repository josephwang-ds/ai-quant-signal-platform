# Slice: Research Workspace Detail (PR-003)

Story 2.2. Mock-only detail workspace for one research project.

## Delivered

- `/research/[researchId]` workspace route
- Research list cards open the matching workspace
- Overview fully implemented (question, hypothesis, objective, stage, confidence, recommendation, summaries, evidence, strengths/weaknesses, open questions, next actions)
- Reusable `LifecycleProgress` (Ch3 stages)
- Local section navigation with informative placeholders for non-Overview tabs
- Right-side action panel (disabled / deferred)
- Loading, error (`?mockError=1`), and not-found states
- Shared mock catalog so list and detail stay consistent

## Key paths

```text
frontend/app/research/[researchId]/page.tsx
frontend/components/features/research/ResearchWorkspacePage.tsx
frontend/components/features/research/{ResearchWorkspaceHeader,ResearchWorkspaceNavigation,OverviewSection,LifecycleProgress,EvidenceSummary,ResearchActionPanel,WorkspacePlaceholder,ResearchWorkspaceSkeleton}.tsx
frontend/components/ui/{TagList,MetricSummaryCard}.tsx
frontend/lib/mockResearchCatalog.ts
frontend/lib/researchWorkspace.ts
frontend/types/research.ts
```

## Demo

| State | How |
|---|---|
| Ready | `/research/rs-momentum-001` |
| Section placeholder | `/research/rs-momentum-001?section=notebook` |
| Not found | `/research/does-not-exist` |
| Error | `/research/rs-momentum-001?mockError=1` |

## Out of scope (deferred)

Notebook editing, experiment creation, validation execution, evaluation engine, files, settings forms, backend, auth, AI review, portfolio.
