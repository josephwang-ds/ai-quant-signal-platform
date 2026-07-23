# Stable Demo Modes

The workspace supports two honest demo paths. Neither path fabricates returns, fills, model output, or paper-trading sessions.

## 1. Frontend-safe walkthrough

Use this path when the backend is unavailable or a portfolio review must start immediately.

```text
Research Library
→ Open Trend Following Study
→ Review the frozen protocol and lifecycle
→ Inspect honest loading / unavailable / planned states
→ Open Robustness, Paper Trading, and Decision governance views
```

What remains stable without the backend:

- canonical `ma-crossover-spy` research definition;
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
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

Verify the backend before opening the product:

```bash
curl --fail http://127.0.0.1:8000/health
```

Then follow:

```text
Research Library
→ Trend Following Study
→ Experiment
→ Validation
→ Robustness
→ Paper Trading
→ Decision
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

- use the canonical `ma-crossover-spy` study;
- capture at a consistent desktop viewport;
- include provenance or evidence status where relevant;
- never edit numerical output into a screenshot;
- update the README caption when a screen or label changes;
- rerun frontend tests and the production build before committing images.

Recommended captures:

1. Research Library
2. Research Overview
3. Validation evidence
4. Robustness matrix
5. Paper Trading readiness
6. Decision review
7. Strategy Studio protocol
8. Model Comparison protocol
