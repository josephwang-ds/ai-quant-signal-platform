# Stable Demo Modes

The workspace supports honest demo paths. Neither path fabricates returns, fills, model output, or paper-trading sessions.

Canonical routes (Phase 4 RC ✅ Complete):

| Route | Surface |
| --- | --- |
| `/` | Research Library (published intelligence runs) |
| `/platform` | Platform Overview |
| `/research/run_*` | Published Workspace (Overview / Signals / Evidence / Validation) |
| `/engine/research/*` | Active Workspace (catalog execution studies) |

## 1. Frontend-safe walkthrough

Use this path when the backend is unavailable or a portfolio review must start immediately.

```text
Research Library (/)
→ Platform Overview (/platform) when explaining product layers
→ Active Workspace Trend demo (/engine/research/ma-crossover-spy)
→ Review frozen protocol, lifecycle tabs, and honest unavailable states
```

What remains stable without the backend:

- Research Library empty / error / loading states (no invented published runs);
- canonical `ma-crossover-spy` research definition in Active Workspace;
- lifecycle navigation and research metadata;
- planned experiments, notebook context, and evidence boundaries;
- explicit unavailable states instead of generated metrics;
- responsive UI across the product routes.

Use this sentence in a walkthrough:

> The product shell and research protocol are local and deterministic. Calculated evidence is intentionally unavailable until the backend responds.

## 2. Full evidence walkthrough

Start both applications before the interview:

```bash
# Terminal 1
cd backend
source .venv/bin/activate
# Optional: dry-run then seed one PUBLISHED intelligence run for Library → Workspace
python scripts/seed_published_demo_run.py --dry-run
python scripts/seed_published_demo_run.py
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

Verify the backend before opening the product:

```bash
curl --fail http://127.0.0.1:8000/health
```

Then follow the published review spine (requires a seeded or otherwise published run):

```text
Research Library (/)
→ Open published run (/research/run_…)
→ Overview → Signals → Evidence → Validation
→ Back to Research Library
```

Separately, Active Workspace evidence remains:

```text
Platform (/platform) or Research Engine (/engine)
→ Trend Following Study (/engine/research/ma-crossover-spy)
→ Experiment → Validation → Robustness → Paper Trading → Decision
```

For a hosted Render backend, open the health endpoint first and wait for a successful response before the walkthrough. Keep one browser session because some research definitions use local browser persistence.

The frontend also starts a shared readiness check on first load. During a Render cold start it shows a bounded startup state, merges concurrent API callers behind one health request, and continues automatically when the backend becomes ready. A GitHub keep-warm schedule reduces cold starts but is not treated as a correctness dependency.

If scheduled warmup appears inactive, verify all three items:

- GitHub Actions is enabled and the `keep-warm` workflow is running on the default branch;
- repository variable `BACKEND_URL` points to the current Render service;
- Render free-instance hours have not been exhausted.

## Failure-safe presentation

If a provider or database is unavailable:

1. Do not refresh repeatedly or describe empty cards as results.
2. Point out the visible unavailable state and provenance boundary.
3. Continue with the frontend-safe walkthrough.
4. Use checked-in screenshots only as previously captured evidence, never as a claim that the current request succeeded.

## Screenshot refresh checklist

Refresh screenshots only after a successful full-evidence run:

- use the canonical `ma-crossover-spy` study for Active Workspace captures;
- optionally capture a seeded Published Workspace run for Library → Overview / Signals / Evidence / Validation;
- capture at a consistent desktop viewport;
- include provenance or evidence status where relevant;
- never edit numerical output into a screenshot;
- update the README caption when a screen or label changes;
- rerun frontend tests and the production build before committing images.

Recommended captures:

1. Research Library
2. Published Workspace Overview (when a published run is available)
3. Active Workspace Research Overview
4. Validation evidence
5. Robustness matrix
6. Paper Trading readiness
7. Decision review
8. Strategy Studio protocol
9. Model Comparison protocol
