import { describe, expect, it } from "vitest";
import { buildPaperTradingCenterModel } from "@/lib/researchPaperTrading";
import { getMockResearchById, CANONICAL_RESEARCH_ID } from "@/lib/mockResearchCatalog";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

function baseValidation(
  overrides: Partial<ResearchValidationResult> = {}
): ResearchValidationResult {
  return {
    research_id: "ma-crossover-spy",
    strategy: {},
    provenance: {
      provider: "yahoo",
      symbol: "SPY",
      source: "Yahoo Finance",
      retrieved_at: "2026-07-14T00:00:00Z",
      requested_start: "2010-01-01",
      requested_end: null,
      actual_start: "2010-01-01",
      actual_end: "2026-07-01",
      interval: "1d",
      cache_hit: false,
      cache_stale: false,
      currency: "USD",
    },
    validation_status: "incomplete",
    evidence_complete: false,
    stages: [
      {
        stage: "parameter_sensitivity",
        label: "Parameter sensitivity",
        status: "completed",
        summary: "ok",
        evidence: {},
        rules: [],
        warnings: [],
        blockers: [],
        generated_at: null,
        provenance: null,
      },
      {
        stage: "benchmark_comparison",
        label: "Benchmark comparison",
        status: "completed",
        summary: "ok",
        evidence: {},
        rules: [],
        warnings: [],
        blockers: [],
        generated_at: null,
        provenance: null,
      },
      {
        stage: "transaction_cost_sensitivity",
        label: "Transaction-cost sensitivity",
        status: "completed",
        summary: "ok",
        evidence: {},
        rules: [],
        warnings: [],
        blockers: [],
        generated_at: null,
        provenance: null,
      },
      {
        stage: "data_quality",
        label: "Data quality",
        status: "incomplete",
        summary: "pending",
        evidence: {},
        rules: [],
        warnings: [],
        blockers: [],
        generated_at: null,
        provenance: null,
      },
    ],
    oos: {
      status: "incomplete",
      split_date: null,
      in_sample_ratio: null,
      minimum_oos_observations: null,
      in_sample_metrics: null,
      out_of_sample_metrics: null,
      oos_benchmark_metrics: null,
      in_sample_observation_count: null,
      out_of_sample_observation_count: null,
      warnings: [],
      boundary_convention: null,
    },
    parameter_sensitivity: {
      status: "completed",
      results: [],
      valid_combination_count: null,
      profitable_combination_count: null,
      positive_sharpe_count: null,
      median_sharpe: null,
      sharpe_range: [null, null],
      median_max_drawdown: null,
      canonical_percentile_by_sharpe: null,
      warnings: [],
    },
    transaction_cost_sensitivity: {
      status: "completed",
      results: [],
      canonical_cost: null,
      canonical_cost_result: null,
      warnings: [],
    },
    data_quality: {
      status: "incomplete",
      fatal_issues: [],
      warnings: [],
      informational: {},
      checks: [],
    },
    warnings: [],
    generated_at: "2026-07-14T00:00:00Z",
    validation_run_id: "val-test",
    ...overrides,
  };
}

function baseEvaluation(
  overrides: Partial<ResearchEvaluationResult> = {}
): ResearchEvaluationResult {
  return {
    research_id: "ma-crossover-spy",
    evaluation_status: "incomplete",
    evidence_summary: [
      {
        stage: "parameter_sensitivity",
        label: "Parameter sensitivity",
        status: "completed",
        summary: "ok",
      },
      {
        stage: "benchmark_comparison",
        label: "Benchmark comparison",
        status: "completed",
        summary: "ok",
      },
      {
        stage: "transaction_cost_sensitivity",
        label: "Transaction-cost sensitivity",
        status: "completed",
        summary: "ok",
      },
      {
        stage: "data_quality",
        label: "Data quality",
        status: "incomplete",
        summary: "pending",
      },
    ],
    evidence_coverage: {
      implemented_stage_count: 4,
      completed_stage_count: 3,
      coverage_percentage: 75,
    },
    completed_stages: [
      "Parameter sensitivity",
      "Benchmark comparison",
      "Transaction-cost sensitivity",
    ],
    incomplete_stages: ["Data quality"],
    unavailable_stages: [
      "Stress testing",
      "Regime analysis",
      "Walk-forward validation",
      "Monte Carlo simulation",
    ],
    blockers: [],
    limitations: ["Paper trading is unavailable."],
    outstanding_evidence: ["Paper trading"],
    provenance: {
      research_id: "ma-crossover-spy",
      validation_run_id: "val-test",
      validation_generated_at: null,
      market_data_provenance: null,
    },
    generated_at: "2026-07-14T00:00:00Z",
    ...overrides,
  };
}

describe("buildPaperTradingCenterModel", () => {
  const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;

  it("shows empty session and never fabricates Active without a session", () => {
    const model = buildPaperTradingCenterModel({
      research,
      validation: null,
      evaluation: null,
    });
    expect(model.hasSession).toBe(false);
    expect(model.eligibility).toBe("not_eligible");
    expect(model.nextActionKind).toBe("continue_validation");
    expect(model.reviewCriteria.every((c) => c.status === "awaiting_observation")).toBe(
      true
    );
  });

  it("marks Needs Review when validation/robustness work is incomplete", () => {
    const model = buildPaperTradingCenterModel({
      research,
      validation: baseValidation(),
      evaluation: baseEvaluation(),
    });
    expect(model.eligibility).toBe("needs_review");
    expect(model.nextActionKind).toBe("continue_robustness");
    expect(
      model.observationItems.find((i) => i.id === "benchmark_behaviour")?.status
    ).toBe("pending");
    expect(
      model.observationItems.find((i) => i.id === "drawdown_behaviour")?.status
    ).toBe("planned");
    expect(
      model.observationItems.every((i) => i.status !== "configured")
    ).toBe(true);
  });

  it("marks Eligible when implemented checks are complete and no session exists", () => {
    const model = buildPaperTradingCenterModel({
      research,
      validation: baseValidation({
        validation_status: "completed",
        data_quality: {
          status: "completed",
          fatal_issues: [],
          warnings: [],
          informational: {},
          checks: [],
        },
        stages: [
          {
            stage: "parameter_sensitivity",
            label: "Parameter sensitivity",
            status: "completed",
            summary: "ok",
            evidence: {},
            rules: [],
            warnings: [],
            blockers: [],
            generated_at: null,
            provenance: null,
          },
          {
            stage: "benchmark_comparison",
            label: "Benchmark comparison",
            status: "completed",
            summary: "ok",
            evidence: {},
            rules: [],
            warnings: [],
            blockers: [],
            generated_at: null,
            provenance: null,
          },
          {
            stage: "transaction_cost_sensitivity",
            label: "Transaction-cost sensitivity",
            status: "completed",
            summary: "ok",
            evidence: {},
            rules: [],
            warnings: [],
            blockers: [],
            generated_at: null,
            provenance: null,
          },
          {
            stage: "data_quality",
            label: "Data quality",
            status: "completed",
            summary: "ok",
            evidence: {},
            rules: [],
            warnings: [],
            blockers: [],
            generated_at: null,
            provenance: null,
          },
        ],
      }),
      evaluation: baseEvaluation({
        evaluation_status: "completed",
        incomplete_stages: [],
        completed_stages: [
          "Parameter sensitivity",
          "Benchmark comparison",
          "Transaction-cost sensitivity",
          "Data quality",
        ],
        evidence_summary: [
          {
            stage: "parameter_sensitivity",
            label: "Parameter sensitivity",
            status: "completed",
            summary: "ok",
          },
          {
            stage: "benchmark_comparison",
            label: "Benchmark comparison",
            status: "completed",
            summary: "ok",
          },
          {
            stage: "transaction_cost_sensitivity",
            label: "Transaction-cost sensitivity",
            status: "completed",
            summary: "ok",
          },
          {
            stage: "data_quality",
            label: "Data quality",
            status: "completed",
            summary: "ok",
          },
        ],
      }),
    });
    expect(model.eligibility).toBe("eligible");
    expect(model.nextActionKind).toBe("begin_observation");
    expect(model.hasSession).toBe(false);
  });

  it("fills deployment fields from research configuration only", () => {
    const model = buildPaperTradingCenterModel({
      research,
      validation: null,
      evaluation: null,
    });
    expect(model.deployment.researchName).toBe("Trend Following Study");
    expect(model.deployment.benchmark).toBe("SPY Buy & Hold");
    expect(model.deployment.strategy).toBe("Moving Average Crossover");
    expect(model.deployment.currentStatus).toBe(research.status);
  });
});
