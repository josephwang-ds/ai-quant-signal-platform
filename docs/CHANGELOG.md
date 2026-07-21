# Changelog

Portfolio-facing summary of major milestones.  
Detailed PR history: [`../CHANGELOG.md`](../CHANGELOG.md).

This project has not published numbered semantic releases yet. Entries below are capability milestones under **Unreleased**.

## [Unreleased]

### Research Workspace spine

- Research Library homepage for project entry and lifecycle orientation
- Research Workspace tabs for Research, Experiment, Validation, Robustness, Paper Trading, Decision, and Archive
- Guided demo entry and portfolio demonstration banner

### Calculated evidence

- Research Execution for the canonical MA crossover study against live market data
- Deterministic Validation (OOS, sensitivity, cost, data quality)
- Evaluation summary over validation evidence (no recalculation)
- Evidence-grounded Research Copilot (OpenAI-compatible providers)

### Authenticity

- Removal of fabricated public-preview metrics
- Authenticity policy and regression tests
- Honest empty states when sessions, scores, or providers are unavailable

### Platform foundation

- Next.js frontend + FastAPI backend demonstrable runtime
- Multi-provider market-data routing (Yahoo / AkShare)
- Render + Vercel deployment path with documented environment contract
- Engineering foundation docs (Project Bible, Architecture Bible, ADRs, CI baseline)

### Management centers (presentation)

- Robustness Center — organises completed / pending / planned / blocked checks
- Paper Trading / Research Deployment Center — observation staging
- Decision Center — approval staging from existing evidence

---

For chronologically ordered PR notes (PR-001 onward), see the root [`CHANGELOG.md`](../CHANGELOG.md).
