# Slice: Research / CreateResearch

First vertical slice of the modular monolith. Coding standard for all future use cases.

## 1. Folder tree

```text
apps/api/
├── pytest.ini
├── src/
│   ├── bootstrap/
│   │   ├── __init__.py
│   │   └── create_app.py
│   ├── modules/
│   │   └── research/
│   │       ├── domain/
│   │       │   ├── research.py              # Entity + ResearchState
│   │       │   └── repository.py            # ResearchRepository port
│   │       ├── application/
│   │       │   ├── commands/
│   │       │   │   ├── create_research_command.py
│   │       │   │   ├── create_research_validator.py
│   │       │   │   └── create_research_handler.py
│   │       │   └── dto/
│   │       │       └── research_dto.py
│   │       ├── infrastructure/
│   │       │   └── repositories/
│   │       │       └── in_memory_research_repository.py
│   │       └── presentation/
│   │           └── router.py                # POST /api/research
│   └── shared/
│       └── errors/
│           └── domain_error.py
└── tests/
    ├── unit/research/test_create_research.py
    └── integration/research/test_create_research_api.py
```

## 2. Dependency graph

```mermaid
flowchart TB
  subgraph presentation["presentation"]
    R["router.py"]
  end
  subgraph application["application"]
    C["CreateResearchCommand"]
    V["CreateResearchValidator"]
    H["CreateResearchHandler"]
    D["ResearchResponse / CreateResearchRequest"]
  end
  subgraph domain["domain"]
    E["Research entity"]
    P["ResearchRepository Protocol"]
  end
  subgraph infrastructure["infrastructure"]
    I["InMemoryResearchRepository"]
  end
  subgraph bootstrap["bootstrap"]
    B["create_app"]
  end

  B --> R
  B --> H
  B --> I
  R --> H
  R --> C
  R --> D
  H --> V
  H --> C
  H --> E
  H --> P
  H --> D
  V --> C
  I -.implements.-> P
  E --> P
```

Allowed dependencies: `presentation → application → domain ← infrastructure`.  
Forbidden: domain importing FastAPI/Pydantic HTTP models; application importing concrete repositories.

## 3. Sequence diagram

```mermaid
sequenceDiagram
  actor Client
  participant HTTP as presentation.router
  participant Handler as CreateResearchHandler
  participant Validator as CreateResearchValidator
  participant Entity as Research.create
  participant Repo as ResearchRepository

  Client->>HTTP: POST /api/research (CreateResearchRequest)
  HTTP->>Handler: handle(CreateResearchCommand)
  Handler->>Validator: validate(command)
  alt invalid
    Validator-->>Handler: ValidationError
    Handler-->>HTTP: raise
    HTTP-->>Client: 422
  else valid
    Handler->>Entity: create(...)
    Entity-->>Handler: Research(state=Draft)
    Handler->>Repo: save(research)
    Repo-->>Handler: Research
    Handler-->>HTTP: ResearchResponse
    HTTP-->>Client: 201 Created
  end
```

## 4. Test coverage checklist

| Layer | Case | Status |
|-------|------|--------|
| Domain | CreateResearch yields `Draft` | Covered |
| Domain | Blank title / objective / owner rejected | Covered |
| Application | Validator rejects oversized title | Covered |
| Application | Handler persists and maps DTO | Covered |
| Application | Invalid command never hits repository | Covered |
| Infrastructure | In-memory save/get used by handler & API | Covered (via handler/API) |
| Presentation | POST 201 happy path | Covered |
| Presentation | POST 422 empty title (Pydantic) | Covered |
| Presentation | POST 422 unknown fields (`extra=forbid`) | Covered |
| Out of scope | State transitions beyond Draft | Not in this slice |
| Out of scope | Postgres adapter | Stub only |

Run:

```bash
cd apps/api && python -m pytest -q
```

## 5. ADR notes

See [ADR-0005](../adr/ADR-0005-create-research-vertical-slice.md) and [ADR-0006](../adr/ADR-0006-research-initial-state-draft.md).
