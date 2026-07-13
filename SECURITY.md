# Security Policy

Security reports are welcome and should be handled privately, responsibly, and without exposing users, deployments, credentials, or research data.

## Supported versions

The project has not published a stable release series. Security fixes currently target the default branch.

| Version | Supported |
|---|---|
| Default branch (`main`) | Yes |
| Historical commits, forks, and private modifications | No |
| Unreleased roadmap capabilities | Not applicable |

This policy will move to release-based support windows when versioned releases begin.

## Reporting a vulnerability

Do not open a public issue, pull request, discussion, or social-media post for a suspected vulnerability.

Preferred reporting path:

1. Use GitHub’s **Report a vulnerability** option on the repository’s Security tab if private vulnerability reporting is available.
2. If it is unavailable, contact [@josephwang-ds](https://github.com/josephwang-ds) through a private contact method listed on the maintainer’s GitHub profile.
3. If no private channel is available, open a public issue containing only a request for confidential contact. Do not include vulnerability details.

Include, when possible:

- affected revision, component, route, or dependency;
- vulnerability class and realistic impact;
- prerequisites and minimal reproduction steps;
- proof-of-concept material with secrets and private data removed;
- known mitigations or workarounds; and
- whether the issue has been disclosed elsewhere.

## Response targets

These are good-faith targets, not contractual guarantees:

| Stage | Target |
|---|---|
| Acknowledge receipt | 3 business days |
| Initial triage | 7 business days |
| Progress update | At least every 14 days while active |
| Remediation and disclosure | Based on severity, complexity, and deployment risk |

The maintainer will validate the report, establish severity and affected scope, coordinate remediation, and agree on disclosure timing. Credit will be offered unless the reporter prefers anonymity or the report is not actionable.

## Coordinated disclosure

Please allow a reasonable remediation period before public disclosure. Avoid accessing data you do not own, degrading services, persisting access, social engineering, or testing third-party systems without authorization.

After a fix is available, the project may publish a security advisory describing affected versions, impact, remediation, and reporter credit. Sensitive exploit details may be delayed when disclosure would create disproportionate risk.

## Security scope

Reports are especially valuable for:

- authentication or authorization bypass;
- credential, secret, or private-data exposure;
- injection, unsafe deserialization, path traversal, SSRF, or remote execution;
- cross-site scripting, request forgery, or insecure browser boundaries;
- dependency or supply-chain compromise;
- unsafe handling of market, portfolio, research, or audit data;
- agent or LLM pathways that bypass Application use cases, deterministic guardrails, or authorization; and
- deployment or configuration defaults that create a practical security risk.

The following are generally not security vulnerabilities unless they create a concrete exploit:

- incorrect investment conclusions or simulated performance;
- missing product features or roadmap capabilities;
- rate limits or availability of free third-party data providers;
- vulnerabilities that affect only obsolete dependencies with no reachable path; and
- automated scanner output without evidence of impact.

## Secrets and sensitive data

Never commit API keys, database URLs, tokens, private datasets, portfolio information, or unredacted logs. Revoke and rotate exposed credentials immediately; removing them from the latest commit is not sufficient because Git history and caches may retain them.

## Safe-harbor intent

Good-faith research that follows this policy, avoids privacy violations and service disruption, and reports findings promptly will be treated as authorized project security research to the extent the repository owner can grant that authorization.

