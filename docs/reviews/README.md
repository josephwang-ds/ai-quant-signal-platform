# Release and AI Audits

Read-only audit reports for portfolio release readiness. These documents record findings at a point in time; they do not change runtime behavior.

| Report | Purpose |
|---|---|
| RC-1 Repository Audit | Initial audit (referenced in `CHANGELOG.md` and `docs/data/AUTHENTICITY_POLICY.md`) that identified P0 blockers: fabricated public evidence, production API localhost fallback, and missing CI. |
| [RC-2 Release Candidate Audit](RC-2-RELEASE-CANDIDATE-AUDIT.md) | Verified remediation PRs #10–#12 and PR #13 on merged `main`; confirmed CI on the default branch, distinguished local sandbox failures from authoritative CI results, and signed off **Portfolio v1.1 Ready**. |
| [AI Grounding and Demo Audit](AI-GROUNDING-DEMO-AUDIT.md) | Post-merge audit of the Research Copilot: answer-specific `citation_ids`, safety checks, no runtime fake LLM, honest provider-unavailable behavior, and demo readiness. |

**Reading order:** RC-1 (blockers) → RC-2 (release sign-off) → AI Grounding (Copilot layer).
