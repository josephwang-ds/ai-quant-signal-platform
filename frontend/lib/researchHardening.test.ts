import { describe, expect, it, beforeEach } from "vitest";
import {
  assertCanonicalCatalog,
  getMockResearchDetails,
  getMockResearchProjects,
} from "@/lib/mockResearchCatalog";
import {
  CANONICAL_FACTOR_RUN_CONFIGURATION,
  CANONICAL_LOW_VOL_RUN_CONFIGURATION,
  CANONICAL_FACTOR_DEMO_IDS,
} from "@/lib/canonicalCrossSectionalFactor";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { buildResearchReadinessModel } from "@/lib/researchReadiness";
import {
  RESEARCH_DECISION_STORAGE_KEY,
  saveResearchDecisionRecord,
  getResearchDecisionRecord,
  RESEARCH_DECISION_OUTCOMES,
} from "@/lib/researchDecisionRecord";

describe("canonical demo configurations", () => {
  it("exposes three reproducible demos without hard-coded metrics", () => {
    assertCanonicalCatalog();
    const projects = getMockResearchProjects();
    expect(projects).toHaveLength(3);
    expect(projects.map((item) => item.id).sort()).toEqual(
      [CANONICAL_RESEARCH_ID, ...CANONICAL_FACTOR_DEMO_IDS].sort()
    );
    for (const detail of getMockResearchDetails()) {
      expect(detail.confidenceScore).toBeNull();
      expect(detail.integrity.metricsStatus).toBe("Not Calculated");
      expect(detail.evidenceSummary.toLowerCase()).toContain("no calculated");
    }
  });

  it("keeps Value out of runnable demo factor configs", () => {
    expect(CANONICAL_FACTOR_RUN_CONFIGURATION.factorId).toBe("momentum");
    expect(CANONICAL_LOW_VOL_RUN_CONFIGURATION.factorId).toBe("low_volatility");
    expect(CANONICAL_FACTOR_RUN_CONFIGURATION.factorId).not.toBe("value");
  });
});

describe("research decision outcomes", () => {
  beforeEach(() => {
    window.localStorage.removeItem(RESEARCH_DECISION_STORAGE_KEY);
  });

  it("supports promote / hold / reject / archive with evidence metadata", () => {
    expect(RESEARCH_DECISION_OUTCOMES).toEqual([
      "promote",
      "hold",
      "reject",
      "archive",
    ]);
    const record = saveResearchDecisionRecord({
      researchId: "demo-1",
      outcome: "hold",
      rationale:
        "Historical cross-sectional evidence is directionally positive, but stability and cost sensitivity require further observation.",
      evidenceTimestamp: "2026-07-24T12:00:00.000Z",
      evidenceSummary: "Referenced calculated RankIC summary from validation panel.",
      reviewerNote: "Human review note",
      now: "2026-07-24T12:05:00.000Z",
    });
    expect(getResearchDecisionRecord("demo-1")).toEqual(record);
    expect(record.outcome).toBe("hold");
  });

  it("migrates legacy advance to promote without inventing metrics", () => {
    window.localStorage.setItem(
      RESEARCH_DECISION_STORAGE_KEY,
      JSON.stringify({
        legacy: {
          researchId: "legacy",
          outcome: "advance",
          rationale: "Ready after validation.",
          decidedAt: "2026-07-01T00:00:00.000Z",
        },
      })
    );
    expect(getResearchDecisionRecord("legacy")?.outcome).toBe("promote");
  });
});

describe("research readiness", () => {
  it("marks incomplete validation without requiring positive performance", () => {
    const research = getMockResearchDetails()[0];
    const model = buildResearchReadinessModel({
      research,
      validation: null,
      evaluation: null,
      factorValidation: null,
      decisionRecorded: false,
    });
    const byId = Object.fromEntries(
      model.items.map((item) => [item.id, item.complete])
    );
    expect(byId.research_question).toBe(true);
    expect(byId.hypothesis).toBe(true);
    expect(byId.protocol).toBe(true);
    expect(byId.validation).toBe(false);
    expect(byId.decision).toBe(false);
    expect(byId.limitations).toBe(true);
  });

  it("marks validation complete from factor evidence without inventing scores", () => {
    const research = getMockResearchDetails().find((item) =>
      item.id.includes("factor")
    )!;
    const model = buildResearchReadinessModel({
      research,
      factorValidation: {
        research_id: research.id,
        template: "cross_sectional_factor",
        universe_id: "us_sector_etfs",
        factor_id: "momentum",
        rebalance_frequency: "monthly",
        holding_period_months: 1,
        ic: {
          series: [],
          rolling_series: [],
          summary: {
            mean_rank_ic: 0.1,
            median_rank_ic: 0.1,
            positive_ic_ratio: 0.55,
            icir: 0.4,
            n_periods: 12,
          },
        },
        quantiles: {
          period_returns: {},
          cumulative_returns: {},
          turnover: { series: [], mean: null },
          transaction_cost: { series: [], total: null, cost_rate: 0.001 },
          n_rebalances: 12,
        },
        long_short: {
          period_returns: [],
          cumulative_returns: [],
          cumulative_final: null,
        },
        capm: {
          benchmark_symbol: "SPY",
          regression: {
            alpha: null,
            alpha_annualized: null,
            alpha_annualized_ci_low: null,
            alpha_annualized_ci_high: null,
            beta: null,
            t_stat_alpha: null,
            r_squared: null,
            n_observations: 0,
          },
          decomposition: {
            dates: [],
            cumulative_beta_contribution: [],
            cumulative_residual_alpha: [],
            cumulative_cost_drag: [],
            methodology: "Unavailable — benchmark evidence was not computed.",
          },
        },
        portfolio_risk: {
          sharpe_ratio_net: null,
          max_drawdown_net: null,
        },
        warnings: [],
        provenance: {
          universe_symbols: [],
          symbols_used: [],
          symbol_series: [],
          start_date: "2019-01-01",
          end_date: null,
          n_factor_periods: 12,
          benchmark_symbol: "SPY",
        },
        generated_at: "2026-07-24T12:00:00.000Z",
        validation_run_id: "run-1",
        validation_status: "completed",
      },
      decisionRecorded: true,
    });
    expect(model.items.find((item) => item.id === "validation")?.complete).toBe(
      true
    );
    expect(model.items.find((item) => item.id === "decision")?.complete).toBe(
      true
    );
  });
});
