# Demo Script

Interview and portfolio walkthrough for **AI Quant Research Workspace**.  
Canonical sample: **Trend Following Study** (`ma-crossover-spy`).

```text
Research Library
→ Trend Following Study
→ Experiment
→ Validation
→ Robustness
→ Paper Trading
→ Decision
```

---

## 30-second introduction

This is a research operating system for quantitative work — not a trading bot.

It keeps one lifecycle visible: Research → Experiment → Validation → Robustness → Paper Trading → Decision → Archive.

Calculated metrics come from the backend. Empty states stay empty. There is no broker, no live execution, and no fabricated P&L.

---

## 3-minute walkthrough

1. **Research Library (`/`)** — Show the product framing and guided entry. Open the sample research.
2. **Overview** — Research question, lifecycle progress, next action (e.g. Run Validation when execution exists).
3. **Validation** — Point at backend-derived OOS / sensitivity status. Note Incomplete vs Completed honestly.
4. **Robustness** — Management view of completed / pending / planned / blocked checks — not a fake stress engine.
5. **Paper Trading** — Observation staging; session stays empty unless a real session exists.
6. **Decision** — Approval staging from existing evidence only.

Close with: authenticity first — the demo proves process integrity, not invented performance.

---

## 8-minute interview walkthrough

| Minute | Screen | What to say |
| --- | --- | --- |
| 0–1 | Library | Problem: research trails scatter. Product: one lifecycle workspace. Demo constraints: research only. |
| 1–2 | Overview | Canonical `ma-crossover-spy` protocol (SPY MA20/60). Spine tabs map to product stages. |
| 2–3 | Experiment | Historical execution against real market data via FastAPI. Browser does not invent metrics. |
| 3–4 | Validation | Deterministic checks. Show provenance (e.g. Yahoo). Evaluation summarises evidence; it is not a spine stage. |
| 4–5 | Robustness | What is done vs planned. Stress/regime items stay Planned until implemented. |
| 5–6 | Paper Trading | Deployment readiness / observation plan. No fake fills. |
| 6–7 | Decision | Checklist and risks from existing coverage. No invented Approved/Rejected. |
| 7–8 | Wrap | Architecture: Next.js + FastAPI + Vercel/Render. Trade-off: honesty over demo theatre. |

---

## Recommended click path

1. Open `/`
2. Click **Continue the sample research** (or **Current Research**)
3. Tab **Experiment** (optional if metrics already projected)
4. Tab **Validation**
5. Tab **Robustness**
6. Tab **Paper Trading**
7. Tab **Decision**
8. Optionally mention **Archive** as close-out stage

If the Render free tier is cold, hit `/health` first. Prefer one browser session when research definitions are localStorage-backed.

---

## Key talking points

- Research OS, not a backtest dashboard or broker
- Canonical seven-stage lifecycle
- Backend-computed evidence only
- AI (Copilot) explains evidence; it does not create truth
- Robustness / Paper / Decision centers organise state — they do not invent engines or sessions
- Portfolio demonstration banner states limits up front

---

## Current limitations

- Research definitions may use browser-local persistence
- Some robustness methods remain Planned
- Paper Trading is observation staging, not live execution
- No broker / OMS
- Validation run ids may be process-local on Render
- Copilot needs backend `LLM_*` config

---

## Likely interviewer questions

| Question | Straight answer |
| --- | --- |
| Is this live trading? | No. Research and paper observation only. |
| Where do metrics come from? | FastAPI research execution/validation against market data. |
| Why empty Paper Trading? | No real session yet — we refuse to fabricate one. |
| What did you not build? | Brokers, OMS, full stress engines, durable multi-browser research store (still pending). |
| How is AI governed? | Copilot is evidence-grounded and cannot override validation. |
| What would you ship next? | Durable research persistence, then deeper robustness engines with the same honesty rules. |
