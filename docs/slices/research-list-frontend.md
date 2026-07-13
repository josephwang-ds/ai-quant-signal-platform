# Slice: Research Workspace / Research List (PR-002)

Story 2.1. Product homepage. Mock-only.

## Delivered

- `/` → `ResearchListPage` (homepage)
- Header: Research Workspace + PR subtitle + New Research
- Toolbar: Search, Status, Owner, Tag, Sort
- Cards: name, question, owner, status, confidence, tags, experiments, last validation, recommendation, updated
- States: Loading (skeleton), Empty (catalog + filter), Error (`?mockError=1` + Retry)
- Responsive: 1 → 2 column card grid; stacked filters on small screens
- Reusable: `ResearchCard`, `StatusBadge`, `ConfidenceBadge`, `EmptyState`

## Key paths

```text
frontend/app/page.tsx
frontend/components/features/research/ResearchListPage.tsx
frontend/components/features/research/ResearchCard.tsx
frontend/components/features/research/ResearchListSkeleton.tsx
frontend/lib/mockResearchList.ts
frontend/lib/researchListFilters.ts
frontend/types/research.ts
frontend/components/ui/{StatusBadge,ConfidenceBadge,EmptyState}.tsx
```

## Demo states

| State | How |
|---|---|
| Ready | `/` |
| Loading | brief on each load |
| Filter empty | set Status to a non-matching combo |
| Error | `/?mockError=1` then Retry after removing the param |

## Future integration

| Action | TODO |
|---|---|
| Load | `GET /api/research` |
| New Research | `POST /api/research` (CreateResearch) |
| Open Workspace | `/research/[id]` |
| Duplicate / Archive | dedicated commands |
