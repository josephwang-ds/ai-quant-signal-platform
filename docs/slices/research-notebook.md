# Slice: Research Notebook (PR-004)

Story 2.3. Structured research record inside each Research Workspace.

## Delivered

- `/research/[researchId]?tab=notebook` (backward compatible with `?section=notebook`)
- Entry types: Observation, Hypothesis, Decision, Action, Result, Reflection
- Filters, sort, entry cards, composer with inline validation
- Light Markdown rendering (no new rich-text dependency)
- Shared mock catalog consistent with list/detail
- Session-local new entries + timeline event append
- Loading, empty, filter-empty, error states

## Key paths

```text
frontend/components/features/research/notebook/
frontend/lib/mockNotebookCatalog.ts
frontend/lib/researchNotebook.ts
frontend/lib/notebookMarkdown.ts
frontend/types/notebook.ts
```

## Demo

| State | URL |
|---|---|
| Notebook | `/research/rs-momentum-001?tab=notebook` |
| New entry | Click **New Entry** on notebook tab |
| Filter empty | Filter to a type with no matches |
| Timeline event | Save entry → open **Timeline** tab |

## Deferred

Backend persistence, collaboration, attachments, AI notes, global event bus.
