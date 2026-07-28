# Roadmap

Capability-based status for the demonstrable Research Workspace.  
Full engineering epic tracker: [`../ROADMAP.md`](../ROADMAP.md).

## Completed milestones

| Milestone | Status | Notes |
| --- | --- | --- |
| Research Library | ✅ Done | Homepage entry for research projects |
| Validation | ✅ Done | Deterministic backend validation + workspace Validation tab |
| Robustness | ✅ Done | Reviews four implemented checks and separates unsupported methods as scope boundaries |
| Paper Observation | ✅ Done | Browser-local bounded plan, dated notes, and session completion |
| Decision | ✅ Done | Browser-local human outcome and rationale linked to evidence review |
| Archive | ✅ Done | Real action for browser-local research; no empty lifecycle tab |
| Research execution | ✅ Done | `POST /api/v1/research/execution` for canonical MA study |
| Evaluation summary | ✅ Done | `POST /api/v1/research/evaluation` (folded into Validation UX) |
| Evidence-grounded Copilot | ✅ Done | Requires backend LLM configuration |
| Multi-provider market data | ✅ Done | Yahoo global / AkShare A-shares routing |
| Demo experience / authenticity surfaces | ✅ Done | Demo banner, guided entry, authenticity tests |

## Product spine

```text
Research → Experiment → Validation → Robustness → Paper Observation → Decision
```

Archive is an action after review. Cross-browser durable archive records remain future work.

## Future work — Not implemented

State clearly as **Not implemented** unless a later PR lands:

| Item | Status |
| --- | --- |
| Phase 4 — Research Artifact & Intelligence Serving Layer | In progress |
| Phase 4.1 — Research Run Registry Foundation | ✅ Done (filesystem registry + immutable manifests; no API) |
| Phase 4.2 — Research Artifact Registry | ✅ Done (checksummed append-only artifacts; no API) |
| Phase 4.3 — Intelligence Snapshot Contracts | ✅ Done (ResearchSummary + Signal snapshots; no API/frontend) |
| Phase 4.3.1 — Registry concurrency / publish recovery | ✅ Done (run locks, idempotent publish, create-run cleanup) |
| Phase 4.4 — Deterministic Artifact-to-Snapshot Builders | ✅ Done (evidence contracts → typed snapshots; no API/frontend) |
| Phase 4.5 — Read-only Intelligence Query Layer | ✅ Done (IntelligenceService + `/api/v1/intelligence`; no write/Publisher/frontend) |
| Phase 4.6 — Frontend Consumption | Not implemented |
| Phase 5 — Portfolio Intelligence | Not implemented |
| Full stress / regime / Monte Carlo robustness engines | Not implemented (canonical trend fixed-parameter walk-forward is implemented) |
| Broker connectivity / live order routing | Not implemented |
| Autonomous trading agent | Not implemented |
| Cross-browser durable research definitions without localStorage | Not implemented (persistence slice pending) |
| Complete Decision Ledger / Decision Room as live governance products | Not implemented (routes may show honest placeholders) |
| Model Lab / deep learning training product | Not implemented |
| Production release automation / Dependabot matrix expansion | Not implemented |

## North star

A research operating system where a Strategy moves through an auditable lifecycle without becoming an execution platform. Architecture remains governed by the Project Bible and Architecture Bible.
