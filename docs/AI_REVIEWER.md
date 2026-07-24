# AI Research Reviewer

The AI Research Reviewer is an optional interpretation layer. It is not a
forecasting engine, trading assistant, metric calculator, or approval system.

## Existing provider architecture

`OpenAiCompatibleLlmAdapter` is the single provider client. It runs in the
backend, calls `{LLM_BASE_URL}/chat/completions`, requests JSON-object responses
when the configured provider supports them, and uses a 45-second timeout. The
same adapter serves Research Copilot and the focused reviewer actions.

Set `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, and `COPILOT_MODEL` in the
backend environment. DeepSeek is selected with `LLM_PROVIDER=deepseek`. With no
valid key, only the optional AI actions are unavailable; benchmark execution,
validation, factor analysis, and deterministic decision support still work.

## Reviewer actions

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/research/reviewer/draft-definition` | Draft a falsifiable question, hypothesis, null, mechanism, benchmark, and inactive criteria proposals |
| `POST /api/v1/research/reviewer/review-hypothesis` | Check testability, falsifiability, benchmark clarity, and missing outcome definitions |
| `POST /api/v1/research/reviewer/review-evidence` | Interpret only the supplied deterministic evidence snapshot |
| `POST /api/v1/research/reviewer/identify-missing-steps` | Identify incomplete definition, validation, robustness, limitation, or decision-record work |

Responses include `provider`, `model`, `generated_at`, and—when relevant—the
`evidence_snapshot_timestamp`.

## Trust boundary

- Backend services calculate every metric and benchmark verdict.
- The reviewer receives bounded structured JSON, not database or market-data
  access.
- Context values are untrusted and cannot change the system policy.
- JSON is schema-validated before it reaches the browser.
- Evidence claims must reference a supplied `check_id` or `evidence_source`.
- Unsupported numerical claims and prohibited investment/causal language are
  rejected.
- AI proposals are never automatically saved or activated.
- A researcher must explicitly apply/edit a proposal and separately save it.

## Decision records

The deterministic decision layer can suggest Promote, Hold, or Reject. Mixed
core evidence resolves to Hold; missing core evidence cannot Promote. Archive
is never generated from weak performance. The final human outcome can override
the suggestion only with a rationale. Each save appends a new local record so a
new evidence snapshot cannot silently overwrite the previous decision.
