/**
 * Overlay real execution evidence onto Research Workspace projections.
 * Never invents metrics when execution is missing or failed.
 */

import type { ResearchExperiment } from "@/types/experiment";
import type { PlannedValidationStage } from "@/types/canonicalResearch";
import type { ResearchDetail, ResearchListItem } from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import { getCanonicalResearchPackage } from "@/lib/canonicalMaCrossover";

const BASELINE_EXPERIMENT_ID = "exp-ma-baseline";

export const HISTORICAL_DISCLAIMER =
  "Historical research result — not investment advice and not a forecast of future performance.";

/** Overlay list-card evidence once Research Execution Engine succeeds. */
export function applyExecutionToListItem(
  item: ResearchListItem,
  execution: ResearchExecutionResult
): ResearchListItem {
  const p = execution.provenance;
  const range = `${p.actual_start} → ${p.actual_end}`;
  return {
    ...item,
    status: "Running",
    lastValidation: "Historical backtest + benchmark comparison completed (engine)",
    currentRecommendation:
      "Review calculated historical evidence. Evaluation remains unavailable.",
    evidenceSummary:
      "Historical backtest and benchmark comparison are populated from the Research Execution Engine. OOS, sensitivity, cost grid, stress, and evaluation remain pending.",
    updatedAt: execution.generated_at,
    integrity: {
      ...item.integrity,
      dataStatus: `Real Historical Data · ${p.source} · ${p.symbol} · ${range}`,
      metricsStatus: "Calculated (Research Execution Engine)",
      validationStatus: "Partial — Historical & Benchmark only",
      evaluationStatus: "Not Available",
      publicityLabel: "Real Historical Data — calculated evidence attached",
      explanatoryText: HISTORICAL_DISCLAIMER,
      evaluationPendingMessage:
        "Evaluation unavailable until real OOS, sensitivity, cost, stress, and data-quality evidence exist.",
    },
  };
}

export function applyExecutionToResearch(
  research: ResearchDetail,
  execution: ResearchExecutionResult
): ResearchDetail {
  const p = execution.provenance;
  const range = `${p.actual_start} → ${p.actual_end}`;
  return {
    ...research,
    status: "Running",
    currentStage: "Running",
    lastValidation: "Historical backtest + benchmark comparison completed (engine)",
    currentRecommendation:
      "Review calculated historical evidence. Evaluation remains unavailable until OOS/sensitivity/cost reviews exist.",
    integrity: {
      ...research.integrity,
      dataStatus: `Real Historical Data · ${p.source} · ${p.symbol} · ${range}`,
      metricsStatus: "Calculated (Research Execution Engine)",
      validationStatus: "Partial — Historical & Benchmark only",
      evaluationStatus: "Not Available",
      publicityLabel: "Real Historical Data — calculated evidence attached",
      explanatoryText: HISTORICAL_DISCLAIMER,
      evaluationPendingMessage:
        "Evaluation unavailable until real OOS, sensitivity, cost, stress, and data-quality evidence exist.",
    },
    researchSummary: `${HISTORICAL_DISCLAIMER} Provenance: ${p.source}, retrieved ${p.retrieved_at}${
      p.cache_hit ? (p.cache_stale ? " (stale cache)" : " (cached)") : " (live)"
    }.`,
    evidenceSummary:
      "Historical backtest and benchmark comparison are populated from the Research Execution Engine. OOS, sensitivity, cost grid, stress, and evaluation remain pending.",
    validationSummary:
      "Supported evidence only: Historical Backtest and Benchmark Comparison. Remaining validation stages are Not Started / Awaiting Engine.",
    evidenceItems: research.evidenceItems.map((item) => {
      if (item.id === "val-historical") {
        return {
          ...item,
          status: "completed",
          result: `Completed · Sharpe ${formatNullable(execution.metrics.sharpe_ratio)} · CAGR ${formatPct(execution.metrics.cagr)} · Max DD ${formatPct(execution.metrics.maximum_drawdown)}`,
        };
      }
      if (item.id === "val-benchmark") {
        return {
          ...item,
          status: "completed",
          result: `Completed · Benchmark total return ${formatPct(execution.benchmark_metrics.total_return)} · Sharpe ${formatNullable(execution.benchmark_metrics.sharpe_ratio)}`,
        };
      }
      return item;
    }),
  };
}

function formatNullable(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(2);
}

function formatPct(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function applyExecutionToExperiments(
  experiments: ResearchExperiment[],
  execution: ResearchExecutionResult
): ResearchExperiment[] {
  const source = experiments.some((item) => item.id === BASELINE_EXPERIMENT_ID)
    ? experiments
    : [buildExecutedBaseline(execution), ...experiments];
  return source.map((experiment) => {
    if (experiment.id !== BASELINE_EXPERIMENT_ID) {
      return experiment;
    }
    const m = execution.metrics;
    return {
      ...experiment,
      name: `${movingAverageLabel(execution)} Baseline Backtest — Executed`,
      status: "Completed",
      startDate: m.start_date ?? experiment.startDate,
      endDate: m.end_date ?? experiment.endDate,
      resultSummary: `Calculated by Research Execution Engine. ${HISTORICAL_DISCLAIMER}`,
      metrics: {
        sharpe: m.sharpe_ratio,
        cagr: m.cagr,
        maxDrawdown: m.maximum_drawdown,
        volatility: m.annualized_volatility,
        tradeCount: m.trade_count,
        winRate: m.win_rate,
        totalTransactionCost:
          m.total_transaction_costs === null
            ? null
            : m.total_transaction_costs * 10_000,
      },
      validationReadiness: "partial",
      notes: `${experiment.notes} Total return ${formatPct(m.total_return)}; trades ${m.trade_count ?? "n/a"}.`,
    };
  });
}

function movingAverageLabel(execution: ResearchExecutionResult): string {
  const shortWindow = execution.strategy.short_window;
  const longWindow = execution.strategy.long_window;
  return typeof shortWindow === "number" && typeof longWindow === "number"
    ? `MA${shortWindow}/${longWindow}`
    : "MA Crossover";
}

function buildExecutedBaseline(
  execution: ResearchExecutionResult
): ResearchExperiment {
  const symbol = execution.provenance.symbol;
  const shortWindow = execution.strategy.short_window;
  const longWindow = execution.strategy.long_window;
  const transactionCost = execution.strategy.transaction_cost;
  return {
    id: BASELINE_EXPERIMENT_ID,
    researchId: execution.research_id,
    name: `${movingAverageLabel(execution)} Baseline Backtest`,
    hypothesis: `Test whether the configured moving-average crossover produces robust historical evidence for ${symbol} after transaction costs.`,
    status: "Designed",
    experimentType: "Backtest",
    datasetOrSymbol: symbol,
    startDate: execution.metrics.start_date ?? execution.provenance.actual_start,
    endDate: execution.metrics.end_date ?? execution.provenance.actual_end,
    benchmark: `${symbol} Buy & Hold`,
    parameters: [
      { key: "short_window", value: String(shortWindow ?? "n/a") },
      { key: "long_window", value: String(longWindow ?? "n/a") },
      { key: "transaction_cost", value: String(transactionCost ?? "n/a") },
    ],
    successCriteria: "Positive risk-adjusted performance with documented drawdown and cost sensitivity.",
    falsificationCondition: "Evidence is not robust after costs, across time, or under validation checks.",
    notes: "Generated from the executable research definition and populated only with backend-calculated evidence.",
    owner: "Research Workspace",
    createdAt: execution.generated_at,
    updatedAt: execution.generated_at,
    resultSummary: "Awaiting execution evidence.",
    metrics: {
      sharpe: null,
      cagr: null,
      maxDrawdown: null,
      volatility: null,
      tradeCount: null,
      winRate: null,
      totalTransactionCost: null,
    },
    linkedNotebookEntryIds: [],
    relatedEvidenceIds: [],
    validationReadiness: "not_ready",
  };
}

export function validationStagesFromExecution(
  execution: ResearchExecutionResult | null
): PlannedValidationStage[] {
  const base = getCanonicalResearchPackage().plannedValidationStages.map((stage) => ({
    ...stage,
  }));
  if (!execution) {
    return base;
  }
  return base.map((stage) => {
    if (stage.id === "val-historical") {
      return {
        ...stage,
        description: `Completed via Research Execution Engine · actual ${execution.provenance.actual_start} → ${execution.provenance.actual_end}.`,
      };
    }
    if (stage.id === "val-benchmark") {
      return {
        ...stage,
        description:
          "Completed via Research Execution Engine (SPY buy-and-hold comparison).",
      };
    }
    return stage;
  });
}

/** Map execution-backed stages to display status strings for the validation panel. */
export function validationDisplayStatus(
  stageId: string,
  execution: ResearchExecutionResult | null
): "completed" | "not_started" | "awaiting_data" {
  if (!execution) {
    const original = getCanonicalResearchPackage().plannedValidationStages.find(
      (s) => s.id === stageId
    );
    return original?.status === "awaiting_data" ? "awaiting_data" : "not_started";
  }
  if (stageId === "val-historical" || stageId === "val-benchmark") {
    return "completed";
  }
  if (stageId === "val-quality") {
    return "awaiting_data";
  }
  return "not_started";
}
