# Demo Script

Interview and portfolio walkthrough for **AI Quant Research Workspace**.  
Canonical sample: **Trend Following Study** (`ma-crossover-spy`).

```text
Research Library
→ Trend Following Study
→ Experiment
→ Validation
→ Robustness
→ Paper Observation
→ Decision
```

---

## 30-second introduction

This is a research operating system for quantitative work — not a trading bot.

It keeps one lifecycle visible: Research → Experiment → Validation → Robustness → Paper Observation → Decision. Archive is a real action after the work is complete, not an empty stage.

Calculated metrics come from the backend. Empty states stay empty. There is no broker, no live execution, and no fabricated P&L.

---

## 3-minute walkthrough

1. **Research Library (`/`)** — Click **Start guided review**. Frame the product as one question, four proof points, and a human-owned decision.
2. **Question** — Show the falsifiable hypothesis and fixed protocol. Say: “This starts with a research question, not a stock recommendation.”
3. **Evidence** — Point at backend-derived OOS / sensitivity status. Say: “Deterministic checks run before AI explains evidence.”
4. **Challenge** — Show the four implemented robustness checks and the separate scope boundary. Say: “Unknowns remain visible, but unsupported methods do not masquerade as workflow tasks.”
5. **Decision** — Save a human outcome and rationale. Say: “The system supports judgment; it does not own approval or execute a trade.”

Close with: **Research First. AI Second. Decisions Last.**

---

## 60-second initiative answer

Use this when asked, “What was your contribution?” or “What makes this different?”

> I started by challenging the original product framing. Another signal dashboard would be easy to demo but hard to trust, so I reframed it as a research operating system. I introduced a clear evidence contract: the backend calculates metrics, deterministic rules validate them, AI can explain existing evidence, and a human retains the final decision. I also made incomplete states visible instead of polishing them away. Then I carried that product decision into the architecture, lifecycle UI, guided three-minute review, and cold-start recovery. The result is not just more functionality; it is a system whose claims can be inspected.

Anchor the answer in five visible initiatives:

1. **Product reframing** — signal dashboard → research decision workflow
2. **Evidence boundary** — backend facts → deterministic checks → optional AI explanation
3. **Honest state model** — Completed / Pending / Blocked evidence stays separate from unsupported methods
4. **Human governance** — analysis supports approval; it never owns approval or execution
5. **Delivery quality** — one guided review path and resilient cold-start behaviour for real demos

---

## 8-minute interview walkthrough

| Minute | Screen | What to say |
| --- | --- | --- |
| 0–1 | Library | Problem: research trails scatter. Product: one lifecycle workspace. Demo constraints: research only. |
| 1–2 | Overview | Canonical `ma-crossover-spy` protocol (SPY MA20/60). Spine tabs map to product stages. |
| 2–3 | Experiment | Historical execution against real market data via FastAPI. Browser does not invent metrics. |
| 3–4 | Validation | Deterministic checks. Show provenance (e.g. Yahoo). Evaluation summarises evidence; it is not a spine stage. |
| 4–5 | Robustness | What the four implemented checks prove, plus the explicit scope boundary. |
| 5–6 | Paper Observation | Create a bounded plan and add a dated human note. No fake fills or P&L. |
| 6–7 | Decision | Save the reviewer’s outcome and rationale. No generated approval. |
| 7–8 | Wrap | Architecture: Next.js + FastAPI + Vercel/Render. Trade-off: honesty over demo theatre. |

---

## Recommended click path

1. Open `/`
2. Click **Start guided review**
3. Use the guide CTA: **Question → Evidence → Challenge → Decision**
4. Exit the guide only when deeper inspection is requested
5. Open **Experiment** or **Paper Observation** as supporting detail—not as required stops

If the Render free tier is cold, hit `/health` first. Prefer one browser session when research definitions are localStorage-backed.

If the backend does not recover in time, switch to the [frontend-safe walkthrough](DEMO_MODE.md) and present the visible unavailable state as an intentional authenticity boundary.

---

## Key talking points

- Research OS, not a backtest dashboard or broker
- Canonical six-stage lifecycle
- Backend-computed evidence only
- AI (Copilot) explains evidence; it does not create truth
- Robustness organises real validation evidence; Paper and Decision persist human-authored browser-local records
- Portfolio demonstration banner states limits up front

---

## Difference from common portfolio projects

| Common demo pattern | What to show here |
| --- | --- |
| “Here is the strategy return” | “Here is the question, protocol, evidence, and decision trail” |
| One optimized backtest | OOS, sensitivity, cost, data quality, and explicit gaps |
| AI-generated recommendation | Deterministic evidence first; AI is a bounded explanation layer |
| Polished happy path | Planned, blocked, empty, and unavailable states remain honest |
| Feature-by-feature tour | Four-stop reviewer narrative: Question → Evidence → Challenge → Decision |

---

## Current limitations

- Research definitions may use browser-local persistence
- Regime, walk-forward, Monte Carlo, and capacity methods remain outside the implemented evidence boundary
- Paper Observation is a research log, not live execution
- No broker / OMS
- Validation run ids may be process-local on Render
- Copilot needs backend `LLM_*` config

---

## Likely interviewer questions

| Question | Straight answer |
| --- | --- |
| Is this live trading? | No. Research and paper observation only. |
| Where do metrics come from? | FastAPI research execution/validation against market data. |
| Why is Paper Observation empty? | No human has started a session yet; the reviewer can create a real bounded plan here. |
| What did you not build? | Brokers, OMS, full stress engines, durable multi-browser research store (still pending). |
| How is AI governed? | Copilot is evidence-grounded and cannot override validation. |
| What would you ship next? | Durable research persistence, then deeper robustness engines with the same honesty rules. |
