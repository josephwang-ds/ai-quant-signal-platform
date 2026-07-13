/**
 * Research Evaluation mock 目录。
 *
 * TODO(backend): GET /api/research/{id}/evaluation
 * TODO(engine): Research Confidence 由确定性 Evaluation Engine 计算，禁止 AI 改写。
 */

import {
  EVALUATION_DIMENSION_WEIGHTS,
  type EvaluationDimension,
  type EvaluationSnapshot,
} from "@/types/evaluation";
import type { ResearchTimelineEvent } from "@/types/notebook";
import {
  assertRecommendationMatchesRules,
  buildPaperTradingRuleChecks,
  computeResearchConfidence,
  deriveDecisionReadiness,
} from "@/lib/researchEvaluation";

function dim(
  partial: Omit<EvaluationDimension, "weight"> & { key: EvaluationDimension["key"] }
): EvaluationDimension {
  return {
    ...partial,
    weight: EVALUATION_DIMENSION_WEIGHTS[partial.key],
  };
}

const MOMENTUM_DIMENSIONS: EvaluationDimension[] = [
  dim({
    key: "historical_backtest_quality",
    name: "Historical Backtest Quality",
    score: 98,
    status: "Strong",
    evidenceRefs: ["ev-mom-bt", "val-mom-hist", "exp-mom-001"],
    evidenceLinks: [
      {
        id: "el-hist-1",
        claim: "Historical backtest quality is strong",
        evidenceRef: "ev-mom-bt",
        detail: "IS net Sharpe 0.78; 214 trades; ValidationPassed on frozen protocol.",
      },
    ],
    limitations: ["Single cost assumption in historical package"],
    blocking: false,
    lastUpdatedAt: "2026-04-02T11:20:00.000Z",
    summary: "Frozen MA 20/60 historical package meets declared gates.",
  }),
  dim({
    key: "out_of_sample_performance",
    name: "Out-of-Sample Performance",
    score: 88,
    status: "Acceptable",
    evidenceRefs: ["ev-mom-oos", "val-mom-oos", "exp-mom-005"],
    evidenceLinks: [
      {
        id: "el-oos-1",
        claim: "Out-of-sample performance is acceptable",
        evidenceRef: "ev-mom-oos",
        detail:
          "OOS Sharpe 0.51 on folds 1–3; date range 2022-01-01 → 2025-06-30 (partial); experiment exp-mom-005.",
      },
    ],
    limitations: ["Walk-forward coverage 3/5 folds"],
    blocking: false,
    lastUpdatedAt: "2026-06-20T16:45:00.000Z",
    summary: "Positive OOS Sharpe with incomplete fold coverage.",
  }),
  dim({
    key: "parameter_stability",
    name: "Parameter Stability",
    score: 94,
    status: "Strong",
    evidenceRefs: ["ev-mom-sens", "val-mom-sens", "exp-mom-002"],
    evidenceLinks: [
      {
        id: "el-sens-1",
        claim: "Stable across nearby parameter values",
        evidenceRef: "ev-mom-sens",
        detail: "Neighbor Sharpe band ±0.09 within ±0.15 policy.",
      },
    ],
    limitations: ["Local grid only"],
    blocking: false,
    lastUpdatedAt: "2026-05-02T13:40:00.000Z",
    summary: "Lookback/MA neighbors remain inside stability band.",
  }),
  dim({
    key: "stress_test_resilience",
    name: "Stress-Test Resilience",
    score: 45,
    status: "Failed",
    evidenceRefs: ["ev-mom-stress", "val-mom-stress"],
    evidenceLinks: [
      {
        id: "el-stress-1",
        claim: "Stress resilience failed",
        evidenceRef: "ev-mom-stress",
        detail:
          "Observed stress DD −22.4% vs threshold −20% on 2020 path; ValidationFailed.",
      },
    ],
    limitations: ["Liquidity overlay coarse"],
    blocking: true,
    lastUpdatedAt: "2026-07-05T10:00:00.000Z",
    summary: "Crisis path exceeds drawdown guardrail.",
  }),
  dim({
    key: "transaction_cost_resilience",
    name: "Transaction-Cost Resilience",
    score: 84,
    status: "Acceptable",
    evidenceRefs: ["exp-mom-004", "val-mom-cost"],
    evidenceLinks: [
      {
        id: "el-cost-1",
        claim: "Transaction costs remain manageable",
        evidenceRef: "exp-mom-004",
        detail: "Net Sharpe ~0.52 at 12 bps; break-even ~15 bps.",
      },
    ],
    limitations: ["Constant bps model"],
    blocking: false,
    lastUpdatedAt: "2026-05-15T17:00:00.000Z",
    summary: "Cost stress retains positive expectancy at 12 bps.",
  }),
  dim({
    key: "risk_review",
    name: "Risk Review",
    score: 55,
    status: "Weak",
    evidenceRefs: ["ev-mom-stress", "val-mom-stress"],
    evidenceLinks: [
      {
        id: "el-risk-1",
        claim: "Risk review remains weak pending stress remediation",
        evidenceRef: "ev-mom-stress",
        detail: "Drawdown guardrail breach blocks risk approval path.",
      },
    ],
    limitations: ["No independent risk sign-off while stress Failed"],
    blocking: true,
    lastUpdatedAt: "2026-07-06T09:00:00.000Z",
    summary: "Risk posture blocked by stress guardrail failure.",
  }),
  dim({
    key: "trade_statistics",
    name: "Trade Statistics",
    score: 92,
    status: "Strong",
    evidenceRefs: ["ev-mom-bt"],
    evidenceLinks: [
      {
        id: "el-trades-1",
        claim: "Sufficient trade count",
        evidenceRef: "ev-mom-bt",
        detail: "214 historical trades above minimum gate of 100.",
      },
    ],
    limitations: ["OOS trade count thinner (89)"],
    blocking: false,
    lastUpdatedAt: "2026-04-02T11:20:00.000Z",
    summary: "Trade count and turnover support statistical review.",
  }),
  dim({
    key: "data_quality",
    name: "Data Quality",
    score: 96,
    status: "Strong",
    evidenceRefs: ["ev-mom-data", "val-mom-data"],
    evidenceLinks: [
      {
        id: "el-dq-1",
        claim: "Primary panel data confidence is strong",
        evidenceRef: "ev-mom-data",
        detail: "Medium-high dataset confidence; provenance reviewed.",
      },
    ],
    limitations: ["Crowding proxy remains heuristic"],
    blocking: false,
    lastUpdatedAt: "2026-07-01T08:00:00.000Z",
    summary: "MarketDataset confidence acceptable for evaluation inputs.",
  }),
  dim({
    key: "experiment_coverage",
    name: "Experiment Coverage",
    score: 82,
    status: "Acceptable",
    evidenceRefs: ["exp-mom-001", "exp-mom-002", "exp-mom-005", "exp-mom-006"],
    evidenceLinks: [
      {
        id: "el-exp-1",
        claim: "Core experiment battery covers baseline, sensitivity, and OOS",
        evidenceRef: "exp-mom-001",
        detail: "Baseline + sensitivity + OOS experiments linked; regime still inconclusive.",
      },
    ],
    limitations: ["Limited multi-asset validation"],
    blocking: false,
    lastUpdatedAt: "2026-06-30T12:00:00.000Z",
    summary: "Experiment set covers primary claims with regime gap.",
  }),
  dim({
    key: "evidence_traceability",
    name: "Evidence Traceability",
    score: 92,
    status: "Strong",
    evidenceRefs: ["ev-mom-bt", "ev-mom-oos", "ev-mom-stress", "nb-mom-005"],
    evidenceLinks: [
      {
        id: "el-trace-1",
        claim: "Evaluation conclusions link to ValidationRun and Evidence IDs",
        evidenceRef: "ev-mom-bt",
        detail: "Notebook and validation artifacts cross-referenced for major claims.",
      },
    ],
    limitations: ["Some regime notes lack pinned taxonomy ID"],
    blocking: false,
    lastUpdatedAt: "2026-07-06T10:00:00.000Z",
    summary: "Evidence graph covers mandatory evaluation claims.",
  }),
];

function buildMomentumSnapshot(): EvaluationSnapshot {
  const confidenceScore = computeResearchConfidence(MOMENTUM_DIMENSIONS);
  const base: EvaluationSnapshot = {
    researchId: "rs-momentum-001",
    evaluationId: "eval-mom-003",
    status: "Completed",
    evaluatedAt: "2026-07-06T10:30:00.000Z",
    lifecycleStage: "Review",
    dataConfidence: "high",
    researchHealth: "Blocked",
    dimensions: MOMENTUM_DIMENSIONS,
    issues: [
      {
        id: "iss-mom-stress",
        kind: "blocker",
        severity: "critical",
        sourceDimensionKey: "stress_test_resilience",
        sourceDimensionName: "Stress-Test Resilience",
        reason: "Stress-test drawdown exceeds guardrail (−22.4% vs −20%).",
        evidenceRef: "ev-mom-stress",
        requiredNextAction:
          "Redesign downside-risk control and rerun stress ValidationRun.",
        owner: "A. Chen",
        dueAt: "2026-07-20T00:00:00.000Z",
      },
      {
        id: "iss-mom-risk",
        kind: "blocker",
        severity: "critical",
        sourceDimensionKey: "risk_review",
        sourceDimensionName: "Risk Review",
        reason: "Risk review cannot approve while stress guardrail is failed.",
        evidenceRef: "ev-mom-stress",
        requiredNextAction: "Clear stress blocker before requesting risk approval.",
        owner: "Risk Desk (demo)",
        dueAt: "2026-07-22T00:00:00.000Z",
      },
      {
        id: "iss-mom-oos",
        kind: "warning",
        severity: "warning",
        sourceDimensionKey: "out_of_sample_performance",
        sourceDimensionName: "Out-of-Sample Performance",
        reason: "Walk-forward coverage incomplete (3/5 folds).",
        evidenceRef: "ev-mom-oos",
        requiredNextAction: "Complete remaining OOS folds after universe freeze.",
        owner: "A. Chen",
        dueAt: "2026-08-01T00:00:00.000Z",
      },
      {
        id: "iss-mom-regime",
        kind: "missing_evidence",
        severity: "info",
        sourceDimensionKey: "experiment_coverage",
        sourceDimensionName: "Experiment Coverage",
        reason: "Regime analysis remains inconclusive — taxonomy not pinned.",
        evidenceRef: "exp-mom-006",
        requiredNextAction: "Pin one published regime definition, then reassess.",
        owner: "A. Chen",
        dueAt: null,
      },
    ],
    strengthsWeaknesses: [
      {
        id: "sw-s1",
        kind: "strength",
        text: "Stable across nearby parameter values",
        sourceDimensionKey: "parameter_stability",
        evidenceRef: "ev-mom-sens",
      },
      {
        id: "sw-s2",
        kind: "strength",
        text: "Positive out-of-sample performance",
        sourceDimensionKey: "out_of_sample_performance",
        evidenceRef: "ev-mom-oos",
      },
      {
        id: "sw-s3",
        kind: "strength",
        text: "Sufficient trade count",
        sourceDimensionKey: "trade_statistics",
        evidenceRef: "ev-mom-bt",
      },
      {
        id: "sw-s4",
        kind: "strength",
        text: "Transaction costs remain manageable",
        sourceDimensionKey: "transaction_cost_resilience",
        evidenceRef: "exp-mom-004",
      },
      {
        id: "sw-w1",
        kind: "weakness",
        text: "Stress drawdown exceeds guardrail",
        sourceDimensionKey: "stress_test_resilience",
        evidenceRef: "ev-mom-stress",
      },
      {
        id: "sw-w2",
        kind: "weakness",
        text: "Performance weak in sideways regimes",
        sourceDimensionKey: "experiment_coverage",
        evidenceRef: "exp-mom-006",
      },
      {
        id: "sw-w3",
        kind: "weakness",
        text: "Limited multi-asset validation",
        sourceDimensionKey: "experiment_coverage",
        evidenceRef: "exp-mom-001",
      },
      {
        id: "sw-w4",
        kind: "weakness",
        text: "Short monitoring history",
        sourceDimensionKey: "risk_review",
        evidenceRef: "ev-mom-stress",
      },
    ],
    recommendation: {
      recommendation: "Continue Validation",
      why: "Mandatory stress resilience failed; Research Confidence remains below paper-trading threshold.",
      blockingConditions: [
        "Stress-test drawdown exceeds guardrail",
        "Risk review not approved",
      ],
      requiredNextActions: [
        "Redesign downside-risk control",
        "Rerun stress ValidationRun",
        "Re-request Evaluation after stress passes",
      ],
      eligibleNextTransition: "Remain in Review → re-enter Validation",
      reviewOwner: "A. Chen",
      reassessmentAt: "2026-07-20T00:00:00.000Z",
      ruleChecks: [],
    },
    history: [
      {
        id: "hist-mom-1",
        evaluatedAt: "2026-06-01T12:00:00.000Z",
        confidenceScore: 82,
        recommendation: "Continue Validation",
        mainChange: "Baseline Evaluation after partial OOS",
        trigger: "EvaluationRequested",
        superseded: true,
      },
      {
        id: "hist-mom-2",
        evaluatedAt: "2026-07-06T10:30:00.000Z",
        confidenceScore,
        recommendation: "Continue Validation",
        mainChange: `82 → ${confidenceScore}: stress test failed`,
        trigger: "EvaluationCompleted",
        superseded: false,
      },
    ],
    evidenceCoveragePct: 88,
    hasValidationData: true,
    superseded: false,
  };

  const readiness = deriveDecisionReadiness(base, confidenceScore);
  base.recommendation.recommendation = readiness;
  base.recommendation.ruleChecks = buildPaperTradingRuleChecks(
    base,
    confidenceScore
  );
  base.researchHealth =
    readiness === "Continue Validation" ? "Blocked" : base.researchHealth;

  // Keep recommendation aligned with deterministic rules.
  void assertRecommendationMatchesRules(base);
  return base;
}

const RSI_DIMENSIONS: EvaluationDimension[] = [
  dim({
    key: "historical_backtest_quality",
    name: "Historical Backtest Quality",
    score: 80,
    status: "Acceptable",
    evidenceRefs: ["ev-rsi-bt"],
    evidenceLinks: [
      {
        id: "el-rsi-hist",
        claim: "Historical package acceptable",
        evidenceRef: "ev-rsi-bt",
        detail: "Prototype backtest on S&P 100 sleeve.",
      },
    ],
    limitations: ["Earnings filter incomplete"],
    blocking: false,
    lastUpdatedAt: "2026-06-15T10:00:00.000Z",
    summary: "Acceptable historical baseline with calendar gap.",
  }),
  dim({
    key: "out_of_sample_performance",
    name: "Out-of-Sample Performance",
    score: 78,
    status: "Acceptable",
    evidenceRefs: ["ev-rsi-oos", "val-rsi-oos"],
    evidenceLinks: [
      {
        id: "el-rsi-oos",
        claim: "OOS Sharpe barely meets threshold",
        evidenceRef: "ev-rsi-oos",
        detail: "OOS Sharpe 0.41; thin 2022 sample.",
      },
    ],
    limitations: ["Thin high-vol subsample"],
    blocking: false,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "OOS passed with limitations.",
  }),
  dim({
    key: "stress_test_resilience",
    name: "Stress-Test Resilience",
    score: 0,
    status: "Missing",
    evidenceRefs: [],
    evidenceLinks: [],
    limitations: ["Stress ValidationRun not started"],
    blocking: true,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "Missing — blocked on earnings calendar join.",
  }),
  dim({
    key: "parameter_stability",
    name: "Parameter Stability",
    score: 70,
    status: "Acceptable",
    evidenceRefs: ["exp-rsi-001"],
    evidenceLinks: [],
    limitations: ["Narrow grid"],
    blocking: false,
    lastUpdatedAt: "2026-06-20T10:00:00.000Z",
    summary: "Limited sensitivity package.",
  }),
  dim({
    key: "transaction_cost_resilience",
    name: "Transaction-Cost Resilience",
    score: 72,
    status: "Acceptable",
    evidenceRefs: ["exp-rsi-001"],
    evidenceLinks: [],
    limitations: [],
    blocking: false,
    lastUpdatedAt: "2026-06-20T10:00:00.000Z",
    summary: "Preliminary cost check only.",
  }),
  dim({
    key: "risk_review",
    name: "Risk Review",
    score: 40,
    status: "Weak",
    evidenceRefs: [],
    evidenceLinks: [],
    limitations: ["Cannot approve without stress"],
    blocking: true,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "Blocked pending stress package.",
  }),
  dim({
    key: "trade_statistics",
    name: "Trade Statistics",
    score: 68,
    status: "Acceptable",
    evidenceRefs: ["ev-rsi-oos"],
    evidenceLinks: [],
    limitations: [],
    blocking: false,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "Trade counts adequate for prototype.",
  }),
  dim({
    key: "data_quality",
    name: "Data Quality",
    score: 45,
    status: "Weak",
    evidenceRefs: [],
    evidenceLinks: [],
    limitations: ["Earnings calendar join incomplete"],
    blocking: true,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "Dataset confidence degraded for stress inputs.",
  }),
  dim({
    key: "experiment_coverage",
    name: "Experiment Coverage",
    score: 60,
    status: "Weak",
    evidenceRefs: ["exp-rsi-001"],
    evidenceLinks: [],
    limitations: [],
    blocking: false,
    lastUpdatedAt: "2026-06-20T10:00:00.000Z",
    summary: "Sparse experiment set.",
  }),
  dim({
    key: "evidence_traceability",
    name: "Evidence Traceability",
    score: 65,
    status: "Acceptable",
    evidenceRefs: ["ev-rsi-oos"],
    evidenceLinks: [],
    limitations: [],
    blocking: false,
    lastUpdatedAt: "2026-07-01T15:30:00.000Z",
    summary: "Partial evidence graph.",
  }),
];

function buildRsiSnapshot(): EvaluationSnapshot {
  const confidenceScore = computeResearchConfidence(RSI_DIMENSIONS);
  const base: EvaluationSnapshot = {
    researchId: "rs-rsi-002",
    evaluationId: "eval-rsi-001",
    status: "Blocked",
    evaluatedAt: "2026-07-02T09:00:00.000Z",
    lifecycleStage: "Running",
    dataConfidence: "degraded",
    researchHealth: "Blocked",
    dimensions: RSI_DIMENSIONS,
    issues: [
      {
        id: "iss-rsi-cal",
        kind: "blocker",
        severity: "critical",
        sourceDimensionKey: "data_quality",
        sourceDimensionName: "Data Quality",
        reason: "Dataset confidence degraded — earnings calendar join incomplete.",
        evidenceRef: "val-rsi-stress",
        requiredNextAction: "Complete calendar alignment before stress ValidationRun.",
        owner: "M. Okonkwo",
        dueAt: "2026-07-18T00:00:00.000Z",
      },
      {
        id: "iss-rsi-stress",
        kind: "missing_evidence",
        severity: "warning",
        sourceDimensionKey: "stress_test_resilience",
        sourceDimensionName: "Stress-Test Resilience",
        reason: "Stress validation package missing.",
        evidenceRef: "val-rsi-stress",
        requiredNextAction: "Prepare stress ValidationRun after data join.",
        owner: "M. Okonkwo",
        dueAt: null,
      },
    ],
    strengthsWeaknesses: [
      {
        id: "sw-rsi-s1",
        kind: "strength",
        text: "Positive out-of-sample performance",
        sourceDimensionKey: "out_of_sample_performance",
        evidenceRef: "ev-rsi-oos",
      },
      {
        id: "sw-rsi-w1",
        kind: "weakness",
        text: "Stress package missing",
        sourceDimensionKey: "stress_test_resilience",
        evidenceRef: "val-rsi-stress",
      },
    ],
    recommendation: {
      recommendation: "Rework Required",
      why: "Data confidence degraded and mandatory stress evidence is missing.",
      blockingConditions: ["Degraded data confidence", "Missing stress package"],
      requiredNextActions: [
        "Repair earnings calendar join",
        "Run stress ValidationRun",
      ],
      eligibleNextTransition: "Remain in Running → Validation",
      reviewOwner: "M. Okonkwo",
      reassessmentAt: "2026-07-18T00:00:00.000Z",
      ruleChecks: [],
    },
    history: [
      {
        id: "hist-rsi-1",
        evaluatedAt: "2026-07-02T09:00:00.000Z",
        confidenceScore,
        recommendation: "Rework Required",
        mainChange: "Initial Evaluation blocked on data join",
        trigger: "EvaluationCompleted",
        superseded: false,
      },
    ],
    evidenceCoveragePct: 42,
    hasValidationData: true,
    superseded: false,
  };

  const readiness = deriveDecisionReadiness(base, confidenceScore);
  base.recommendation.recommendation = readiness;
  base.recommendation.ruleChecks = buildPaperTradingRuleChecks(
    base,
    confidenceScore
  );
  return base;
}

function buildPairsSnapshot(): EvaluationSnapshot {
  const dimensions: EvaluationDimension[] = [
    dim({
      key: "historical_backtest_quality",
      name: "Historical Backtest Quality",
      score: 94,
      status: "Strong",
      evidenceRefs: ["ev-pairs-bt"],
      evidenceLinks: [
        {
          id: "el-pairs-hist",
          claim: "Historical pairs package strong",
          evidenceRef: "ev-pairs-bt",
          detail: "Net Sharpe 0.92 on holdout package (demo).",
        },
      ],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Strong historical quality.",
    }),
    dim({
      key: "out_of_sample_performance",
      name: "Out-of-Sample Performance",
      score: 90,
      status: "Strong",
      evidenceRefs: ["ev-pairs-oos"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "OOS passed.",
    }),
    dim({
      key: "parameter_stability",
      name: "Parameter Stability",
      score: 88,
      status: "Strong",
      evidenceRefs: ["ev-pairs-sens"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Stable cointegration window.",
    }),
    dim({
      key: "stress_test_resilience",
      name: "Stress-Test Resilience",
      score: 86,
      status: "Strong",
      evidenceRefs: ["ev-pairs-stress"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Stress within guardrail.",
    }),
    dim({
      key: "transaction_cost_resilience",
      name: "Transaction-Cost Resilience",
      score: 85,
      status: "Strong",
      evidenceRefs: ["ev-pairs-bt"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Costs contained.",
    }),
    dim({
      key: "risk_review",
      name: "Risk Review",
      score: 87,
      status: "Strong",
      evidenceRefs: ["ev-pairs-stress"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-16T09:00:00.000Z",
      summary: "Risk review approved (demo).",
    }),
    dim({
      key: "trade_statistics",
      name: "Trade Statistics",
      score: 84,
      status: "Acceptable",
      evidenceRefs: ["ev-pairs-bt"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Trade stats adequate.",
    }),
    dim({
      key: "data_quality",
      name: "Data Quality",
      score: 90,
      status: "Strong",
      evidenceRefs: ["ev-pairs-data"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "High data confidence.",
    }),
    dim({
      key: "experiment_coverage",
      name: "Experiment Coverage",
      score: 86,
      status: "Strong",
      evidenceRefs: ["exp-pairs-001"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Coverage complete for demo package.",
    }),
    dim({
      key: "evidence_traceability",
      name: "Evidence Traceability",
      score: 88,
      status: "Strong",
      evidenceRefs: ["ev-pairs-bt", "ev-pairs-oos"],
      evidenceLinks: [],
      limitations: [],
      blocking: false,
      lastUpdatedAt: "2026-06-15T11:00:00.000Z",
      summary: "Traceable evidence set.",
    }),
  ];

  const confidenceScore = computeResearchConfidence(dimensions);
  const base: EvaluationSnapshot = {
    researchId: "rs-pairs-003",
    evaluationId: "eval-pairs-002",
    status: "Completed",
    evaluatedAt: "2026-06-16T10:00:00.000Z",
    lifecycleStage: "Validated",
    dataConfidence: "high",
    researchHealth: "Healthy",
    dimensions,
    issues: [],
    strengthsWeaknesses: [
      {
        id: "sw-pairs-s1",
        kind: "strength",
        text: "Positive out-of-sample performance",
        sourceDimensionKey: "out_of_sample_performance",
        evidenceRef: "ev-pairs-oos",
      },
      {
        id: "sw-pairs-s2",
        kind: "strength",
        text: "Stress drawdown within guardrail",
        sourceDimensionKey: "stress_test_resilience",
        evidenceRef: "ev-pairs-stress",
      },
    ],
    recommendation: {
      recommendation: "Ready for Paper Trading",
      why: "All paper-trading readiness rules passed on demo Evaluation.",
      blockingConditions: [],
      requiredNextActions: ["Request governed Paper Trading admission (deferred)"],
      eligibleNextTransition: "Validated → Paper Trading (governed)",
      reviewOwner: "S. Patel",
      reassessmentAt: "2026-09-16T00:00:00.000Z",
      ruleChecks: [],
    },
    history: [
      {
        id: "hist-pairs-1",
        evaluatedAt: "2026-06-16T10:00:00.000Z",
        confidenceScore,
        recommendation: "Ready for Paper Trading",
        mainChange: "EvaluationCompleted — ready state",
        trigger: "EvaluationCompleted",
        superseded: false,
      },
    ],
    evidenceCoveragePct: 95,
    hasValidationData: true,
    superseded: false,
  };

  const readiness = deriveDecisionReadiness(base, confidenceScore);
  base.recommendation.recommendation = readiness;
  base.recommendation.ruleChecks = buildPaperTradingRuleChecks(
    base,
    confidenceScore
  );
  base.researchHealth =
    readiness === "Ready for Paper Trading" ? "Healthy" : "Watch";
  return base;
}

export const MOCK_EVALUATION_BY_RESEARCH: Record<string, EvaluationSnapshot> = {
  "rs-momentum-001": buildMomentumSnapshot(),
  "rs-rsi-002": buildRsiSnapshot(),
  "rs-pairs-003": buildPairsSnapshot(),
};

function cloneSnapshot(snapshot: EvaluationSnapshot): EvaluationSnapshot {
  return {
    ...snapshot,
    dimensions: snapshot.dimensions.map((dimension) => ({
      ...dimension,
      evidenceRefs: [...dimension.evidenceRefs],
      evidenceLinks: dimension.evidenceLinks.map((link) => ({ ...link })),
      limitations: [...dimension.limitations],
    })),
    issues: snapshot.issues.map((issue) => ({ ...issue })),
    strengthsWeaknesses: snapshot.strengthsWeaknesses.map((item) => ({
      ...item,
    })),
    recommendation: {
      ...snapshot.recommendation,
      blockingConditions: [...snapshot.recommendation.blockingConditions],
      requiredNextActions: [...snapshot.recommendation.requiredNextActions],
      ruleChecks: snapshot.recommendation.ruleChecks.map((rule) => ({
        ...rule,
      })),
    },
    history: snapshot.history.map((item) => ({ ...item })),
  };
}

export function getMockEvaluation(
  researchId: string
): EvaluationSnapshot | null {
  const found = MOCK_EVALUATION_BY_RESEARCH[researchId];
  return found ? cloneSnapshot(found) : null;
}

/** Empty / missing-validation payload for researches without Evaluation mock. */
export function getEmptyEvaluation(researchId: string): EvaluationSnapshot {
  return {
    researchId,
    evaluationId: `eval-empty-${researchId}`,
    status: "Missing Validation",
    evaluatedAt: null,
    lifecycleStage: "Draft",
    dataConfidence: "low",
    researchHealth: "Degraded",
    dimensions: [],
    issues: [
      {
        id: `iss-empty-${researchId}`,
        kind: "missing_evidence",
        severity: "warning",
        sourceDimensionKey: null,
        sourceDimensionName: "Validation",
        reason: "No Evaluation package — validation data missing for this research.",
        evidenceRef: "—",
        requiredNextAction: "Complete Validation pipeline before Evaluation.",
        owner: "Unassigned",
        dueAt: null,
      },
    ],
    strengthsWeaknesses: [],
    recommendation: {
      recommendation: "Continue Research",
      why: "Evaluation requires a Validation package.",
      blockingConditions: ["Missing validation data"],
      requiredNextActions: ["Run Validation stages", "Request Evaluation"],
      eligibleNextTransition: "Draft / Running → Validation",
      reviewOwner: "Unassigned",
      reassessmentAt: "—",
      ruleChecks: [],
    },
    history: [],
    evidenceCoveragePct: 0,
    hasValidationData: false,
    superseded: false,
  };
}

export function getMockEvaluationTimelineEvents(
  researchId: string
): ResearchTimelineEvent[] {
  const snapshot = getMockEvaluation(researchId);
  if (!snapshot || !snapshot.evaluatedAt) {
    return [];
  }

  const events: ResearchTimelineEvent[] = [
    {
      id: `tl-eval-req-${snapshot.evaluationId}`,
      researchId,
      occurredAt: snapshot.evaluatedAt,
      title: "EvaluationRequested",
      summary: "Evaluation package requested for governed readiness review.",
      kind: "evaluation",
      sourceEntryId: snapshot.evaluationId,
    },
    {
      id: `tl-eval-done-${snapshot.evaluationId}`,
      researchId,
      occurredAt: snapshot.evaluatedAt,
      title: "EvaluationCompleted",
      summary: `Research Confidence ${computeResearchConfidence(snapshot.dimensions)}; ${snapshot.recommendation.recommendation}.`,
      kind: "evaluation",
      sourceEntryId: snapshot.evaluationId,
    },
    {
      id: `tl-eval-conf-${snapshot.evaluationId}`,
      researchId,
      occurredAt: snapshot.evaluatedAt,
      title: "ResearchConfidenceUpdated",
      summary: `Confidence updated to ${computeResearchConfidence(snapshot.dimensions)} (demo calculation).`,
      kind: "evaluation",
      sourceEntryId: snapshot.evaluationId,
    },
  ];

  const superseded = snapshot.history.filter((item) => item.superseded);
  for (const item of superseded) {
    events.push({
      id: `tl-eval-sup-${item.id}`,
      researchId,
      occurredAt: item.evaluatedAt,
      title: "EvaluationSuperseded",
      summary: item.mainChange,
      kind: "evaluation",
      sourceEntryId: item.id,
    });
  }

  if (snapshot.recommendation.recommendation === "Rework Required") {
    events.push({
      id: `tl-eval-rework-${snapshot.evaluationId}`,
      researchId,
      occurredAt: snapshot.evaluatedAt,
      title: "ReworkRequested",
      summary: snapshot.recommendation.why,
      kind: "evaluation",
      sourceEntryId: snapshot.evaluationId,
    });
  }

  return events;
}

export class MockEvaluationError extends Error {
  constructor(message = "Unable to load evaluation.") {
    super(message);
    this.name = "MockEvaluationError";
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function shouldForceMockError(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return new URLSearchParams(window.location.search).get("mockError") === "1";
}

export async function loadMockEvaluation(
  researchId: string,
  options?: { delayMs?: number }
): Promise<EvaluationSnapshot> {
  await delay(options?.delayMs ?? 360);
  if (shouldForceMockError()) {
    throw new MockEvaluationError(
      "Mock evaluation load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockEvaluation(researchId) ?? getEmptyEvaluation(researchId);
}
