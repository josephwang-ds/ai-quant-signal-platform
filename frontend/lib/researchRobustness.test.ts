import { describe, expect, it } from "vitest";
import {
  buildRobustnessCenterModel,
  ROBUSTNESS_MATRIX_ITEMS,
  ROBUSTNESS_SCOPE_BOUNDARIES,
} from "@/lib/researchRobustness";
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
    stages: [],
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
      status: "incomplete",
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
      status: "incomplete",
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
    evidence_summary: [],
    evidence_coverage: {
      implemented_stage_count: 6,
      completed_stage_count: 0,
      coverage_percentage: 0,
    },
    completed_stages: [],
    incomplete_stages: [],
    unavailable_stages: [
      "Stress testing",
      "Regime analysis",
      "Walk-forward validation",
      "Monte Carlo simulation",
    ],
    blockers: [],
    limitations: [],
    outstanding_evidence: [],
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

describe("buildRobustnessCenterModel", () => {
  it("shows only implemented checks and keeps unsupported methods as scope boundaries", () => {
    const model = buildRobustnessCenterModel({
      validation: null,
      evaluation: null,
    });

    expect(model.items).toHaveLength(ROBUSTNESS_MATRIX_ITEMS.length);
    expect(model.items.map((item) => item.id)).toEqual([
      "parameter_sensitivity",
      "benchmark_comparison",
      "transaction_cost",
      "data_quality",
    ]);
    expect(model.scopeBoundaryIds).toEqual([...ROBUSTNESS_SCOPE_BOUNDARIES]);
    expect(model.items.find((i) => i.id === "parameter_sensitivity")?.status).toBe(
      "pending"
    );
    expect(model.overallStatus).toBe("not_started");
    expect(model.nextItemId).toBe("parameter_sensitivity");
  });

  it("marks completed stages from evaluation evidence only", () => {
    const model = buildRobustnessCenterModel({
      validation: null,
      evaluation: baseEvaluation({
        completed_stages: ["Parameter sensitivity", "Data quality"],
        incomplete_stages: ["Benchmark comparison"],
        evidence_summary: [
          {
            stage: "parameter_sensitivity",
            label: "Parameter sensitivity",
            status: "completed",
            summary: "Deterministic parameter grid completed.",
          },
        ],
      }),
    });

    expect(model.items.find((i) => i.id === "parameter_sensitivity")?.status).toBe(
      "completed"
    );
    expect(model.items.find((i) => i.id === "data_quality")?.status).toBe("completed");
    expect(model.items.find((i) => i.id === "benchmark_comparison")?.status).toBe(
      "pending"
    );
    expect(model.scopeBoundaryIds).toContain("monte_carlo");
  });

  it("surfaces blockers only when evaluation is blocked", () => {
    const model = buildRobustnessCenterModel({
      validation: null,
      evaluation: baseEvaluation({
        evaluation_status: "blocked",
        blockers: ["Provider unavailable"],
        incomplete_stages: ["Parameter sensitivity"],
      }),
    });

    expect(model.items.find((i) => i.id === "parameter_sensitivity")?.status).toBe(
      "blocked"
    );
    expect(model.overallStatus).toBe("blocked");
    expect(model.nextActionKind).toBe("resolve_blocker");
  });

  it("keeps unsupported analysis out of executable checklist items", () => {
    const model = buildRobustnessCenterModel({
      validation: null,
      evaluation: baseEvaluation(),
    });

    expect(model.items.some((item) => item.id === ("market_regime" as never))).toBe(
      false
    );
    expect(model.scopeBoundaryIds).toEqual([
      "market_regime",
      "walk_forward",
      "monte_carlo",
      "liquidity_capacity",
    ]);
  });

  it("uses validation nested status when evaluation is absent", () => {
    const model = buildRobustnessCenterModel({
      validation: baseValidation({
        parameter_sensitivity: {
          status: "completed",
          results: [],
          valid_combination_count: 1,
          profitable_combination_count: null,
          positive_sharpe_count: null,
          median_sharpe: null,
          sharpe_range: [null, null],
          median_max_drawdown: null,
          canonical_percentile_by_sharpe: null,
          warnings: [],
        },
      }),
      evaluation: null,
    });

    expect(model.items.find((i) => i.id === "parameter_sensitivity")?.status).toBe(
      "completed"
    );
    expect(model.hasValidationEvidence).toBe(true);
  });

  it("never invents a maturity percentage or score field", () => {
    const model = buildRobustnessCenterModel({
      validation: null,
      evaluation: baseEvaluation(),
    });
    expect(model).not.toHaveProperty("coverage_percentage");
    expect(model).not.toHaveProperty("score");
    expect(model).not.toHaveProperty("maturity");
  });
});
