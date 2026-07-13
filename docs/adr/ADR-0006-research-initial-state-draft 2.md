# ADR-0006: Research initial state is Draft

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision owners:** Architecture maintainers
- **Scope:** Research aggregate create semantics
- **ID note:** Formerly misnumbered as `0002-research-initial-state-draft.md`. That filename never superseded ADR-0002.

## Context

Chapter-02 Domain Model lists Research lifecycle as Proposed → Scoped → Active → ….  
Chapter-03 State Machine (authoritative for business state) defines Research aggregate states as Draft → Planning → Running → Synthesizing → Reviewed → Closed → Reopened.

CreateResearch must pick one initial state.

## Decision

`Research.create` always starts in **`Draft`**, matching Chapter-03. No transition beyond Draft is performed in CreateResearch.

Chapter-02 labels remain conceptual vocabulary; runtime and API expose Chapter-03 state values (`"Draft"`, …).

## Consequences

- Clients and tests assert `state == "Draft"` after create.
- Later slices (`StartResearchPlanning`, etc.) own explicit transitions; CreateResearch never silently advances state.

## References

- [Domain Model](../Architecture-Bible/Chapter-02-Domain-Model.md)
- [State Machine](../Architecture-Bible/Chapter-03-State-Machine.md)
- [ADR-0005 CreateResearch slice](ADR-0005-create-research-vertical-slice.md)
- [ADR index](README.md)
