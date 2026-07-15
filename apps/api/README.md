# apps/api — target modular-monolith reference

This tree hosts the **target** FastAPI modular monolith. It is not yet the deployed production entrypoint (`backend/` remains the Render runtime until an approved cutover).

## Purpose

- Encode vertical-slice conventions (`domain` / `application` / `infrastructure` / `presentation`)
- Host reference use cases such as Research / CreateResearch
- Provide a clean composition root for future migration

## Dependencies

| File | Role |
|---|---|
| `requirements.txt` | Runtime deps for the reference API (FastAPI, Pydantic, Uvicorn) |
| `requirements-dev.txt` | Test deps (pytest, httpx) |

Install into a dedicated virtualenv (do not assume `backend/.venv`):

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Entrypoint

| Concern | Path |
|---|---|
| Composition root | `src/bootstrap/create_app.py` → `create_app()` |
| ASGI app factory | `create_app()` returns a FastAPI instance with injected handlers |
| Research HTTP adapter | `src/modules/research/presentation/router.py` |

Run a local server (reference only):

```bash
cd apps/api
source .venv/bin/activate
export PYTHONPATH=src
uvicorn bootstrap.create_app:create_app --factory --reload --port 8001
```

Default Research create endpoint: `POST http://127.0.0.1:8001/api/research`

## Development commands

```bash
# From apps/api with PYTHONPATH configured via pytest.ini
cd apps/api
source .venv/bin/activate
python -m pytest -q
```

`pytest.ini` sets `pythonpath = src` and `testpaths = tests`. These offline
unit and integration tests are required in GitHub Actions CI independently from
the legacy `backend/` suite.

## Relationship to `backend/`

| Path | Status |
|---|---|
| `backend/` | Current deployed runtime |
| `apps/api/` | Target modular structure; migrate capability-by-capability |

Do not delete or replace `backend/` until parity tests and an accepted cutover ADR exist.

## TODO (migration)

- Mount approved routers into the production composition root
- Replace in-memory stubs with persistence adapters
- Align dependency manifests with a monorepo packaging strategy when justified
