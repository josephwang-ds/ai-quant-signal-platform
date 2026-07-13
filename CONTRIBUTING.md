# Contributing to AI Quant Research Workspace

Thank you for helping build a rigorous research operating system. Contributions are welcome when they preserve the product constitution: research first, evidence before conclusions, deterministic governance, and AI as an assistant rather than an authority.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities through [SECURITY.md](SECURITY.md), not a public issue.

## Before you begin

Read, in order:

1. [Project Bible](docs/PROJECT_BIBLE.md)
2. Relevant [Architecture Bible](docs/Architecture-Bible/) chapter
3. [Project Structure](PROJECT_STRUCTURE.md)
4. Relevant accepted [ADRs](docs/adr/)
5. [Development Workflow](DEVELOPMENT_WORKFLOW.md)

For substantial work, open or link an issue that states the problem, bounded context, acceptance criteria, and non-goals.

## Choose the right issue type

| Issue form | Use it for |
|---|---|
| Bug report | reproducible behavior that differs from an expected contract |
| Feature request | a focused new product or engineering outcome |
| Epic | a measurable outcome requiring multiple sequenced stories |
| Story | one independently reviewable result within an epic or context |

Do not report security vulnerabilities through an issue form. Search existing issues before creating a new one, and remove credentials, private datasets, portfolio details, and sensitive logs.

## Development workflow

1. **Orient:** inspect the current worktree and authoritative documents.
2. **Scope:** choose one bounded outcome and identify its owning context.
3. **Decide:** write an ADR first if the change alters an accepted architectural decision.
4. **Implement:** deliver the smallest complete vertical slice; preserve unrelated behavior.
5. **Verify:** run focused tests, then the broader checks affected by the change.
6. **Document:** update contracts, diagrams, migration notes, and operator guidance.
7. **Review:** submit a focused PR with evidence and known risks.
8. **Merge:** use protected-branch checks and a review from an appropriate owner.

The repository’s pull request template is required. Complete every applicable section and write “Not applicable” with a reason instead of deleting risk, architecture, or verification prompts.

## Branch naming

Use lowercase kebab-case:

| Purpose | Pattern | Example |
|---|---|---|
| Product capability | `feature/<context>-<outcome>` | `feature/research-close-workflow` |
| Defect | `fix/<area>-<problem>` | `fix/validation-expiry-guard` |
| Documentation | `docs/<topic>` | `docs/contributor-foundation` |
| Refactoring | `refactor/<area>-<intent>` | `refactor/market-provider-port` |
| Tests | `test/<area>-<coverage>` | `test/research-transitions` |
| Maintenance | `chore/<topic>` | `chore/python-tooling` |

Automation-created branches may use the tool’s required prefix, such as `codex/`, followed by the same descriptive form.

## Commit guidance

- Keep commits coherent and reviewable.
- Use an imperative subject that describes the outcome.
- Explain why in the body when the rationale is not obvious.
- Do not mix formatting sweeps, generated assets, or unrelated fixes into a behavioral change.
- Never commit credentials, private datasets, local environments, or build caches.

## Architecture review process

Architecture review is required when a change:

- creates or changes a bounded context, aggregate, state, invariant, or domain event;
- changes dependency direction or introduces a new cross-context dependency;
- adds a database, queue, cache, provider, agent authority, or deployment unit;
- changes a public contract or data-retention model; or
- supersedes an accepted ADR.

The proposal must include context, decision, alternatives, consequences, migration, rollback, and compliance checks. Add a new ADR; do not rewrite accepted history. Small implementation choices within an accepted decision do not require an ADR.

## Pull request checklist

### Scope and architecture

- [ ] The PR has one clear outcome and names its bounded context.
- [ ] Product constitution and frozen architecture remain intact.
- [ ] Domain, Application, Infrastructure, and Presentation responsibilities are respected.
- [ ] Cross-context access uses a contract or event, not internal imports.
- [ ] Planned work is not described as implemented.

### Quality

- [ ] Tests cover success, failure, and relevant state/invariant paths.
- [ ] Formatting, lint, type, test, and build checks pass where applicable.
- [ ] External I/O, time, and randomness are controlled in tests.
- [ ] Errors are intentional and logs contain no secrets or sensitive research data.
- [ ] Accessibility and bilingual behavior were checked for UI changes.

### Documentation and operations

- [ ] Documentation and diagrams match the change.
- [ ] An ADR is included when architecture changed.
- [ ] Migration, compatibility, observability, and rollback are addressed.
- [ ] The PR description lists exact verification commands and results.

## Definition of Done

Done means the acceptance criteria are met, architecture remains compliant, appropriate automated and manual checks pass, documentation is current, risks are visible, and the change is safe to review, operate, migrate, and reverse. The full definition is maintained in the [Project Bible](docs/PROJECT_BIBLE.md#definition-of-done).

## Review principles

Review the most consequential concerns first: correctness, domain integrity, data/evidence provenance, security, failure behavior, and operability. Style feedback should reference an established rule. Ask for smaller follow-up work when it is independently valuable; do not expand a PR without a clear reason.

## Reporting security issues

Do not open a public issue containing credentials, exploitable details, private data, or sensitive deployment information. Follow the private reporting and coordinated-disclosure process in [SECURITY.md](SECURITY.md).
