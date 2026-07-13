# Architecture Decision Records

Authoritative numbering is sequential under the `ADR-NNNN` prefix.

| ID | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001.md) | Adopt a Modular Monolith as the Default Runtime | Accepted |
| [ADR-0002](ADR-0002.md) | Organize the Domain Around Bounded Contexts and Aggregates | Accepted |
| [ADR-0003](ADR-0003.md) | Apply Clean Architecture Through Vertical Slices | Accepted |
| [ADR-0004](ADR-0004.md) | Use Events and AI as Governed Workflow Participants | Accepted |
| [ADR-0005](ADR-0005-create-research-vertical-slice.md) | CreateResearch as the first modular-monolith vertical slice | Accepted |
| [ADR-0006](ADR-0006-research-initial-state-draft.md) | Research initial state is Draft | Accepted |

## Numbering rules

1. New decisions receive the next unused integer (`ADR-0007`, …).
2. Do not reuse IDs. Superseded decisions keep their ID and gain a `Superseded by` note.
3. Filenames may include a kebab-case slug after the ID for discoverability.
4. Historical collisions (`0001-create-research-vertical-slice.md`, `0002-research-initial-state-draft.md`) were retired in PR-001; their decisions live as ADR-0005 and ADR-0006.
