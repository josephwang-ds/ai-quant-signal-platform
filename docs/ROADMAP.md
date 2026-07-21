# Roadmap

Capability-based status for the demonstrable Research Workspace.  
Full engineering epic tracker: [`../ROADMAP.md`](../ROADMAP.md).

## Completed milestones

| Milestone | Status | Notes |
| --- | --- | --- |
| Research Library | ✅ Done | Homepage entry for research projects |
| Validation | ✅ Done | Deterministic backend validation + workspace Validation tab |
| Robustness | ✅ Done | Robustness Center organises evidence-backed status (not a new stress engine) |
| Paper Trading | ✅ Done | Research Deployment / observation staging UI |
| Decision | ✅ Done | Decision Center approval staging from existing evidence |
| Research execution | ✅ Done | `POST /api/v1/research/execution` for canonical MA study |
| Evaluation summary | ✅ Done | `POST /api/v1/research/evaluation` (folded into Validation UX) |
| Evidence-grounded Copilot | ✅ Done | Requires backend LLM configuration |
| Multi-provider market data | ✅ Done | Yahoo global / AkShare A-shares routing |
| Demo experience / authenticity surfaces | ✅ Done | Demo banner, guided entry, authenticity tests |

## Product spine

```text
Research → Experiment → Validation → Robustness → Paper Trading → Decision → Archive
```

Archive UI exists as a lifecycle tab; durable archive workflows remain limited where marked deferred in the workspace.

## Future work — Not implemented

State clearly as **Not implemented** unless a later PR lands:

| Item | Status |
| --- | --- |
| Full stress / regime / Monte Carlo robustness engines | Not implemented |
| Broker connectivity / live order routing | Not implemented |
| Autonomous trading agent | Not implemented |
| Cross-browser durable research definitions without localStorage | Not implemented (persistence slice pending) |
| Complete Decision Ledger / Decision Room as live governance products | Not implemented (routes may show honest placeholders) |
| Model Lab / deep learning training product | Not implemented |
| Production release automation / Dependabot matrix expansion | Not implemented |

## North star

A research operating system where a Strategy moves through an auditable lifecycle without becoming an execution platform. Architecture remains governed by the Project Bible and Architecture Bible.
