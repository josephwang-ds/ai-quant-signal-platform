# Slice: Research Hub / Research List (research-first)

Story 2.1. Product homepage. Local persistence + catalog demo.

## Product model

Research is **one research question**, not one ticker/strategy file.

```text
Research (question + hypothesis)
  └── Experiments (designed later inside the workspace)
        └── Evidence (backend-calculated only)
```

Create on the Hub asks for title, question, hypothesis, and optional tags.
Ticker, strategy windows, dates, and costs belong to Experiments — not Research create.

## Delivered

- `/` → `ResearchListPage` (Research Hub)
- Header: Research + New Research
- Toolbar (slim): Search, Status, Sort (updated / created / name)
- Cards (whole-card clickable):
  - Title + status
  - Research question
  - Experiment count
  - Latest evidence (`evidenceSummary` — never invented)
  - Relative updated time
  - Overflow archive (no primary CTA button)
- States: Loading (skeleton), Empty (catalog + filter), Error + Retry
- No KPI strip / fake statistics on the Hub

## Key paths

```text
frontend/app/page.tsx
frontend/components/features/research/ResearchListPage.tsx
frontend/components/features/research/ResearchCard.tsx
frontend/components/features/research/NewResearchModal.tsx
frontend/components/features/research/ResearchListSkeleton.tsx
frontend/lib/localResearchRepository.ts
frontend/lib/researchRepository.ts
frontend/lib/researchListFilters.ts
frontend/types/research.ts
```

## Create contract (local)

```ts
CreateResearchInput = {
  name: string;
  researchQuestion: string;
  hypothesis: string;
  tags: string[];
  owner?: string;
}
```

New research starts as **Draft**, `experimentCount: 0`, no `runConfiguration`.
MA/run configuration remains on the canonical demo for the executable SPY MA20/60 pipeline.

## Demo

Canonical id `ma-crossover-spy` is framed as **Trend Following Study**.
Executable protocol is unchanged (SPY MA20/60). Evidence remains backend-only.

## Future integration

| Action | TODO |
|---|---|
| Load | `GET /api/research` |
| New Research | `POST /api/research` (CreateResearch — align question/hypothesis fields) |
| Open Workspace | `/research/[id]` |
| Experiments | Persist under `researchId`; compose ticker/strategy there |
| Archive | dedicated command |
