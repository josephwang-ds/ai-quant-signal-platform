# ADR-0005: CreateResearch as the first modular-monolith vertical slice

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision owners:** Architecture maintainers
- **Scope:** Research module delivery standard
- **ID note:** Formerly misnumbered as `0001-create-research-vertical-slice.md`. That filename never superseded ADR-0001.

## Context

The Architecture Bible and modular-monolith plan freeze module boundaries (`research`, `validation`, `governance`, `portfolio`, `market`) with `domain / application / infrastructure / presentation` per module. The legacy `backend/` app remains the deployed runtime until migration completes. We need one production-shaped use case that defines the coding standard without redesigning product behavior or migrating existing routes.

## Decision

Implement only **Research / CreateResearch** under `apps/api/src/modules/research/`, with:

- Domain entity + repository Protocol in `domain/`
- Command, Validator, Handler, DTOs in `application/`
- In-memory repository stub in `infrastructure/`
- FastAPI router in `presentation/`
- Composition root in `bootstrap/create_app.py`
- Unit tests (domain/application) and integration tests (HTTP)

Do not implement other Research use cases, other modules, or Strategy aggregate APIs in this change.

## Consequences

- Future slices copy this folder layout and dependency direction.
- Persistence can replace `InMemoryResearchRepository` at bootstrap without changing the Handler.
- Legacy `backend/` is unchanged; the new API surface is exercised via `apps/api` until the cutover mounts the same routers.

## References

- [ADR-0001 Modular Monolith](ADR-0001.md)
- [ADR-0003 Clean Architecture Through Vertical Slices](ADR-0003.md)
- [ADR index](README.md)
