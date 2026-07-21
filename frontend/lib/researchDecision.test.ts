import { describe, expect, it } from "vitest";
import { buildDecisionCenterModel } from "@/lib/researchDecision";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";
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
        stage: "data_quality",
        label: "Data quality",
        status: "incomplete",
        summary: "pending",
      },
    ],
    evidence_coverage: {
      implemented_stage_count: 4,
      completed_stage_count: 1,
      coverage_percentage: 25,
    },
    completed_stages: ["Parameter sensitivity"],
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

describe("buildDecisionCenterModel", () => {
  const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;

  it("is Not Ready without validation and never invents notes or approval", () => {
    const model = buildDecisionCenterModel({
      research,
      validation: null,
      evaluation: null,
    });
    expect(model.decisionStatus).toBe("not_ready");
    expect(model.decisionNotes).toBeNull();
    expect(model.evidence.every((row) => row.status === "pending")).toBe(true);
    expect(model.nextActionKind).toBe("complete_validation");
  });

  it("is Under Review when validation exists but work remains", () => {
    const model = buildDecisionCenterModel({
      research,
      validation: baseValidation(),
      evaluation: baseEvaluation(),
    });
    expect(model.decisionStatus).toBe("under_review");
    expect(model.evidence.find((e) => e.id === "validation")?.status).toBe(
      "pending"
    );
    expect(model.remainingRiskIds).toContain("extreme_volatility");
    expect(model.remainingRiskIds).toContain("forward_validation");
    expect(model.remainingRiskIds).toContain("implemented_robustness_pending");
    expect(model.checklist.find((c) => c.id === "limitations_documented")?.status).toBe(
      "completed"
    );
    expect(model.nextActionKind).toBe("complete_validation");
  });

  it("maps Archived lifecycle status without inventing Rejected", () => {
    const model = buildDecisionCenterModel({
      research: { ...research, status: "Archived" },
      validation: baseValidation({ validation_status: "completed" }),
      evaluation: baseEvaluation({ evaluation_status: "completed" }),
    });
    expect(model.decisionStatus).toBe("archived");
    expect(model.nextActionKind).toBe("none");
  });

  it("maps Paper Trading lifecycle to Approved for Paper Trading", () => {
    const model = buildDecisionCenterModel({
      research: { ...research, status: "Paper Trading" },
      validation: baseValidation({ validation_status: "completed" }),
      evaluation: baseEvaluation({ evaluation_status: "completed" }),
      hasSession: true,
    });
    expect(model.decisionStatus).toBe("approved_for_paper");
    expect(model.evidence.find((e) => e.id === "paper_trading")?.status).toBe(
      "completed"
    );
  });

  it("accepts real decision notes only when provided", () => {
    const model = buildDecisionCenterModel({
      research,
      validation: null,
      evaluation: null,
      decisionNotes: "  Human review note.  ",
    });
    expect(model.decisionNotes).toBe("Human review note.");
  });
});
