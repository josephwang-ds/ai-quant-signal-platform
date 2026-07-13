import type { TranslationKey } from "@/lib/i18n";

/** 管理层驾驶舱六宫格模块定义（模拟决策支持数据） */
export type CockpitTile = {
  id: string;
  href: string;
  titleKey: TranslationKey;
  descKey: TranslationKey;
};

export const EXECUTIVE_COCKPIT_TILES: CockpitTile[] = [
  {
    id: "executive-cockpit",
    href: "/",
    titleKey: "executiveCockpit",
    descKey: "executiveCockpitTileDesc",
  },
  {
    id: "strategy-health-score",
    href: "/strategy-health-score",
    titleKey: "strategyHealthScore",
    descKey: "moduleStrategyHealthScoreOverviewDesc",
  },
  {
    id: "return-quality-lens",
    href: "/return-quality-lens",
    titleKey: "returnQualityLens",
    descKey: "moduleReturnQualityLensOverviewDesc",
  },
  {
    id: "risk-gate-review",
    href: "/risk-gate-review",
    titleKey: "riskGateReview",
    descKey: "moduleRiskGateReviewOverviewDesc",
  },
  {
    id: "scenario-shock-test",
    href: "/scenario-shock-test",
    titleKey: "scenarioShockTest",
    descKey: "moduleScenarioShockTestOverviewDesc",
  },
  {
    id: "decision-ledger",
    href: "/decision-ledger",
    titleKey: "decisionLedger",
    descKey: "moduleDecisionLedgerOverviewDesc",
  },
];

/** 驾驶舱顶部快照（模拟数据，仅供决策支持演示） */
export type CockpitSnapshot = {
  portfolioNav: number;
  ytdReturnPct: number;
  maxDrawdownPct: number;
  sharpeRatio: number;
  riskLevel: number;
  healthScore: number;
};

export const MOCK_COCKPIT_SNAPSHOT: CockpitSnapshot = {
  portfolioNav: 1_042_800,
  ytdReturnPct: 4.28,
  maxDrawdownPct: -8.6,
  sharpeRatio: 1.12,
  riskLevel: 2,
  healthScore: 76,
};

/** 收益质量透视指标（模拟数据） */
export type ReturnQualityMetrics = {
  totalReturn: number;
  benchmarkReturn: number;
  excessReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  costDrag: number;
  hitRate: number;
  profitFactor: number;
  capitalAtRisk: number;
  drawdownBufferToRed: number;
};

export const returnQualityMetrics: ReturnQualityMetrics = {
  totalReturn: 0.1428,
  benchmarkReturn: 0.1182,
  excessReturn: 0.0246,
  maxDrawdown: -0.086,
  sharpeRatio: 1.12,
  costDrag: 0.018,
  hitRate: 0.58,
  profitFactor: 1.34,
  capitalAtRisk: 42_500,
  drawdownBufferToRed: 0.034,
};

/** 风控闸口审查三段式流程（模拟数据） */
export type RiskGateReviewFlow = {
  strategySignal: {
    rawSignal: string;
    strategy: string;
    confidence: string;
  };
  riskGate: {
    riskLevel: string;
    gateDecision: string;
    reasons: string[];
  };
  finalAction: {
    action: string;
    note: string;
  };
};

export const riskGateReviewFlow: RiskGateReviewFlow = {
  strategySignal: {
    rawSignal: "BUY",
    strategy: "Momentum",
    confidence: "Medium",
  },
  riskGate: {
    riskLevel: "Yellow",
    gateDecision: "Downgraded to WATCH",
    reasons: [
      "Current drawdown reached -6.4%",
      "Volatility above normal range",
      "Recent simulated trades underperformed",
      "Signal conflicts with short-term market regime",
    ],
  },
  finalAction: {
    action: "HOLD ONLY",
    note: "No new simulated position",
  },
};

/** 情景冲击测试场景（模拟数据） */
export type ScenarioShockScenario = {
  id: string;
  title: string;
  navImpact: string;
  riskLevelAfter: string;
  triggeredRules: string[];
  systemAction: string;
  managementInterpretation: string;
};

export const scenarioShockScenarios: ScenarioShockScenario[] = [
  {
    id: "single-day-drop",
    title: "Single-day market drop -5%",
    navImpact: "-4.1%",
    riskLevelAfter: "Yellow",
    triggeredRules: [
      "Drawdown threshold crossed at -6.4%",
      "Intraday volatility spike detected",
    ],
    systemAction: "Restrict new simulated positions; maintain existing paper exposure only",
    managementInterpretation:
      "A one-day shock is contained but moves the session into cautious governance. Review whether simulated adds should resume after stabilization.",
  },
  {
    id: "five-day-selloff",
    title: "5-day market selloff",
    navImpact: "-7.8%",
    riskLevelAfter: "Orange",
    triggeredRules: [
      "Multi-day drawdown acceleration",
      "Rolling Sharpe deterioration",
      "Risk gate downgrade triggered",
    ],
    systemAction: "Suspend simulated adds; flag portfolio for leadership review",
    managementInterpretation:
      "Persistent selloff stress tests capital buffer and governance patience. Treat as a risk预案 checkpoint, not a forecast of further losses.",
  },
  {
    id: "volatility-doubles",
    title: "Volatility doubles",
    navImpact: "-2.3%",
    riskLevelAfter: "Yellow",
    triggeredRules: [
      "Volatility regime shift above baseline",
      "Position sizing guardrail activated",
    ],
    systemAction: "Reduce simulated position change frequency; widen watch thresholds",
    managementInterpretation:
      "Higher volatility raises execution drag in paper mode. Emphasize risk-adjusted quality over headline return during the shock window.",
  },
  {
    id: "cost-triples",
    title: "Transaction cost triples",
    navImpact: "-1.6%",
    riskLevelAfter: "Light Yellow",
    triggeredRules: [
      "Cost drag ratio exceeds governance limit",
      "Turnover efficiency warning",
    ],
    systemAction: "Throttle simulated rebalance frequency; require cost-aware review",
    managementInterpretation:
      "Cost shocks erode simulated edge faster than price moves alone. Useful for testing whether the strategy remains viable under frictions.",
  },
  {
    id: "three-losing-trades",
    title: "3 consecutive losing trades",
    navImpact: "-3.5%",
    riskLevelAfter: "Orange",
    triggeredRules: [
      "Consecutive loss counter reached 3",
      "Cooldown window recommended",
      "Signal confidence downgraded",
    ],
    systemAction: "Enter simulated cooldown; block new entries until review",
    managementInterpretation:
      "Loss streaks test discipline more than single-day marks. The ledger should capture why the gate paused paper follow-through.",
  },
];

/** 决策留痕台账条目（模拟数据） */
export type DecisionLedgerEntry = {
  id: string;
  date: string;
  symbol: string;
  strategy: string;
  rawSignal: string;
  riskLevel: string;
  gateDecision: string;
  finalPaperAction: string;
  explanation: string;
  humanNote: string;
  outcome: string;
};

export const decisionLedgerEntries: DecisionLedgerEntry[] = [
  {
    id: "ledger-2026-07-01",
    date: "2026-07-01",
    symbol: "AAPL",
    strategy: "Momentum",
    rawSignal: "BUY",
    riskLevel: "Yellow",
    gateDecision: "Downgraded to WATCH",
    finalPaperAction: "HOLD ONLY",
    explanation:
      "Drawdown reached -6.4% while volatility expanded. Gate blocked a new simulated entry despite a positive momentum signal.",
    humanNote:
      "Reviewer: pause adds until weekly risk review. Document rationale for audit.",
    outcome:
      "No simulated position change. Session flagged for accountability follow-up in next governance meeting.",
  },
  {
    id: "ledger-2026-06-28",
    date: "2026-06-28",
    symbol: "MSFT",
    strategy: "MA Crossover",
    rawSignal: "SELL",
    riskLevel: "Green",
    gateDecision: "Approved with caution",
    finalPaperAction: "REDUCE",
    explanation:
      "Signal and risk gate aligned. Simulated reduction allowed to align paper exposure with rule exit.",
    humanNote: "Reviewer: acceptable de-risk; confirm cost impact in ledger.",
    outcome:
      "Simulated exposure reduced. Outcome logged for post-review comparison against benchmark.",
  },
  {
    id: "ledger-2026-06-24",
    date: "2026-06-24",
    symbol: "NVDA",
    strategy: "Combined Signal",
    rawSignal: "BUY",
    riskLevel: "Orange",
    gateDecision: "Blocked — cooldown active",
    finalPaperAction: "NO ACTION",
    explanation:
      "Three consecutive simulated losses triggered cooldown. Human override was not requested.",
    humanNote:
      "Reviewer: uphold gate decision. Do not treat raw signal as an execution instruction.",
    outcome:
      "Gate decision upheld. Accountability record shows human-in-the-loop confirmation.",
  },
  {
    id: "ledger-2026-06-20",
    date: "2026-06-20",
    symbol: "AAPL",
    strategy: "Momentum",
    rawSignal: "BUY",
    riskLevel: "Light Yellow",
    gateDecision: "Approved — size capped",
    finalPaperAction: "ADD (capped)",
    explanation:
      "Risk-adjusted approval with position cap after cost-drag review. Not a full-conviction simulated add.",
    humanNote: "Reviewer: cap reflects governance limit, not strategy conviction score.",
    outcome:
      "Capped simulated add executed. Follow-up: monitor drawdown buffer vs red level for 5 sessions.",
  },
  {
    id: "ledger-2026-06-15",
    date: "2026-06-15",
    symbol: "SPY",
    strategy: "MA Crossover",
    rawSignal: "WAIT",
    riskLevel: "Green",
    gateDecision: "No gate intervention",
    finalPaperAction: "MAINTAIN",
    explanation:
      "No actionable signal change. Ledger entry created for traceability even when no simulated action occurs.",
    humanNote: "Reviewer: routine watch — document that inaction is also a governed decision.",
    outcome:
      "Maintained simulated posture. Audit trail complete for quarterly review sample.",
  },
];

/** 策略决策室 — 信号快照（模拟数据） */
export type DecisionRoomSignalSnapshot = {
  symbol: string;
  strategy: string;
  rawSignal: string;
  riskLevel: string;
  gateDecision: string;
  finalPaperAction: string;
  strategyHealthScore: number;
};

export const decisionRoomSignalSnapshot: DecisionRoomSignalSnapshot = {
  symbol: "SPY",
  strategy: "Momentum",
  rawSignal: "BUY",
  riskLevel: "Yellow",
  gateDecision: "Downgraded to WATCH",
  finalPaperAction: "HOLD ONLY",
  strategyHealthScore: 76,
};

/** 策略决策室 — 三角色解释（mock，非 LLM） */
export type DecisionRoomRole = {
  id: string;
  title: string;
  explanation: string;
};

export const decisionRoomRoles: DecisionRoomRole[] = [
  {
    id: "strategy-analyst",
    title: "Strategy Analyst",
    explanation:
      "Momentum on SPY is positive over the lookback window, producing a raw BUY. Confidence is medium because trend strength is intact but not accelerating. This is a rule output only — not an execution instruction.",
  },
  {
    id: "risk-officer",
    title: "Risk Officer",
    explanation:
      "Composite risk is Yellow (L3): drawdown near -6.4% and volatility above baseline. Policy restricts new simulated positions. Gate downgrades the session to WATCH and maps final paper action to HOLD ONLY.",
  },
  {
    id: "cfo-view",
    title: "CFO View",
    explanation:
      "From a governance lens, return quality is acceptable but drawdown buffer to Red is narrowing. Strategy Health Score 76/100 supports continued monitoring, not aggressive simulated adds. Human review should confirm before any cooldown release.",
  },
];

/** 策略决策室 — 模拟 RAG 检索片段 */
export type RetrievedRiskContext = {
  id: string;
  source: string;
  text: string;
};

export const decisionRoomRetrievedContext: RetrievedRiskContext[] = [
  {
    id: "ctx-risk-policy",
    source: "Risk Policy",
    text: "Level 3 Yellow restricts new simulated positions.",
  },
  {
    id: "ctx-decision-policy",
    source: "Decision Policy",
    text: "Raw signal must pass Risk Gate Review before any paper action.",
  },
  {
    id: "ctx-metric-glossary",
    source: "Metric Glossary",
    text: "Max Drawdown measures the largest peak-to-trough decline.",
  },
];

/** 策略决策室 — 复盘问题 */
export const decisionRoomReviewQuestions: string[] = [
  "Did the next 3-day return confirm the signal?",
  "Did volatility normalize?",
  "Did risk level return to Green or Light Yellow?",
];
