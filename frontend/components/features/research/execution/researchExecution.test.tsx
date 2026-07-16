import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import ProvenanceBanner from "@/components/features/research/execution/ProvenanceBanner";
import OverviewSection, {
  type OverviewSectionLabels,
} from "@/components/features/research/OverviewSection";
import ValidationPendingPanel from "@/components/features/research/ValidationPendingPanel";
import LoadingState from "@/components/ui/LoadingState";
import {
  applyExecutionToExperiments,
  applyExecutionToResearch,
  HISTORICAL_DISCLAIMER,
  validationDisplayStatus,
} from "@/lib/applyResearchExecution";
import { CANONICAL_RESEARCH_ID, getMockResearchById } from "@/lib/mockResearchCatalog";
import { getMockExperiments } from "@/lib/mockExperimentCatalog";
import { getCanonicalResearchPackage } from "@/lib/canonicalMaCrossover";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import { ResearchExecutionApiError } from "@/lib/researchExecutionApi";

const SAMPLE_EXECUTION: ResearchExecutionResult = {
  research_id: CANONICAL_RESEARCH_ID,
  strategy: {
    type: "ma_crossover",
    short_window: 20,
    long_window: 60,
  },
  provenance: {
    provider: "yahoo",
    symbol: "SPY",
    source: "Yahoo Finance via yfinance",
    retrieved_at: "2026-07-13T12:00:00+00:00",
    requested_start: "2018-01-01",
    requested_end: null,
    actual_start: "2018-01-02",
    actual_end: "2024-12-31",
    interval: "1d",
    cache_hit: false,
    cache_stale: false,
    currency: "USD",
  },
  metrics: {
    total_return: 0.42,
    cagr: 0.05,
    annualized_volatility: 0.15,
    sharpe_ratio: 0.55,
    maximum_drawdown: -0.22,
    trade_count: 12,
    win_rate: 0.51,
    turnover: 12,
    total_transaction_costs: 0.012,
    observation_count: 1600,
    start_date: "2018-03-28",
    end_date: "2024-12-31",
  },
  benchmark_metrics: {
    total_return: 0.9,
    cagr: 0.09,
    annualized_volatility: 0.18,
    sharpe_ratio: 0.6,
    maximum_drawdown: -0.34,
    trade_count: 0,
    win_rate: null,
    turnover: 0,
    total_transaction_costs: 0,
    observation_count: 1600,
    start_date: "2018-03-28",
    end_date: "2024-12-31",
  },
  series: [],
  warnings: [],
  generated_at: "2026-07-13T12:01:00+00:00",
  supported_evidence: {
    historical_backtest: "completed",
    benchmark_comparison: "completed",
    out_of_sample: "not_started",
    parameter_sensitivity: "not_started",
    transaction_cost_review: "not_started",
    data_quality_review: "awaiting_engine",
    evaluation: "unavailable",
  },
};

const overviewLabels: OverviewSectionLabels = {
  briefTitle: "Research Brief",
  keyResultsTitle: "Key Results",
  guidedWorkflowTitle: "Guided workflow",
  conclusionTitle: "Research Conclusion",

  datasetPeriodLabel: "Dataset & period",
  strategyRuleLabel: "Strategy rule",
  evidenceStatusLabel: "Evidence",
  decisionStatusLabel: "Evaluation status",

  evidenceComplete: "Evidence complete",
  evidenceIncomplete: "Incomplete",
  evidencePending: "Not started",

  decisionPending: "Decision pending evidence and review.",
  evaluationCompleted: "Completed",
  evaluationIncomplete: "Incomplete",
  evaluationBlocked: "Blocked",

  coverageLabel: "Coverage",
  keyStrengthsLabel: "Key strengths",
  limitationLabel: "Known weaknesses",
  nextActionLabel: "Next actions",

  strategyTotalReturnLabel: "Strategy total return",
  benchmarkTotalReturnLabel: "Benchmark total return",
  maxDrawdownLabel: "Maximum drawdown",
  oosSharpeLabel: "Out-of-sample Sharpe ratio",

  keyResultsUnavailable: "Run the research to calculate historical evidence.",
  oosSharpeUnavailable:
    "Run validation to calculate out-of-sample Sharpe ratio.",

  stepRunResearch: "Run Research",
  stepValidateEvidence: "Validate evidence",
  stepReviewEvaluation: "Review evaluation",
  stepAskCopilot: "Ask Copilot",

  ctaRunResearch: "Run Research",
  ctaResearchLoading: "Research is running…",
  ctaRetryResearch: "Retry research",

  ctaRunValidation: "Run Validation",
  ctaRequestEvaluation: "Request Evaluation",
  ctaAskCopilot: "Ask Copilot",
};

describe("PR-008B research execution UI", () => {
  it("shows loading copy while waiting for backend evidence", () => {
    render(<LoadingState message="Loading research execution from backend…" />);
    expect(
      screen.getByText("Loading research execution from backend…")
    ).toBeInTheDocument();
  });

  it("renders extended provenance fields when present", () => {
    render(
      <ProvenanceBanner
        provenance={{
          ...SAMPLE_EXECUTION.provenance,
          asset_class: "etf",
          adjustment: "auto_adjust",
          canonical_symbol: "SPY",
        }}
        labels={{
          realData: "Real Historical Data",
          cached: "Cached",
          stale: "Stale cache",
          provider: "Provider",
          symbol: "Symbol",
          assetClass: "Asset class",
          adjustment: "Adjustment",
          range: "Actual date range",
          retrieved: "Retrieved",
          disclaimer: HISTORICAL_DISCLAIMER,
        }}
      />
    );

    expect(screen.getByText("etf")).toBeInTheDocument();
    expect(screen.getByText("auto_adjust")).toBeInTheDocument();
  });

  it("renders provenance labels and historical disclaimer", () => {
    render(
      <ProvenanceBanner
        provenance={SAMPLE_EXECUTION.provenance}
        labels={{
          realData: "Real Historical Data",
          cached: "Cached",
          stale: "Stale cache",
          provider: "Provider",
          symbol: "Symbol",
          range: "Actual date range",
          retrieved: "Retrieved",
          disclaimer: HISTORICAL_DISCLAIMER,
        }}
      />
    );

    expect(screen.getByText("Real Historical Data")).toBeInTheDocument();
    expect(screen.getByText("Yahoo Finance via yfinance")).toBeInTheDocument();
    expect(screen.getByText("SPY")).toBeInTheDocument();
    expect(screen.getByText(HISTORICAL_DISCLAIMER)).toBeInTheDocument();
  });

  it("renders successful calculated metrics without a confidence score", () => {
    const research = applyExecutionToResearch(
      getMockResearchById(CANONICAL_RESEARCH_ID)!,
      SAMPLE_EXECUTION
    );

    render(
      <OverviewSection
        language="en"
        research={research}
        executionStatus="ready"
        execution={SAMPLE_EXECUTION}
        validationStatus="idle"
        validation={null}
        evaluationStatus="idle"
        evaluation={null}
        provenanceSlot={
          <ProvenanceBanner
            provenance={SAMPLE_EXECUTION.provenance}
            labels={{
              realData: "Real Historical Data",
              cached: "Cached",
              stale: "Stale",
              provider: "Provider",
              symbol: "Symbol",
              range: "Range",
              retrieved: "Retrieved",
              disclaimer: HISTORICAL_DISCLAIMER,
            }}
          />
        }
        onRunResearch={() => void 0}
        onRunValidation={() => void 0}
        onRequestEvaluation={() => void 0}
        onAskCopilot={() => void 0}
        labels={overviewLabels}
      />
    );

    expect(screen.getByText("42.0%")).toBeInTheDocument();
    expect(screen.getByText("90.0%")).toBeInTheDocument();
    expect(screen.getByText("-22.0%")).toBeInTheDocument();
    expect(screen.getByText(overviewLabels.oosSharpeUnavailable)).toBeInTheDocument();
    expect(screen.queryByText(/Research Confidence:\s*\d/i)).not.toBeInTheDocument();
    expect(research.confidenceScore).toBeNull();
  });

  it("marks only historical and benchmark validation as completed", () => {
    const stages = getCanonicalResearchPackage().plannedValidationStages;
    const mapped = stages.map((stage) => ({
      id: stage.id,
      status: validationDisplayStatus(stage.id, SAMPLE_EXECUTION),
    }));
    expect(mapped).toEqual([
      { id: "val-historical", status: "completed" },
      { id: "val-benchmark", status: "completed" },
      { id: "val-oos", status: "not_started" },
      { id: "val-sensitivity", status: "not_started" },
      { id: "val-costs", status: "not_started" },
      { id: "val-quality", status: "awaiting_data" },
    ]);

    const { container } = render(
      <ValidationPendingPanel
        stages={stages}
        statusForStage={(stageId) => validationDisplayStatus(stageId, SAMPLE_EXECUTION)}
        labels={{
          title: "Validation",
          summary: "Supported evidence only",
          notStarted: "Not Started",
          awaitingData: "Awaiting Data",
          completed: "Completed",
          note: HISTORICAL_DISCLAIMER,
        }}
      />
    );

    const badges = Array.from(
      container.querySelectorAll(".validation-pending-panel__item .badge")
    ).map((el) => el.textContent);
    expect(badges).toEqual([
      "Completed",
      "Completed",
      "Not Started",
      "Not Started",
      "Not Started",
      "Awaiting Data",
    ]);
    expect(screen.getByText(HISTORICAL_DISCLAIMER)).toBeInTheDocument();
  });

  it("updates only the baseline experiment with real metrics", () => {
    const experiments = applyExecutionToExperiments(
      getMockExperiments(CANONICAL_RESEARCH_ID),
      SAMPLE_EXECUTION
    );
    const baseline = experiments.find((item) => item.id === "exp-ma-baseline");
    const oos = experiments.find((item) => item.id === "exp-ma-oos");

    expect(baseline?.status).toBe("Completed");
    expect(baseline?.metrics.sharpe).toBe(0.55);
    expect(oos?.status).toBe("Designed");
    expect(oos?.metrics.sharpe).toBeNull();
  });

  it("creates an execution-backed baseline for a local research definition", () => {
    const execution = {
      ...SAMPLE_EXECUTION,
      research_id: "research-local-demo",
      provenance: { ...SAMPLE_EXECUTION.provenance, symbol: "QQQ" },
      strategy: {
        ...SAMPLE_EXECUTION.strategy,
        short_window: 10,
        long_window: 50,
        transaction_cost: 0.002,
      },
    };

    const experiments = applyExecutionToExperiments([], execution);

    expect(experiments).toHaveLength(1);
    expect(experiments[0]).toMatchObject({
      researchId: "research-local-demo",
      name: "MA10/50 Baseline Backtest — Executed",
      status: "Completed",
      datasetOrSymbol: "QQQ",
      metrics: { sharpe: 0.55 },
    });
  });
});

describe("researchExecutionApi error path", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 502,
        json: async () => ({ detail: "Yahoo Finance unavailable" }),
      }))
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("surfaces backend/provider failure without fabricating values", async () => {
    const { fetchResearchExecution } = await import("@/lib/researchExecutionApi");
    await expect(fetchResearchExecution()).rejects.toBeInstanceOf(
      ResearchExecutionApiError
    );
    await expect(fetchResearchExecution()).rejects.toMatchObject({
      status: 502,
      message: "Yahoo Finance unavailable",
    });
  });
});
