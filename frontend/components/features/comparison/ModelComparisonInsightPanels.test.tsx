import { describe, expect, it } from "vitest";
import { buildComparisonConclusion } from "@/components/features/comparison/ModelComparisonInsightPanels";
import type { ModelComparisonResponse } from "@/lib/api";

const sample: ModelComparisonResponse = {
  test_start: "2022-01-01",
  test_end: "2023-01-01",
  results: [
    {
      label: "Logistic L2",
      kind: "ml",
      strategy: "logistic_l2",
      metrics: {
        total_return: 0.1,
        sharpe_ratio: 0.8,
        max_drawdown: -0.12,
        strategy_max_drawdown: -0.12,
        number_of_trades: 5,
        transaction_cost_total: 0.002,
      },
    },
    {
      label: "Random Forest",
      kind: "ml",
      strategy: "random_forest",
      metrics: {
        total_return: 0.2,
        sharpe_ratio: 0.5,
        max_drawdown: -0.2,
        strategy_max_drawdown: -0.2,
        number_of_trades: 12,
        transaction_cost_total: 0.01,
      },
    },
  ],
  summary: {
    best_total_return: "Random Forest",
    best_sharpe: "Logistic L2",
    lowest_drawdown: "Logistic L2",
    fewest_trades: "Logistic L2",
  },
  interpretation: [],
};

describe("buildComparisonConclusion", () => {
  it("mentions best sharpe and walk-forward caveat in English", () => {
    const text = buildComparisonConclusion(sample, "en");
    expect(text).toContain("Best OOS Sharpe");
    expect(text).toContain("Logistic L2");
    expect(text).toContain("walk-forward");
  });

  it("mentions sample-out best sharpe in Chinese", () => {
    const text = buildComparisonConclusion(sample, "zh");
    expect(text).toContain("样本外最佳 Sharpe");
    expect(text).toContain("walk-forward");
  });
});
